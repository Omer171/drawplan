import datetime as dt

from drawplan import planner, storage
from tests.conftest import TODAY


def test_r3_no_goals_means_no_task(state):
    assert planner.daily_task(state, TODAY) is None
    assert state["tasks"] == {}


def test_r3_first_task_is_first_skill_of_first_goal_at_30_minutes(state):
    planner.add_goal(state, "manga", TODAY)
    planner.add_goal(state, "figure", TODAY)
    task = planner.daily_task(state, TODAY)
    assert task["goal"] == "manga"
    assert task["skill"] == planner.CATALOG["manga"][0]
    assert task["minutes"] == 30


def test_r3_task_text_is_specific(state):
    planner.add_goal(state, "portraits", TODAY)
    task = planner.daily_task(state, TODAY)
    assert "30 minutes" in task["text"]
    assert task["skill"] in task["text"]
    assert "portraits" in task["text"]
    assert any(ex in task["text"] for ex in planner.EXERCISES[task["skill"]])


def test_r3_same_task_all_day_even_after_progress(state):
    planner.add_goal(state, "manga", TODAY)
    first = dict(planner.daily_task(state, TODAY))
    planner.record_log(state, TODAY, 120, "manga", first["skill"], 120, 0)
    assert planner.daily_task(state, TODAY)["skill"] == first["skill"]
    assert planner.daily_task(state, TODAY)["text"] == first["text"]


def test_r3_task_survives_save_and_load(state, data_file):
    planner.add_goal(state, "comic", TODAY)
    task = dict(planner.daily_task(state, TODAY))
    storage.save(state, data_file)
    reloaded = storage.load(data_file)
    assert planner.daily_task(reloaded, TODAY) == task


def test_r3_new_task_on_a_new_day(state):
    planner.add_goal(state, "manga", TODAY)
    planner.daily_task(state, TODAY)
    tomorrow = TODAY + dt.timedelta(days=1)
    planner.daily_task(state, tomorrow)
    assert set(state["tasks"]) == {TODAY.isoformat(), tomorrow.isoformat()}


def test_r3_every_catalog_skill_has_exercises():
    for skills in planner.CATALOG.values():
        for skill in skills:
            assert planner.EXERCISES[skill]


def test_r3_exercise_varies_by_date(state):
    planner.add_goal(state, "manga", TODAY)
    skill = planner.CATALOG["manga"][0]
    texts = set()
    for d in range(len(planner.EXERCISES[skill])):
        fresh = storage.new_state()
        planner.add_goal(fresh, "manga", TODAY)
        texts.add(planner.daily_task(fresh, TODAY + dt.timedelta(days=d))["text"])
    assert len(texts) > 1
