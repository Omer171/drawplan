import json

import pytest

from drawplan import planner, storage
from tests.conftest import TODAY


def test_r1_catalog_has_the_six_goals():
    assert list(planner.CATALOG) == [
        "portraits", "figure", "anatomy", "manga", "comic", "animation"]


def test_r1_every_goal_has_several_skills():
    for skills in planner.CATALOG.values():
        assert len(skills) >= 3


def test_r1_add_goal_by_name(state):
    assert planner.add_goal(state, "manga", TODAY) == "manga"
    assert state["goals"] == [{"name": "manga", "added": "2026-11-20"}]


def test_r1_add_goal_by_number_and_ignores_case_and_spaces(state):
    assert planner.add_goal(state, "1", TODAY) == "portraits"
    assert planner.add_goal(state, "  Comic ", TODAY) == "comic"


def test_r1_several_goals_kept_in_order(state):
    planner.add_goal(state, "figure", TODAY)
    planner.add_goal(state, "animation", TODAY)
    assert planner.active_goals(state) == ["figure", "animation"]


def test_r1_duplicate_goal_rejected(state):
    planner.add_goal(state, "manga", TODAY)
    with pytest.raises(ValueError):
        planner.add_goal(state, "manga", TODAY)
    assert len(state["goals"]) == 1


@pytest.mark.parametrize("bad", ["", "painting", "0", "7", "-1"])
def test_r1_unknown_goal_rejected(state, bad):
    with pytest.raises(ValueError):
        planner.add_goal(state, bad, TODAY)
    assert state["goals"] == []


def test_r1_goal_is_saved_and_loaded(state, data_file):
    planner.add_goal(state, "anatomy", TODAY)
    storage.save(state, data_file)
    assert storage.load(data_file)["goals"][0]["name"] == "anatomy"


def test_r1_missing_file_loads_empty_state(data_file):
    assert storage.load(data_file) == storage.new_state()


def test_r1_corrupt_file_raises_and_is_not_overwritten(data_file):
    data_file.write_text("{not json", encoding="utf-8")
    with pytest.raises(storage.StorageError):
        storage.load(data_file)
    assert data_file.read_text(encoding="utf-8") == "{not json"


def test_r1_saved_file_is_valid_json_without_leftover_temp(state, data_file):
    storage.save(state, data_file)
    assert json.loads(data_file.read_text(encoding="utf-8"))["version"] == 1
    assert [p.name for p in data_file.parent.iterdir()] == [data_file.name]


def test_r1_data_path_uses_env_var(monkeypatch, tmp_path):
    monkeypatch.setenv("DRAWPLAN_DATA", str(tmp_path / "x.json"))
    assert storage.data_path() == tmp_path / "x.json"


def test_r1_data_path_defaults_to_current_dir(monkeypatch):
    monkeypatch.delenv("DRAWPLAN_DATA", raising=False)
    assert storage.data_path().name == "drawplan_data.json"
