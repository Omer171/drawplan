import datetime as dt
import json

import pytest

from drawplan import cli, planner, storage

LAST_MONDAY = dt.date(2026, 11, 9)       # the week Mon 11-09 .. Sun 11-15
MONDAY = dt.date(2026, 11, 16)           # the current week in these tests
SKILLS = planner.CATALOG["manga"]        # paneling, anatomy, penning, inking, expressions


def day(n):
    """Day n (0 = Monday) of last week."""
    return LAST_MONDAY + dt.timedelta(days=n)


@pytest.fixture
def manga(state):
    planner.add_goal(state, "manga", LAST_MONDAY)
    return state


def summary(state):
    return planner.week_summary(state, LAST_MONDAY)


# ---------- weeks ----------

def test_r7_weeks_run_monday_to_sunday():
    assert planner.week_start(dt.date(2026, 11, 20)) == MONDAY       # Friday
    assert planner.week_start(dt.date(2026, 11, 16)) == MONDAY       # Monday
    assert planner.week_start(dt.date(2026, 11, 22)) == MONDAY       # Sunday
    assert planner.last_finished_week(dt.date(2026, 11, 22)) == LAST_MONDAY
    assert planner.last_finished_week(dt.date(2026, 11, 23)) == MONDAY


# ---------- what the summary contains ----------

def test_r7_total_hours_count_every_log_in_the_week_only(manga):
    planner.record_log(manga, day(0), 60, "manga", "inking", 30, 0)
    planner.record_log(manga, day(6), 45, None, None, 0, 0)          # off-goal counts
    planner.record_log(manga, MONDAY, 500, "manga", "inking", 500, 0)  # next week
    assert summary(manga)["total_minutes"] == 105


def test_r7_hours_per_skill_cover_every_pair_in_roadmap_order(manga):
    planner.add_goal(manga, "figure", day(0))
    planner.record_log(manga, day(1), 60, "manga", "inking", 40, 0)
    planner.record_log(manga, day(2), 60, "manga", "inking", 20, 0)
    planner.record_log(manga, day(3), 60, "figure", "gesture", 15, 0)
    minutes = summary(manga)["skill_minutes"]
    assert list(minutes) == planner.work_options(manga)
    assert minutes[("manga", "inking")] == 60
    assert minutes[("figure", "gesture")] == 15
    assert minutes[("manga", "paneling")] == 0


def test_r7_completed_vs_skipped_counts_every_day_of_the_week(manga):
    planner.daily_task(manga, day(0))
    planner.record_log(manga, day(0), 30, "manga", "inking", 30, 0)  # completed
    planner.daily_task(manga, day(1))
    planner.record_log(manga, day(1), 30, "manga", "inking", 10, 0)  # short: skipped
    planner.daily_task(manga, day(2))                                # never logged
    s = summary(manga)
    assert (s["completed"], s["skipped"]) == (1, 6)                  # 4 days not opened


def test_r7_days_before_the_first_goal_are_not_counted(state):
    planner.add_goal(state, "manga", day(4))                         # Friday
    planner.daily_task(state, day(4))
    planner.record_log(state, day(4), 30, "manga", "inking", 30, 0)
    s = summary(state)
    assert (s["completed"], s["skipped"]) == (1, 2)                  # Fri, Sat, Sun


# ---------- the neglected skill ----------

def test_r7_neglected_is_the_skill_under_half_the_average(manga):
    for skill in SKILLS:
        planner.record_log(manga, day(0), 60, "manga", skill, 20 if skill == "penning" else 60, 0)
    # average = (4*60 + 20) / 5 = 52; 20 < 26
    assert summary(manga)["neglected"] == ("manga", "penning")


def test_r7_lowest_skill_not_under_half_the_average_is_not_neglected(manga):
    for skill in SKILLS:
        planner.record_log(manga, day(0), 60, "manga", skill, 30 if skill == "penning" else 60, 0)
    # average = 54; 30 is not < 27
    assert summary(manga)["neglected"] is None


def test_r7_week_without_on_goal_time_has_no_neglected_skill(manga):
    planner.record_log(manga, day(0), 90, None, None, 0, 0)
    assert summary(manga)["neglected"] is None


def test_r7_tie_goes_to_roadmap_order(manga):
    for skill in SKILLS[:3]:
        planner.record_log(manga, day(0), 60, "manga", skill, 60, 0)
    # inking and expressions both have 0
    assert summary(manga)["neglected"] == ("manga", "inking")


def test_r7_neglect_is_compared_across_goals(manga):
    planner.add_goal(manga, "figure", LAST_MONDAY)
    for goal, skill in planner.work_options(manga):
        if (goal, skill) != ("figure", "poses"):
            planner.record_log(manga, day(0), 30, goal, skill, 30, 0)
    assert summary(manga)["neglected"] == ("figure", "poses")


