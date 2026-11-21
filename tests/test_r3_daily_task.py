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


# ---------- round 3: rotation and focus weeks (R3 changed) ----------

MONDAY = dt.date(2026, 11, 16)        # week of TODAY (Fri 2026-11-20)
LAST_MONDAY = dt.date(2026, 11, 9)    # the week before


def _days(start, n):
    return [start + dt.timedelta(days=i) for i in range(n)]


def _task_pairs(state, days):
    return [(planner.daily_task(state, d)["goal"], planner.daily_task(state, d)["skill"])
            for d in days]


def _neglect_inking(state):
    """Manga active all of last week, with time on every skill except inking."""
    planner.add_goal(state, "manga", LAST_MONDAY)
    for skill in planner.CATALOG["manga"]:
        if skill != "inking":
            planner.record_log(state, LAST_MONDAY, 60, "manga", skill, 60, 0)


def test_r3_tasks_rotate_through_every_skill_in_order(state):
    planner.add_goal(state, "manga", TODAY)
    skills = planner.CATALOG["manga"]
    pairs = _task_pairs(state, _days(TODAY, len(skills) + 1))
    assert [s for _, s in pairs] == skills + [skills[0]]


def test_r3_rotation_covers_every_goal_in_roadmap_order(state):
    planner.add_goal(state, "manga", TODAY)
    planner.add_goal(state, "figure", TODAY)
    options = planner.work_options(state)
    assert _task_pairs(state, _days(TODAY, len(options))) == options


def test_r3_missed_day_does_not_skip_a_skill(state):
    planner.add_goal(state, "manga", TODAY)
    planner.daily_task(state, TODAY)
    later = planner.daily_task(state, TODAY + dt.timedelta(days=3))
    assert later["skill"] == planner.CATALOG["manga"][1]


def test_r3_rotation_does_not_follow_logged_skill(state):
    planner.add_goal(state, "manga", TODAY)
    skills = planner.CATALOG["manga"]
    planner.daily_task(state, TODAY)
    planner.record_log(state, TODAY, 90, "manga", skills[3], 90, 0)
    assert planner.daily_task(state, TODAY + dt.timedelta(days=1))["skill"] == skills[1]


def test_r3_goal_added_later_joins_rotation(state):
    planner.add_goal(state, "manga", TODAY)
    for d in _days(TODAY, len(planner.CATALOG["manga"])):
        planner.daily_task(state, d)          # last task: manga's last skill
    day = TODAY + dt.timedelta(days=len(planner.CATALOG["manga"]))
    planner.add_goal(state, "figure", day)
    task = planner.daily_task(state, day)
    assert (task["goal"], task["skill"]) == ("figure", planner.CATALOG["figure"][0])


def test_r3_focus_skill_gets_monday_wednesday_friday_sunday(state):
    _neglect_inking(state)
    pairs = _task_pairs(state, _days(MONDAY, 7))
    focus_days = [i for i, p in enumerate(pairs) if p == ("manga", "inking")]
    assert focus_days == [0, 2, 4, 6]


def test_r3_other_days_rotate_and_skip_the_focus_skill(state):
    _neglect_inking(state)
    pairs = _task_pairs(state, _days(MONDAY, 7))
    others = [s for _, s in pairs[1::2]]                # Tue, Thu, Sat
    assert others == ["paneling", "anatomy", "penning"]


def test_r3_focus_task_text_says_it_is_the_focus(state):
    _neglect_inking(state)
    assert "focus" in planner.daily_task(state, MONDAY)["text"].lower()
    assert "focus" not in planner.daily_task(state, MONDAY + dt.timedelta(days=1))[
        "text"].lower()


def test_r3_balanced_week_means_plain_rotation(state):
    planner.add_goal(state, "manga", LAST_MONDAY)
    for skill in planner.CATALOG["manga"]:
        planner.record_log(state, LAST_MONDAY, 60, "manga", skill, 60, 0)
    pairs = _task_pairs(state, _days(MONDAY, 5))
    assert [s for _, s in pairs] == planner.CATALOG["manga"]


def test_r3_focus_lasts_only_the_week_after_the_summary(state):
    _neglect_inking(state)
    next_monday = MONDAY + dt.timedelta(days=7)
    # This week: inking catches up (it gets far more time than the rest).
    planner.record_log(state, MONDAY, 300, "manga", "inking", 300, 0)
    for skill in planner.CATALOG["manga"]:
        if skill != "inking":
            planner.record_log(state, MONDAY, 60, "manga", skill, 60, 0)
    assert planner.focus_pair(state, MONDAY) == ("manga", "inking")
    assert planner.focus_pair(state, next_monday) is None


def test_r3_focus_continues_while_skill_stays_neglected(state):
    _neglect_inking(state)
    next_monday = MONDAY + dt.timedelta(days=7)
    for skill in planner.CATALOG["manga"]:
        if skill != "inking":
            planner.record_log(state, MONDAY, 60, "manga", skill, 60, 0)
    assert planner.focus_pair(state, next_monday) == ("manga", "inking")
