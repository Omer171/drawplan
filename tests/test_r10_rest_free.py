"""R10: free practice and planned rest days (and the R2, R3, R4, R7 rules they change)."""

import datetime as dt

import pytest

from drawplan import planner, storage
from tests.test_r7_weekly import run_cli

TODAY = dt.date(2026, 11, 20)            # Friday; the week is Mon 11-16 .. Sun 11-22
LAST_MONDAY = dt.date(2026, 11, 9)       # the week Mon 11-09 .. Sun 11-15
SKILLS = planner.CATALOG["manga"]        # paneling, anatomy, penning, inking, expressions


def day(n):
    """Day n (0 = Monday) of last week."""
    return LAST_MONDAY + dt.timedelta(days=n)


def plus(n, start=TODAY):
    return start + dt.timedelta(days=n)


@pytest.fixture
def manga(state):
    planner.add_goal(state, "manga", LAST_MONDAY)
    return state


def summary(state):
    return planner.week_summary(state, LAST_MONDAY)


def counts(s):
    return s["completed"], s["free_practice"], s["rest"], s["skipped"]


# ---------- free practice ----------

def test_r10_log_without_task_is_free_practice_not_skipped(manga):
    planner.record_log(manga, day(0), 40, "manga", "inking", 30, 0)   # no task asked
    s = summary(manga)
    assert counts(s) == (0, 1, 0, 6)
    assert planner.day_status(manga, day(0)) == "free practice"


def test_r10_task_asked_after_practice_logged_is_marked_free(manga):
    planner.record_log(manga, day(0), 40, "manga", "inking", 30, 0)
    task = planner.daily_task(manga, day(0))
    assert task is not None and task["free_practice"] is True
    assert planner.day_status(manga, day(0)) == "free practice"


def test_r10_task_asked_before_any_log_is_not_free(manga):
    task = planner.daily_task(manga, day(0))
    assert "free_practice" not in task
    planner.record_log(manga, day(0), 40, "manga", "inking", 5, 0)    # too short
    assert planner.day_status(manga, day(0)) == "skipped"


def test_r10_zero_minute_log_before_task_does_not_make_it_free(manga):
    planner.record_log(manga, day(0), 0, None, None, 0, 0)
    task = planner.daily_task(manga, day(0))
    assert "free_practice" not in task


def test_r10_free_task_is_never_completed_or_scaled(manga):
    planner.record_log(manga, day(0), 40, "manga", "inking", 30, 0)
    task = planner.daily_task(manga, day(0))
    before = manga["task_minutes"]
    planner.record_log(manga, day(0), 120, "manga", "inking", 120, 0)  # does the task
    assert manga["task_minutes"] == before
    assert task["completed"] is False and task["adjusted"] is False
    assert counts(summary(manga)) == (0, 1, 0, 6)


def test_r10_free_task_stays_uncompleted_after_editing_logs(manga):
    planner.record_log(manga, day(0), 40, "manga", "inking", 30, 0)
    task = planner.daily_task(manga, day(0))
    planner.edit_log(manga, 0, 120, "manga", "inking", 120, 0)
    assert task["completed"] is False


def test_r10_free_task_earns_no_task_xp(manga):
    planner.record_log(manga, day(0), 60, "manga", "inking", 60, 0)
    xp = planner.player_xp(manga)
    planner.daily_task(manga, day(0))
    planner.record_log(manga, day(0), 60, None, None, 0, 0)
    assert planner.player_xp(manga) == xp


def test_r10_deleting_the_practice_makes_the_day_skipped_again(manga):
    planner.record_log(manga, day(0), 40, "manga", "inking", 30, 0)
    planner.daily_task(manga, day(0))
    planner.delete_log(manga, 0)
    assert planner.day_status(manga, day(0)) == "skipped"


def test_r10_zero_minute_log_alone_is_skipped(manga):
    planner.record_log(manga, day(0), 0, None, None, 0, 0)
    assert planner.day_status(manga, day(0)) == "skipped"


def test_r10_completed_task_still_counts_as_completed(manga):
    planner.daily_task(manga, day(0))
    planner.record_log(manga, day(0), 30, "manga", "inking", 30, 0)
    assert planner.day_status(manga, day(0)) == "completed"


# ---------- marking and cancelling rest days ----------

def test_r10_mark_rest_day_from_tomorrow_on(state):
    planner.mark_rest_day(state, plus(1), TODAY)
    assert state["rest_days"] == [plus(1).isoformat()]
    assert planner.is_rest_day(state, plus(1))


@pytest.mark.parametrize("offset", [0, -1, -10])
def test_r10_today_and_past_days_cannot_be_marked(state, offset):
    with pytest.raises(ValueError):
        planner.mark_rest_day(state, plus(offset), TODAY)
    assert state["rest_days"] == []