def test_r7_goal_added_mid_week_is_shown_but_never_neglected(manga):
    for skill in SKILLS:
        planner.record_log(manga, day(0), 60, "manga", skill, 60, 0)
    planner.add_goal(manga, "figure", day(5))
    s = summary(manga)
    assert ("figure", "gesture") in s["skill_minutes"]
    assert s["neglected"] is None


def test_r7_no_goals_means_nothing_neglected(state):
    s = summary(state)
    assert s["neglected"] is None
    assert (s["completed"], s["skipped"]) == (0, 0)


# ---------- the summary text ----------

def test_r7_summary_text_shows_hours_tasks_and_neglected_skill(manga):
    planner.daily_task(manga, day(0))
    planner.record_log(manga, day(0), 90, "manga", "paneling", 60, 0)
    text = planner.render_week_summary(summary(manga))
    assert "2026-11-09" in text and "2026-11-15" in text
    assert "1.5 total hours" in text
    assert "paneling" in text and "1.0h" in text
    assert "1 completed, 6 skipped" in text
    assert "anatomy" in text.split("neglected")[-1]                  # first 0-minute skill
    assert "Mon, Wed, Fri and Sun" in text


def test_r7_summary_text_without_neglected_skill_says_rotation(manga):
    for skill in SKILLS:
        planner.record_log(manga, day(0), 60, "manga", skill, 60, 0)
    text = planner.render_week_summary(summary(manga))
    assert "rotate" in text.lower()


# ---------- shown once, at the end of every week ----------

def test_r7_summary_due_once_after_the_week_ends(manga):
    first = planner.due_week_summary(manga, MONDAY + dt.timedelta(days=2))
    assert first["start"] == LAST_MONDAY.isoformat()
    assert manga["summaries"] == [LAST_MONDAY.isoformat()]
    assert planner.due_week_summary(manga, MONDAY + dt.timedelta(days=3)) is None


def test_r7_summary_not_due_before_any_goal_existed(state):
    planner.add_goal(state, "manga", MONDAY)
    assert planner.due_week_summary(state, MONDAY) is None
    assert state["summaries"] == []


def test_r7_only_the_last_finished_week_is_shown(manga):
    three_weeks_later = MONDAY + dt.timedelta(days=14)
    s = planner.due_week_summary(manga, three_weeks_later)
    assert s["start"] == (MONDAY + dt.timedelta(days=7)).isoformat()
    assert len(manga["summaries"]) == 1


def test_r7_focus_comes_from_the_summary_even_if_never_shown(manga):
    for skill in SKILLS[:-1]:
        planner.record_log(manga, day(0), 60, "manga", skill, 60, 0)
    assert manga["summaries"] == []
    assert planner.focus_pair(manga, MONDAY) == ("manga", SKILLS[-1])


def test_r7_file_without_summaries_loads(data_file):
    data = storage.new_state()
    del data["summaries"]
    data_file.write_text(json.dumps(data), encoding="utf-8")
    assert storage.load(data_file)["summaries"] == []


def test_r7_shown_summaries_survive_save_and_load(manga, data_file):
    planner.due_week_summary(manga, MONDAY)
    storage.save(manga, data_file)
    assert storage.load(data_file)["summaries"] == [LAST_MONDAY.isoformat()]


# ---------- CLI ----------

def run_cli(monkeypatch, capsys, data_file, answers, today):
    monkeypatch.setenv("DRAWPLAN_DATA", str(data_file))
    monkeypatch.setattr(cli.webbrowser, "open", lambda url: True)
    feed = iter(answers)
    monkeypatch.setattr("builtins.input", lambda prompt="": next(feed))
    assert cli.main(today=today) == 0
    return capsys.readouterr().out


def test_r7_cli_shows_summary_at_start_once_and_saves_it(monkeypatch, capsys, manga,
                                                         data_file):
    storage.save(manga, data_file)
    out = run_cli(monkeypatch, capsys, data_file, ["q"], MONDAY)
    assert "Week of 2026-11-09" in out
    assert storage.load(data_file)["summaries"] == [LAST_MONDAY.isoformat()]
    out = run_cli(monkeypatch, capsys, data_file, ["q"], MONDAY)
    assert "Week of" not in out


def test_r7_cli_menu_item_shows_last_week_summary(monkeypatch, capsys, manga, data_file):
    manga["summaries"] = [LAST_MONDAY.isoformat()]                   # already shown
    storage.save(manga, data_file)
    out = run_cli(monkeypatch, capsys, data_file, ["7", "8"], MONDAY)
    assert "Weekly summary" in out
    assert "Week of 2026-11-09" in out
