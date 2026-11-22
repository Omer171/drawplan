import datetime as dt

import pytest

from drawplan import planner, storage
from tests.conftest import TODAY
from tests.test_r7_weekly import run_cli

START = dt.date(2026, 11, 2)   # a Monday in the same month as TODAY (Fri 2026-11-20)
NOTES_MENU = "11"


def days_before(n):
    return TODAY - dt.timedelta(days=n)


@pytest.fixture
def manga(state):
    planner.add_goal(state, "manga", START)
    return state


def log(state, day, skill="inking", well="", fix="", fixed=None, goal="manga"):
    return planner.record_log(state, day, 60, goal, skill, 45 if goal else 0, 1,
                              went_well=well, fix=fix, fixed=fixed)


# ---------- writing notes ----------

def test_r11_notes_are_saved_on_the_log_with_its_skill(manga):
    entry = log(manga, TODAY, well="clean lines", fix="hands looked stiff")
    assert entry["went_well"] == "clean lines"
    assert entry["fix"] == "hands looked stiff"
    assert (entry["goal"], entry["skill"]) == ("manga", "inking")


def test_r11_notes_are_optional_and_trimmed(manga):
    entry = log(manga, TODAY, well="  good flow  ", fix="   ")
    assert entry["went_well"] == "good flow"
    assert "fix" not in entry                        # blank notes are not stored
    plain = planner.record_log(manga, TODAY, 30, "manga", "inking", 30, 0)
    assert "went_well" not in plain and "fix" not in plain


def test_r11_something_else_log_cannot_have_notes(manga):
    with pytest.raises(ValueError):
        log(manga, TODAY, goal=None, skill=None, fix="too crowded")
    assert manga["logs"] == []
    entry = log(manga, TODAY, goal=None, skill=None)
    assert "fix" not in entry


def test_r11_old_logs_without_notes_read_as_blank(manga):
    manga["logs"].append({"date": days_before(3).isoformat(), "total_minutes": 30,
                          "goal": "manga", "skill": "inking", "goal_minutes": 30,
                          "drawings": 0})
    assert planner.open_fix(manga, "manga", "inking") is None
    assert planner.note_pairs(manga) == []


# ---------- the task shows the last open fix note ----------

def test_r11_open_fix_is_the_newest_open_fix_note_for_that_skill(manga):
    log(manga, days_before(5), fix="hands looked stiff")
    log(manga, days_before(3), fix="lines too thick")
    log(manga, days_before(2), skill="anatomy", fix="proportions off")
    log(manga, days_before(1), fix="")           # a blank note doesn't replace it
    assert planner.open_fix(manga, "manga", "inking") == "lines too thick"
    assert planner.open_fix(manga, "manga", "anatomy") == "proportions off"
    assert planner.open_fix(manga, "manga", "paneling") is None


def test_r11_a_fixed_note_is_no_longer_shown(manga):
    log(manga, days_before(5), fix="hands looked stiff")
    log(manga, days_before(3), fix="lines too thick")
    later = days_before(1)
    checks = planner.fixes_to_check(manga, "manga", "inking", later)
    log(manga, later, fixed={checks[1]: True, checks[0]: False})
    assert planner.open_fix(manga, "manga", "inking") == "hands looked stiff"


def test_r11_cli_task_shows_last_fix_note_for_its_skill(monkeypatch, capsys, manga,
                                                         data_file):
    pair = planner.work_options(manga)[0]          # the first task goes to the first pair
    log(manga, days_before(2), skill=pair[1], fix="panels felt too crowded")
    storage.save(manga, data_file)
    out = run_cli(monkeypatch, capsys, data_file, ["3", "q"], TODAY)
    assert "Last time you wanted to fix: panels felt too crowded" in out
    assert "crowded" not in storage.load(data_file)["tasks"][TODAY.isoformat()]["text"]


def test_r11_cli_task_without_a_fix_note_shows_no_reminder(monkeypatch, capsys, manga,
                                                            data_file):
    log(manga, days_before(2), skill="expressions", fix="faces look the same")
    storage.save(manga, data_file)
    out = run_cli(monkeypatch, capsys, data_file, ["3", "q"], TODAY)
    assert "Last time you wanted to fix" not in out


def test_r11_review_task_also_shows_the_fix_note(monkeypatch, capsys, state, data_file):
    planner.add_goal(state, "manga", dt.date(2026, 10, 1))
    planner.set_target(state, "manga", "paneling", 1)
    planner.record_log(state, dt.date(2026, 10, 1), 60, "manga", "paneling", 60, 0,
                       fix="gutters uneven")
    storage.save(state, data_file)
    out = run_cli(monkeypatch, capsys, data_file, ["3", "q"], TODAY)
    assert "Review paneling" in out
    assert "Last time you wanted to fix: gutters uneven" in out