def test_r10_only_one_rest_day_per_calendar_week(state):
    planner.mark_rest_day(state, plus(1), TODAY)                       # Sat 11-21
    with pytest.raises(ValueError):
        planner.mark_rest_day(state, plus(2), TODAY)                   # Sun 11-22
    planner.mark_rest_day(state, plus(3), TODAY)                       # Mon 11-23
    with pytest.raises(ValueError):
        planner.mark_rest_day(state, plus(9), TODAY)                   # Sun 11-29
    assert state["rest_days"] == [plus(1).isoformat(), plus(3).isoformat()]


def test_r10_marking_the_same_day_again_is_rejected(state):
    planner.mark_rest_day(state, plus(4), TODAY)
    with pytest.raises(ValueError):
        planner.mark_rest_day(state, plus(4), TODAY)
    assert state["rest_days"] == [plus(4).isoformat()]


def test_r10_rest_days_are_kept_sorted(state):
    planner.mark_rest_day(state, plus(10), TODAY)
    planner.mark_rest_day(state, plus(3), TODAY)
    assert state["rest_days"] == [plus(3).isoformat(), plus(10).isoformat()]


def test_r10_cancel_a_future_rest_day(state):
    planner.mark_rest_day(state, plus(3), TODAY)
    planner.cancel_rest_day(state, plus(3), TODAY)
    assert state["rest_days"] == []
    planner.mark_rest_day(state, plus(4), TODAY)                       # week is free again


def test_r10_cannot_cancel_today_past_or_unplanned_rest_days(state):
    planner.mark_rest_day(state, plus(1), TODAY)
    with pytest.raises(ValueError):
        planner.cancel_rest_day(state, plus(1), plus(1))               # it is that day now
    with pytest.raises(ValueError):
        planner.cancel_rest_day(state, plus(1), plus(2))               # it has passed
    with pytest.raises(ValueError):
        planner.cancel_rest_day(state, plus(5), TODAY)                 # never planned
    assert state["rest_days"] == [plus(1).isoformat()]


def test_r10_upcoming_rest_days_lists_only_dates_after_today(state):
    planner.mark_rest_day(state, plus(1), TODAY)
    planner.mark_rest_day(state, plus(5), TODAY)
    assert planner.upcoming_rest_days(state, TODAY) == [plus(1), plus(5)]
    assert planner.upcoming_rest_days(state, plus(1)) == [plus(5)]


def test_r10_rest_days_default_to_empty_for_old_files(data_file):
    data_file.write_text('{"version": 1, "goals": [], "logs": [], "tasks": {}, '
                         '"task_minutes": 30}', encoding="utf-8")
    assert storage.load(data_file)["rest_days"] == []


# ---------- rest days: tasks (R3) ----------

def test_r10_rest_day_gets_no_task_and_saves_nothing(manga):
    planner.mark_rest_day(manga, plus(1), TODAY)
    assert planner.daily_task(manga, plus(1)) is None
    assert plus(1).isoformat() not in manga["tasks"]


def test_r10_rotation_continues_after_a_rest_day(manga):
    first = planner.daily_task(manga, TODAY)
    planner.mark_rest_day(manga, plus(1), TODAY)
    planner.daily_task(manga, plus(1))
    after = planner.daily_task(manga, plus(2))
    assert SKILLS.index(after["skill"]) == (SKILLS.index(first["skill"]) + 1) % len(SKILLS)


# ---------- rest days: weekly summary (R7) ----------

def test_r10_rest_day_counts_as_rest_not_skipped(manga):
    manga["rest_days"] = [day(2).isoformat()]        # planned earlier, now in the past
    planner.daily_task(manga, day(0))
    planner.record_log(manga, day(0), 30, "manga", "inking", 30, 0)
    planner.record_log(manga, day(1), 30, "manga", "inking", 30, 0)
    assert counts(summary(manga)) == (1, 1, 1, 4)


def test_r10_drawing_on_a_rest_day_still_counts_as_rest(manga):
    manga["rest_days"] = [day(3).isoformat()]
    planner.record_log(manga, day(3), 45, "manga", "inking", 45, 0)
    assert planner.day_status(manga, day(3)) == "rest"
    assert summary(manga)["skill_minutes"][("manga", "inking")] == 45


def test_r10_summary_text_shows_all_four_kinds_of_day(manga):
    manga["rest_days"] = [day(2).isoformat()]
    planner.daily_task(manga, day(0))
    planner.record_log(manga, day(0), 30, "manga", "inking", 30, 0)
    planner.record_log(manga, day(1), 30, "manga", "inking", 30, 0)
    text = planner.render_week_summary(summary(manga))
    assert "1 completed, 1 free practice, 1 rest day, 4 skipped" in text


