import datetime as dt

import pytest

from drawplan import planner, storage
from tests.conftest import TODAY

TOMORROW = TODAY + dt.timedelta(days=1)


@pytest.fixture
def manga(state):
    planner.add_goal(state, "manga", TODAY)
    return state


def test_r4_log_is_recorded_with_all_answers(manga):
    entry = planner.record_log(manga, TODAY, 90, "manga", "inking", 60, 4)
    assert entry == {"date": "2026-11-20", "total_minutes": 90, "goal": "manga",
                     "skill": "inking", "goal_minutes": 60, "drawings": 4}
    assert manga["logs"] == [entry]


def test_r4_log_survives_save_and_load(manga, data_file):
    planner.record_log(manga, TODAY, 90, "manga", "inking", 60, 4)
    storage.save(manga, data_file)
    assert storage.load(data_file)["logs"] == manga["logs"]


def test_r4_work_options_list_every_goal_skill_pair(manga):
    planner.add_goal(manga, "figure", TODAY)
    options = planner.work_options(manga)
    assert options[0] == ("manga", planner.CATALOG["manga"][0])
    assert len(options) == len(planner.CATALOG["manga"]) + len(planner.CATALOG["figure"])


def test_r4_credit_goes_to_skill_actually_worked_on(manga):
    task = planner.daily_task(manga, TODAY)
    assert task["skill"] != "inking"
    planner.record_log(manga, TODAY, 45, "manga", "inking", 45, 0)
    progress = planner.skill_progress(manga, "manga")
    assert progress["inking"] == 45
    assert progress[task["skill"]] == 0


def test_r4_something_else_counts_total_but_not_goal(manga):
    planner.record_log(manga, TODAY, 50, None, None, 0, 2)
    assert planner.total_minutes(manga) == 50
    assert planner.goal_minutes(manga, "manga") == 0


def test_r4_next_task_targets_most_neglected_skill(manga):
    skills = planner.CATALOG["manga"]
    for skill in skills[:-1]:
        planner.record_log(manga, TODAY, 30, "manga", skill, 30, 0)
    assert planner.daily_task(manga, TOMORROW)["skill"] == skills[-1]


def test_r4_neglect_is_compared_across_goals(manga):
    planner.add_goal(manga, "figure", TODAY)
    for skill in planner.CATALOG["manga"]:
        planner.record_log(manga, TODAY, 10, "manga", skill, 10, 0)
    assert planner.daily_task(manga, TOMORROW)["goal"] == "figure"


def test_r4_full_task_makes_next_task_longer(manga):
    task = planner.daily_task(manga, TODAY)
    planner.record_log(manga, TODAY, 30, "manga", task["skill"], 30, 0)
    assert planner.daily_task(manga, TOMORROW)["minutes"] == 35


def test_r4_full_time_on_other_skill_still_counts_as_done(manga):
    planner.daily_task(manga, TODAY)
    planner.record_log(manga, TODAY, 40, "manga", "inking", 40, 0)
    assert manga["task_minutes"] == 35


def test_r4_falling_short_makes_next_task_shorter(manga):
    planner.daily_task(manga, TODAY)
    planner.record_log(manga, TODAY, 60, "manga", "inking", 20, 0)
    assert planner.daily_task(manga, TOMORROW)["minutes"] == 25


def test_r4_only_first_log_of_a_day_adjusts_length(manga):
    planner.daily_task(manga, TODAY)
    planner.record_log(manga, TODAY, 30, "manga", "inking", 30, 0)
    planner.record_log(manga, TODAY, 30, "manga", "inking", 30, 0)
    assert manga["task_minutes"] == 35


def test_r4_log_without_task_does_not_adjust_length(manga):
    planner.record_log(manga, TODAY, 5, "manga", "inking", 5, 0)
    assert manga["task_minutes"] == 30


def test_r4_task_length_stays_between_10_and_120(manga):
    manga["task_minutes"] = 120
    planner.daily_task(manga, TODAY)
    planner.record_log(manga, TODAY, 200, "manga", "inking", 200, 0)
    assert manga["task_minutes"] == 120
    manga["task_minutes"] = 10
    planner.daily_task(manga, TOMORROW)
    planner.record_log(manga, TOMORROW, 0, None, None, 0, 0)
    assert manga["task_minutes"] == 10


@pytest.mark.parametrize("total, goal, skill, goal_min, drawings", [
    (-1, "manga", "inking", 0, 0),          # negative total
    (30, "manga", "inking", 40, 0),         # on-goal more than total
    (30, "manga", "inking", -5, 0),         # negative on-goal
    (30, "manga", "inking", 10, -1),        # negative drawings
    (30, "figure", "gesture", 10, 0),       # goal not active
    (30, "manga", "shading", 10, 0),        # skill not in goal
    (30, None, None, 10, 0),                # "something else" with on-goal time
    (30.5, "manga", "inking", 10, 0),       # not a whole number
])
def test_r4_invalid_log_rejected_and_nothing_saved(manga, total, goal, skill,
                                                   goal_min, drawings):
    planner.daily_task(manga, TODAY)
    with pytest.raises(ValueError):
        planner.record_log(manga, TODAY, total, goal, skill, goal_min, drawings)
    assert manga["logs"] == []
    assert manga["task_minutes"] == 30
    assert not manga["tasks"][TODAY.isoformat()]["adjusted"]