# ---------- checking a fix at the next log ----------

def test_r11_next_log_checks_every_open_fix_from_earlier_dates_oldest_first(manga):
    a = len(manga["logs"]); log(manga, days_before(5), fix="hands looked stiff")
    b = len(manga["logs"]); log(manga, days_before(3), fix="lines too thick")
    log(manga, days_before(3), skill="anatomy", fix="proportions off")
    c = len(manga["logs"]); log(manga, TODAY, fix="same-day note")
    assert planner.fixes_to_check(manga, "manga", "inking", TODAY) == [a, b]
    assert c not in planner.fixes_to_check(manga, "manga", "inking", TODAY)


def test_r11_yes_marks_fixed_and_no_counts_a_come_back(manga):
    log(manga, days_before(5), fix="hands looked stiff")
    log(manga, days_before(4), fix="lines too thick")
    a, b = planner.fixes_to_check(manga, "manga", "inking", days_before(2))
    log(manga, days_before(2), fixed={a: True, b: False})
    assert manga["logs"][a]["fixed"] == days_before(2).isoformat()
    assert manga["logs"][b]["came_back"] == [days_before(2).isoformat()]
    assert "fixed" not in manga["logs"][b]
    assert planner.fixes_to_check(manga, "manga", "inking", TODAY) == [b]
    log(manga, TODAY, fixed={b: False})
    assert manga["logs"][b]["came_back"] == [days_before(2).isoformat(),
                                            TODAY.isoformat()]


def test_r11_a_fix_is_asked_once_per_date(manga):
    log(manga, days_before(5), fix="hands looked stiff")
    (a,) = planner.fixes_to_check(manga, "manga", "inking", TODAY)
    log(manga, TODAY, fixed={a: False})
    assert planner.fixes_to_check(manga, "manga", "inking", TODAY) == []


def test_r11_checking_a_fix_that_is_not_due_is_rejected(manga):
    log(manga, days_before(5), skill="anatomy", fix="proportions off")
    with pytest.raises(ValueError):
        log(manga, TODAY, fixed={0: True})              # another skill's note
    with pytest.raises(ValueError):
        log(manga, TODAY, fixed={7: True})              # no such log
    assert len(manga["logs"]) == 1 and "fixed" not in manga["logs"][0]


def test_r11_cli_log_asks_fix_check_then_notes(monkeypatch, capsys, manga, data_file):
    log(manga, days_before(3), fix="hands looked stiff")
    storage.save(manga, data_file)
    inking = planner.work_options(manga).index(("manga", "inking")) + 1
    answers = ["4", "60", str(inking), "45", "2", "y", "smooth curves",
               "panels felt too crowded", "q"]
    out = run_cli(monkeypatch, capsys, data_file, answers, TODAY)
    assert "Last time you wanted to fix: hands looked stiff." in out
    saved = storage.load(data_file)["logs"]
    assert saved[0]["fixed"] == TODAY.isoformat()
    assert saved[1]["went_well"] == "smooth curves"
    assert saved[1]["fix"] == "panels felt too crowded"


def test_r11_cli_something_else_log_asks_no_notes(monkeypatch, capsys, manga, data_file):
    storage.save(manga, data_file)
    other = len(planner.work_options(manga)) + 1
    run_cli(monkeypatch, capsys, data_file, ["4", "30", str(other), "0", "q"], TODAY)
    saved = storage.load(data_file)["logs"]
    assert len(saved) == 1 and "fix" not in saved[0]


# ---------- R9: editing and deleting logs with notes ----------

def test_r11_editing_a_log_keeps_its_notes_and_answers(manga):
    log(manga, days_before(5), well="nice", fix="hands looked stiff")
    log(manga, days_before(2), fixed={0: False})
    planner.edit_log(manga, 0, 90, "manga", "anatomy", 80, 2)
    edited = manga["logs"][0]
    assert edited["fix"] == "hands looked stiff" and edited["went_well"] == "nice"
    assert edited["came_back"] == [days_before(2).isoformat()]
    assert planner.open_fix(manga, "manga", "anatomy") == "hands looked stiff"
    assert planner.open_fix(manga, "manga", "inking") is None


def test_r11_notes_of_a_log_edited_to_something_else_are_ignored(manga):
    log(manga, days_before(5), fix="hands looked stiff")
    planner.edit_log(manga, 0, 60, None, None, 0, 0)
    assert planner.open_fix(manga, "manga", "inking") is None
    assert planner.note_pairs(manga) == []


