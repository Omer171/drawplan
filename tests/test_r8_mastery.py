import datetime as dt

import pytest

from drawplan import planner, storage
from tests.conftest import TODAY
from tests.test_r7_weekly import run_cli

SKILLS = planner.CATALOG["manga"]        # paneling, anatomy, penning, inking, expressions
MONDAY = dt.date(2026, 11, 16)           # the week of TODAY (Fri 2026-11-20)
LAST_MONDAY = dt.date(2026, 11, 9)


def days(n):
    return dt.timedelta(days=n)


@pytest.fixture
def manga(state):
    planner.add_goal(state, "manga", TODAY)
    return state


def log(state, day, skill, minutes, goal="manga"):
    planner.record_log(state, day, minutes, goal, skill, minutes, 0)


def master(state, day, skill, goal="manga"):
    """Master a skill quickly: target 1 hour, then log one hour on it."""
    planner.set_target(state, goal, skill, 1)
    log(state, day, skill, 60, goal)


def pair(task):
    return task["goal"], task["skill"]


# ---------- targets ----------

def test_r8_default_target_is_20_hours(manga):
    assert all(planner.target_hours(manga, g, s) == 20 for g, s in planner.work_options(manga))


def test_r8_set_target_changes_the_bar_and_is_saved(manga, data_file):
    planner.set_target(manga, "manga", "anatomy", 50)
    planner.set_target(manga, "manga", "inking", 15)
    log(manga, TODAY, "inking", 90)
    assert planner.target_hours(manga, "manga", "anatomy") == 50
    lines = planner.render_roadmap(manga, TODAY).splitlines()
    inking = next(line for line in lines if line.strip().startswith("inking"))
    assert "10%" in inking and "1.5/15h" in inking
    assert "0.0/50h" in next(line for line in lines if line.strip().startswith("anatomy"))
    storage.save(manga, data_file)
    assert storage.load(data_file)["targets"] == {"manga": {"anatomy": 50, "inking": 15}}


@pytest.mark.parametrize("hours", [0, 1001, -5, "10", 2.5, True, None])
def test_r8_target_must_be_whole_hours_from_1_to_1000(manga, hours):
    with pytest.raises(ValueError):
        planner.set_target(manga, "manga", "inking", hours)
    assert manga["targets"] == {}


def test_r8_target_for_a_pair_not_in_the_goals_is_rejected(manga):
    with pytest.raises(ValueError):
        planner.set_target(manga, "figure", "gesture", 10)
    assert manga["targets"] == {}


def test_r8_target_can_go_down_before_mastery(manga):
    planner.set_target(manga, "manga", "inking", 40)
    planner.set_target(manga, "manga", "inking", 10)
    assert planner.target_hours(manga, "manga", "inking") == 10


def test_r8_file_without_targets_loads(data_file):
    data_file.write_text('{"version": 1, "goals": [], "logs": [], "tasks": {}, '
                         '"task_minutes": 30}', encoding="utf-8")
    state = storage.load(data_file)
    assert state["targets"] == {} and state["mastered_targets"] == {}


# ---------- mastery ----------

def test_r8_skill_is_mastered_at_100_percent_of_its_target(manga):
    planner.set_target(manga, "manga", "inking", 2)
    log(manga, TODAY, "inking", 119)
    assert not planner.is_mastered(manga, "manga", "inking")
    log(manga, TODAY, "inking", 1)
    assert planner.is_mastered(manga, "manga", "inking")
    assert not planner.is_mastered(manga, "manga", "paneling")


def test_r8_lowering_the_target_can_master_a_skill(manga):
    log(manga, TODAY, "inking", 120)
    assert not planner.is_mastered(manga, "manga", "inking")
    planner.set_target(manga, "manga", "inking", 2)
    assert planner.is_mastered(manga, "manga", "inking")


def test_r8_mastered_skill_target_can_only_be_raised(manga):
    master(manga, TODAY, "inking")
    for hours in (1, 0, 1001):
        with pytest.raises(ValueError):
            planner.set_target(manga, "manga", "inking", hours)
    assert planner.target_hours(manga, "manga", "inking") == 1
    assert manga["mastered_targets"] == {}