def test_r10_days_before_the_first_goal_are_still_not_counted(state):
    planner.add_goal(state, "manga", day(4))
    state["rest_days"] = [day(5).isoformat()]
    planner.record_log(state, day(2), 30, None, None, 0, 0)          # before the goal
    s = summary(state)
    assert counts(s) == (0, 0, 1, 2)


# ---------- rest days: streak (R2) ----------

def test_r10_rest_day_bridges_the_streak_without_adding(state):
    state["rest_days"] = [plus(-1).isoformat()]
    planner.record_log(state, plus(-2), 30, None, None, 0, 0)
    planner.record_log(state, TODAY, 30, None, None, 0, 0)
    assert planner.streak(state, TODAY) == 2


def test_r10_streak_survives_a_rest_day_yesterday(state):
    state["rest_days"] = [plus(-1).isoformat()]
    planner.record_log(state, plus(-2), 30, None, None, 0, 0)
    planner.record_log(state, plus(-3), 30, None, None, 0, 0)
    assert planner.streak(state, TODAY) == 2              # today not drawn yet


def test_r10_streak_survives_a_rest_day_today(state):
    state["rest_days"] = [TODAY.isoformat()]
    planner.record_log(state, plus(-1), 30, None, None, 0, 0)
    assert planner.streak(state, TODAY) == 1
    assert planner.streak(state, plus(1)) == 1            # tomorrow not drawn yet


def test_r10_drawing_on_a_rest_day_adds_to_the_streak(state):
    state["rest_days"] = [plus(-1).isoformat()]
    for n in (-2, -1, 0):
        planner.record_log(state, plus(n), 30, None, None, 0, 0)
    assert planner.streak(state, TODAY) == 3


def test_r10_rest_days_alone_make_no_streak(state):
    state["rest_days"] = [plus(-1).isoformat()]
    assert planner.streak(state, TODAY) == 0


def test_r10_missed_day_still_breaks_the_streak(state):
    state["rest_days"] = [plus(-2).isoformat()]
    planner.record_log(state, plus(-3), 30, None, None, 0, 0)          # rest, missed, today
    planner.record_log(state, TODAY, 30, None, None, 0, 0)
    assert planner.streak(state, TODAY) == 1


# ---------- CLI ----------

REST_MENU = "10"


def test_r10_cli_marks_a_rest_day_and_saves_it(monkeypatch, capsys, manga, data_file):
    storage.save(manga, data_file)
    out = run_cli(monkeypatch, capsys, data_file, [REST_MENU, "2026-11-24", "q"], TODAY)
    assert "Plan a rest day" in out
    assert storage.load(data_file)["rest_days"] == ["2026-11-24"]


def test_r10_cli_rejects_a_bad_rest_day(monkeypatch, capsys, manga, data_file):
    storage.save(manga, data_file)
    out = run_cli(monkeypatch, capsys, data_file, [REST_MENU, "2026-11-20", "q"], TODAY)
    assert "after today" in out
    out = run_cli(monkeypatch, capsys, data_file, [REST_MENU, "soon", "q"], TODAY)
    assert "Not a date" in out
    assert storage.load(data_file)["rest_days"] == []


def test_r10_cli_cancels_an_upcoming_rest_day(monkeypatch, capsys, manga, data_file):
    planner.mark_rest_day(manga, plus(4), TODAY)
    storage.save(manga, data_file)
    out = run_cli(monkeypatch, capsys, data_file, [REST_MENU, "1", "q"], TODAY)
    assert "2026-11-24" in out
    assert storage.load(data_file)["rest_days"] == []


def test_r10_cli_enter_goes_back_without_saving(monkeypatch, capsys, manga, data_file):
    planner.mark_rest_day(manga, plus(4), TODAY)
    storage.save(manga, data_file)
    run_cli(monkeypatch, capsys, data_file, [REST_MENU, "", "q"], TODAY)
    assert storage.load(data_file)["rest_days"] == [plus(4).isoformat()]


def test_r10_cli_task_on_a_rest_day_says_rest(monkeypatch, capsys, manga, data_file):
    manga["rest_days"] = [TODAY.isoformat()]
    storage.save(manga, data_file)
    out = run_cli(monkeypatch, capsys, data_file, ["3", "q"], TODAY)
    assert "Today is your planned rest day" in out
    assert storage.load(data_file)["tasks"] == {}


def test_r10_cli_rest_day_is_menu_10(monkeypatch, capsys, data_file):
    # R11 menu: quit moved from 11 to 12 in round 6 (see test_r11_cli_quit_is_now_12).
    out = run_cli(monkeypatch, capsys, data_file, ["q"], TODAY)
    assert "10) Plan a rest day" in out
