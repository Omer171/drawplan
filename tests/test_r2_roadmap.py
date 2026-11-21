import datetime as dt

from drawplan import planner
from tests.conftest import TODAY


def log(state, minutes, goal="manga", skill="inking", drawings=0, total=None,
        day=TODAY):
    planner.record_log(state, day, total if total is not None else minutes,
                       goal, skill, minutes, drawings)


def test_r2_progress_bar_shapes():
    assert planner.progress_bar(0, width=10) == "[----------]"
    assert planner.progress_bar(0.5, width=10) == "[#####-----]"
    assert planner.progress_bar(1.7, width=10) == "[##########]"


def test_r2_skill_progress_starts_at_zero_for_each_skill(state):
    planner.add_goal(state, "manga", TODAY)
    progress = planner.skill_progress(state, "manga")
    assert list(progress) == planner.CATALOG["manga"]
    assert set(progress.values()) == {0}


def test_r2_skill_progress_sums_on_goal_minutes_only(state):
    planner.add_goal(state, "manga", TODAY)
    log(state, 30, total=90)
    log(state, 15)
    assert planner.skill_progress(state, "manga")["inking"] == 45


def test_r2_same_skill_in_two_goals_tracked_separately(state):
    planner.add_goal(state, "manga", TODAY)
    planner.add_goal(state, "comic", TODAY)
    log(state, 60, goal="comic", skill="anatomy")
    assert planner.skill_progress(state, "comic")["anatomy"] == 60
    assert planner.skill_progress(state, "manga")["anatomy"] == 0


def test_r2_roadmap_shows_a_bar_per_skill(state):
    planner.add_goal(state, "manga", TODAY)
    log(state, 600)  # 10h of 20h target
    text = planner.render_roadmap(state, TODAY)
    for skill in planner.CATALOG["manga"]:
        assert skill in text
    inking_line = next(l for l in text.splitlines() if l.strip().startswith("inking"))
    assert "50%" in inking_line and "10.0/20h" in inking_line


def test_r2_roadmap_covers_every_goal(state):
    planner.add_goal(state, "figure", TODAY)
    planner.add_goal(state, "portraits", TODAY)
    text = planner.render_roadmap(state, TODAY)
    assert "FIGURE" in text and "PORTRAITS" in text


def test_r2_roadmap_without_goals_says_so(state):
    assert "No goals yet" in planner.render_roadmap(state, TODAY)


def test_r2_goal_milestones_hours_drawings_and_mastery(state):
    planner.add_goal(state, "manga", TODAY)
    log(state, 1200, drawings=12)  # inking mastered, 20h, 12 drawings
    reached = {label: done for label, done in planner.goal_milestones(state, "manga")}
    assert reached["1 hour on manga"] and reached["10 hours on manga"]
    assert not reached["50 hours on manga"]
    assert reached["10 drawings"] and not reached["50 drawings"]
    assert reached["Master inking"] and not reached["Master paneling"]


def test_r2_overall_hours_use_total_study_time(state):
    planner.add_goal(state, "manga", TODAY)
    log(state, 0, total=600, goal=None, skill=None)  # 10h, none on-goal
    reached = dict(planner.overall_milestones(state))
    assert reached["10 total study hours"]
    assert not reached["50 total study hours"]
    assert planner.goal_minutes(state, "manga") == 0


def test_r2_streak_counts_consecutive_days(state):
    planner.add_goal(state, "manga", TODAY)
    for back in (0, 1, 2, 4):
        log(state, 10, day=TODAY - dt.timedelta(days=back))
    assert planner.streak(state, TODAY) == 3


def test_r2_streak_still_alive_if_last_log_was_yesterday(state):
    planner.add_goal(state, "manga", TODAY)
    log(state, 10, day=TODAY - dt.timedelta(days=1))
    assert planner.streak(state, TODAY) == 1
    assert planner.streak(state, TODAY + dt.timedelta(days=1)) == 0


def test_r2_roadmap_marks_reached_milestones(state):
    planner.add_goal(state, "manga", TODAY)
    log(state, 60)
    text = planner.render_roadmap(state, TODAY)
    assert "[x] 1 hour on manga" in text
    assert "[ ] 10 hours on manga" in text
    # 10 study XP + 100 XP for the "1 hour" milestone (R6) -> level 2
    assert "Level 2" in text and "Streak: 1 day" in text


def test_r2_roadmap_is_plain_ascii(state):
    planner.add_goal(state, "animation", TODAY)
    planner.render_roadmap(state, TODAY).encode("ascii")