def test_r8_raising_a_mastered_target_records_it_and_unmasters(manga):
    master(manga, TODAY, "inking")
    planner.set_target(manga, "manga", "inking", 30)
    assert planner.target_hours(manga, "manga", "inking") == 30
    assert manga["mastered_targets"] == {"manga": {"inking": [1]}}
    assert not planner.is_mastered(manga, "manga", "inking")


def test_r8_target_must_stay_above_earlier_mastered_targets(manga):
    planner.set_target(manga, "manga", "inking", 15)
    log(manga, TODAY, "inking", 15 * 60)
    planner.set_target(manga, "manga", "inking", 30)
    with pytest.raises(ValueError):
        planner.set_target(manga, "manga", "inking", 15)
    planner.set_target(manga, "manga", "inking", 16)
    assert planner.target_hours(manga, "manga", "inking") == 16


def test_r8_earlier_mastery_stays_a_reached_milestone_and_keeps_its_xp(manga):
    planner.set_target(manga, "manga", "inking", 15)
    log(manga, TODAY, "inking", 15 * 60)
    xp = planner.player_xp(manga)
    planner.set_target(manga, "manga", "inking", 30)
    reached = dict(planner.goal_milestones(manga, "manga"))
    assert reached["Master inking (15h)"] is True
    assert reached["Master inking"] is False
    assert planner.player_xp(manga) == xp
    log(manga, TODAY, "inking", 15 * 60)
    assert dict(planner.goal_milestones(manga, "manga"))["Master inking"] is True
    assert planner.player_xp(manga) > xp


def test_r8_roadmap_marks_mastered_skills(manga):
    master(manga, TODAY, "inking")
    lines = planner.render_roadmap(manga, TODAY).splitlines()
    assert "MASTERED" in next(line for line in lines if line.strip().startswith("inking"))
    assert "MASTERED" not in next(line for line in lines
                                  if line.strip().startswith("penning"))


def test_r8_mastery_date_is_the_log_that_reached_the_target(manga):
    planner.set_target(manga, "manga", "inking", 2)
    log(manga, TODAY, "inking", 60)
    log(manga, TODAY + days(3), "inking", 60)
    log(manga, TODAY + days(5), "inking", 60)
    assert planner.mastery_date(manga, "manga", "inking") == TODAY + days(3)
    assert planner.mastery_date(manga, "manga", "paneling") is None


# ---------- rotation and review tasks ----------

def test_r8_mastered_skill_leaves_the_rotation(manga):
    master(manga, TODAY, "paneling")
    tasks = [pair(planner.daily_task(manga, TODAY + days(i))) for i in range(5)]
    assert ("manga", "paneling") not in tasks
    assert [s for _, s in tasks] == SKILLS[1:] + [SKILLS[1]]


def test_r8_rotation_carries_on_after_the_last_task_skill_is_mastered(manga):
    for i in range(3):
        planner.daily_task(manga, TODAY + days(i))     # paneling, anatomy, penning
    master(manga, TODAY + days(2), "penning")
    assert planner.daily_task(manga, TODAY + days(3))["skill"] == "inking"


def test_r8_review_is_due_14_days_after_mastery_and_takes_the_slot(manga):
    master(manga, TODAY, "paneling")
    assert not planner.daily_task(manga, TODAY + days(13)).get("review")
    task = planner.daily_task(manga, TODAY + days(14))
    assert pair(task) == ("manga", "paneling") and task["review"] is True
    assert task["minutes"] == 15                                     # half of 30
    assert "review" in task["text"].lower() and "paneling" in task["text"]


def test_r8_review_is_due_again_14_days_after_the_last_review(manga):
    master(manga, TODAY, "paneling")
    planner.daily_task(manga, TODAY + days(14))
    assert not planner.daily_task(manga, TODAY + days(27)).get("review")
    assert planner.daily_task(manga, TODAY + days(28))["review"] is True