def test_r11_deleting_a_log_removes_its_notes(manga):
    log(manga, days_before(5), fix="hands looked stiff")
    planner.delete_log(manga, 0)
    assert planner.open_fix(manga, "manga", "inking") is None


# ---------- look-back ----------

def lookback_state(manga):
    log(manga, days_before(10), well="good gestures", fix="hands looked stiff")
    log(manga, days_before(9), fix="lines too thick")
    log(manga, days_before(8), fix="panels felt too crowded")
    log(manga, days_before(7), well="clean blacks")
    log(manga, days_before(6), fixed={0: True, 1: False, 2: False})
    log(manga, days_before(5), fixed={1: False})
    log(manga, days_before(4), fix="shading muddy")
    log(manga, days_before(4), skill="anatomy", fix="proportions off")
    return manga


def test_r11_note_pairs_lists_pairs_with_notes_in_roadmap_order(manga):
    lookback_state(manga)
    assert planner.note_pairs(manga) == [("manga", "anatomy"), ("manga", "inking")]


def test_r11_lookback_lists_notes_oldest_first_with_status(manga):
    text = planner.render_notes(lookback_state(manga), "manga", "inking")
    assert text.index("good gestures") < text.index("clean blacks") < \
        text.index("shading muddy")
    assert "fixed {}".format(days_before(6).isoformat()) in text
    assert "came back 2 times" in text
    assert "came back 1 time" in text
    assert "not checked yet" in text
    assert "proportions off" not in text


def test_r11_lookback_groups_fixed_coming_back_and_unchecked(manga):
    groups = planner.note_groups(lookback_state(manga), "manga", "inking")
    assert [n["fix"] for n in groups["fixed"]] == ["hands looked stiff"]
    assert [n["fix"] for n in groups["coming back"]] == ["lines too thick",
                                                         "panels felt too crowded"]
    assert [n["fix"] for n in groups["not checked"]] == ["shading muddy"]


def test_r11_cli_lookback_menu(monkeypatch, capsys, manga, data_file):
    lookback_state(manga)
    manga["notes_reminder"] = TODAY.strftime("%Y-%m")
    storage.save(manga, data_file)
    out = run_cli(monkeypatch, capsys, data_file, [NOTES_MENU, "2", "q"], TODAY)
    assert "11) Look back at notes" in out
    assert "Keeps coming back" in out and "lines too thick" in out


def test_r11_cli_lookback_with_no_notes(monkeypatch, capsys, manga, data_file):
    storage.save(manga, data_file)
    out = run_cli(monkeypatch, capsys, data_file, [NOTES_MENU, "q"], TODAY)
    assert "No notes yet." in out


def test_r11_cli_quit_is_now_12(monkeypatch, capsys, data_file):
    out = run_cli(monkeypatch, capsys, data_file, ["12"], TODAY)
    assert "12) Quit" in out


# ---------- monthly reminder ----------

def test_r11_reminder_is_due_once_a_month_when_older_notes_exist(manga):
    log(manga, dt.date(2026, 10, 30), fix="hands looked stiff")
    assert planner.due_notes_reminder(manga, TODAY) is True
    assert manga["notes_reminder"] == "2026-11"
    assert planner.due_notes_reminder(manga, TODAY) is False
    assert planner.due_notes_reminder(manga, dt.date(2026, 12, 1)) is True


def test_r11_no_reminder_without_notes_from_an_earlier_month(manga):
    log(manga, dt.date(2026, 11, 3), fix="hands looked stiff")
    planner.record_log(manga, dt.date(2026, 10, 20), 60, "manga", "inking", 60, 0)
    assert planner.due_notes_reminder(manga, TODAY) is False
    assert manga["notes_reminder"] is None
    assert storage.new_state()["notes_reminder"] is None


def test_r11_cli_shows_reminder_at_start_and_records_it(monkeypatch, capsys, state,
                                                        data_file):
    planner.add_goal(state, "manga", dt.date(2026, 10, 1))
    planner.record_log(state, dt.date(2026, 10, 1), 60, "manga", "inking", 30, 0,
                       fix="hands looked stiff")
    state["summaries"] = [planner.last_finished_week(TODAY).isoformat()]
    storage.save(state, data_file)
    out = run_cli(monkeypatch, capsys, data_file, ["q"], TODAY)
    assert "look back at your notes" in out
    assert storage.load(data_file)["notes_reminder"] == "2026-11"
    out = run_cli(monkeypatch, capsys, data_file, ["q"], TODAY)
    assert "look back at your notes" not in out
