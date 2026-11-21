import datetime as dt

import pytest

from drawplan import gallery, planner
from tests.conftest import TODAY


@pytest.fixture
def manga(state):
    planner.add_goal(state, "manga", TODAY)
    return state


def log(state, minutes, skill="inking", total=None, day=TODAY, goal="manga"):
    planner.record_log(state, day, total if total is not None else minutes,
                       goal, skill, minutes, 0)


def off_goal(state, minutes, day=TODAY):
    planner.record_log(state, day, minutes, None, None, 0, 0)


@pytest.mark.parametrize("lvl,xp", [(1, 0), (2, 50), (3, 150), (4, 300), (5, 500)])
def test_r6_level_curve(lvl, xp):
    assert planner.xp_for_level(lvl) == xp
    assert planner.level_for_xp(xp) == lvl
    assert planner.level_for_xp(xp - 1) == max(1, lvl - 1)


def test_r6_ten_xp_per_on_goal_hour_per_skill(manga):
    log(manga, 30)
    log(manga, 59)  # 89 minutes -> 14 XP (floored)
    assert planner.skill_xp(manga, "manga", "inking") == 14
    assert planner.skill_xp(manga, "manga", "paneling") == 0


def test_r6_off_goal_time_earns_no_skill_xp(manga):
    off_goal(manga, 600)
    assert all(planner.skill_xp(manga, "manga", s) == 0 for s in planner.CATALOG["manga"])


def test_r6_same_skill_in_two_goals_has_separate_xp(manga):
    planner.add_goal(manga, "comic", TODAY)
    log(manga, 60, goal="comic", skill="anatomy")
    assert planner.skill_xp(manga, "comic", "anatomy") == 10
    assert planner.skill_xp(manga, "manga", "anatomy") == 0


def test_r6_completed_task_gives_20_xp_to_task_skill(manga):
    task = planner.daily_task(manga, TODAY)  # 30 minutes on manga/paneling
    assert task["skill"] == "paneling"
    log(manga, 30, skill="inking")
    assert task["completed"] is True
    assert planner.skill_xp(manga, "manga", "paneling") == 20
    assert planner.skill_xp(manga, "manga", "inking") == 5


def test_r6_incomplete_task_gives_no_task_xp(manga):
    task = planner.daily_task(manga, TODAY)
    log(manga, 29, skill="paneling")
    assert task["completed"] is False
    assert planner.skill_xp(manga, "manga", "paneling") == 29 * 10 // 60


def test_r6_only_first_log_can_complete_task(manga):
    task = planner.daily_task(manga, TODAY)
    log(manga, 5, skill="paneling")
    log(manga, 60, skill="paneling")
    assert task["completed"] is False


def test_r6_old_adjusted_task_without_completed_flag_is_derived(manga):
    manga["tasks"]["2026-11-19"] = {"goal": "manga", "skill": "paneling", "minutes": 30,
                                   "text": "", "adjusted": True}
    log(manga, 45, day=TODAY - dt.timedelta(days=1))
    assert planner.skill_xp(manga, "manga", "paneling") == 20


def test_r6_skill_level_from_skill_xp(manga):
    log(manga, 300)  # 50 XP
    assert planner.skill_level(manga, "manga", "inking") == 2
    assert planner.skill_level(manga, "manga", "paneling") == 1


def test_r6_milestone_bonus_is_100_xp_each(manga):
    assert planner.player_xp(manga) == 0
    log(manga, 60)  # 10 study XP + "1 hour on manga" milestone
    assert planner.player_xp(manga) == 110
    assert planner.level(manga) == 2


def test_r6_overall_milestones_give_bonus_too(manga):
    off_goal(manga, 600)  # "10 total study hours"
    assert planner.player_xp(manga) == 100


def test_r6_player_xp_sums_skills_and_bonuses(manga):
    planner.daily_task(manga, TODAY)
    log(manga, 30, skill="paneling")  # 5 study + 20 task
    log(manga, 30, day=TODAY + dt.timedelta(days=1))  # 5 study, reaches 1h milestone
    assert planner.player_xp(manga) == 5 + 20 + 5 + 100


def test_r6_next_level_xp(manga):
    assert planner.next_level_xp(manga) == 50
    log(manga, 60)  # 110 XP, level 2
    assert planner.next_level_xp(manga) == 150


def test_r6_roadmap_shows_player_and_skill_levels(manga):
    log(manga, 300)  # 50 skill XP + 1h milestone 100 = 150 player XP -> level 3
    text = planner.render_roadmap(manga, TODAY)
    assert "Level 3" in text and "150 XP" in text and "next level at 300 XP" in text
    lines = [line.strip() for line in text.splitlines()]
    inking = next(line for line in lines if line.startswith("inking"))
    assert "lvl 2" in inking and "50 XP" in inking
    paneling = next(line for line in lines if line.startswith("paneling"))
    assert "lvl 1" in paneling and " 0 XP" in paneling


def test_r6_streak_ignores_zero_minute_logs(manga):
    log(manga, 10, day=TODAY - dt.timedelta(days=1))
    off_goal(manga, 0)
    assert planner.streak(manga, TODAY) == 1  # today does not count, yesterday does
    off_goal(manga, 0, day=TODAY - dt.timedelta(days=2))
    assert planner.streak(manga, TODAY) == 1


def test_r6_saved_art_counts_as_a_drawing_day(manga, tmp_path):
    src = tmp_path / "a.png"
    src.write_bytes(b"x")
    gallery.save_art(manga, TODAY, str(src), "manga", "inking", tmp_path / "drawplan_art")
    log(manga, 10, day=TODAY - dt.timedelta(days=1))
    assert planner.streak(manga, TODAY) == 2