def test_r8_review_stays_due_until_a_task_is_given(manga):
    master(manga, TODAY, "paneling")
    assert planner.daily_task(manga, TODAY + days(20))["review"] is True


def test_r8_review_task_is_at_least_10_minutes(manga):
    manga["task_minutes"] = 15
    master(manga, TODAY, "paneling")
    assert planner.daily_task(manga, TODAY + days(14))["minutes"] == 10


def test_r8_longest_waiting_review_goes_first(manga):
    master(manga, TODAY + days(1), "anatomy")
    master(manga, TODAY, "inking")
    assert pair(planner.daily_task(manga, TODAY + days(15))) == ("manga", "inking")
    assert pair(planner.daily_task(manga, TODAY + days(16))) == ("manga", "anatomy")


def test_r8_review_task_counts_like_any_task_for_r4(manga):
    master(manga, TODAY, "paneling")
    review_day = TODAY + days(14)
    planner.daily_task(manga, review_day)
    log(manga, review_day, "paneling", 15)
    assert manga["tasks"][review_day.isoformat()]["completed"] is True
    assert manga["task_minutes"] == 35


def _neglect_expressions_last_week(state, skip_paneling=False):
    for i, skill in enumerate(SKILLS[:4]):
        if not (skip_paneling and skill == "paneling"):
            log(state, LAST_MONDAY + days(i), skill, 60)


def test_r8_focus_day_wins_over_a_due_review(state):
    planner.add_goal(state, "manga", dt.date(2026, 11, 2))
    master(state, dt.date(2026, 11, 2), "paneling")           # review due Mon 11-16
    _neglect_expressions_last_week(state, skip_paneling=True)
    assert pair(planner.daily_task(state, MONDAY)) == ("manga", "expressions")
    tuesday = planner.daily_task(state, MONDAY + days(1))
    assert pair(tuesday) == ("manga", "paneling") and tuesday["review"]


def test_r8_focus_skill_mastered_since_is_no_longer_the_focus(state):
    planner.add_goal(state, "manga", LAST_MONDAY)
    _neglect_expressions_last_week(state)
    master(state, MONDAY, "expressions")
    task = planner.daily_task(state, MONDAY)
    assert pair(task) == ("manga", "paneling") and "focus" not in task["text"]


def test_r8_all_mastered_means_no_task_until_a_review_is_due(state):
    planner.add_goal(state, "portraits", TODAY)
    for skill in planner.CATALOG["portraits"]:
        master(state, TODAY, skill, "portraits")
    assert planner.all_mastered(state)
    assert planner.daily_task(state, TODAY + days(1)) is None
    assert state["tasks"] == {}
    task = planner.daily_task(state, TODAY + days(14))
    assert pair(task) == ("portraits", "proportions") and task["review"]


# ---------- CLI ----------

def test_r8_cli_sets_a_skill_target(monkeypatch, capsys, manga, data_file):
    storage.save(manga, data_file)
    out = run_cli(monkeypatch, capsys, data_file, ["8", "4", "15", "q"], TODAY)
    assert "inking" in out
    assert storage.load(data_file)["targets"] == {"manga": {"inking": 15}}


def test_r8_cli_rejected_target_is_explained_and_not_saved(monkeypatch, capsys, manga,
                                                           data_file):
    master(manga, TODAY, "inking")
    storage.save(manga, data_file)
    out = run_cli(monkeypatch, capsys, data_file, ["8", "4", "1", "q"], TODAY)
    assert "raise" in out.lower()
    assert storage.load(data_file)["mastered_targets"] == {}


def test_r8_cli_all_mastered_says_so(monkeypatch, capsys, state, data_file):
    planner.add_goal(state, "portraits", TODAY)
    for skill in planner.CATALOG["portraits"]:
        master(state, TODAY, skill, "portraits")
    storage.save(state, data_file)
    out = run_cli(monkeypatch, capsys, data_file, ["3", "q"], TODAY + days(1))
    assert "mastered" in out.lower() and "raise" in out.lower()
