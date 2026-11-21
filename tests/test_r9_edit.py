import datetime as dt

import pytest

from drawplan import gallery, planner, storage
from tests.conftest import TODAY
from tests.test_r7_weekly import run_cli


def days(n):
    return dt.timedelta(days=n)


@pytest.fixture
def manga(state):
    planner.add_goal(state, "manga", TODAY)
    return state


@pytest.fixture
def art_dir(data_file):
    return gallery.art_dir(data_file)


@pytest.fixture
def image(tmp_path):
    path = tmp_path / "src" / "sketch.png"
    path.parent.mkdir()
    path.write_bytes(b"fake image bytes")
    return path


# ---------- editing and deleting logs ----------

def test_r9_edit_log_replaces_the_answers_and_keeps_the_date(manga):
    planner.record_log(manga, TODAY, 90, "manga", "inking", 60, 4)
    planner.record_log(manga, TODAY + days(1), 30, None, None, 0, 0)
    planner.edit_log(manga, 0, 120, "manga", "paneling", 100, 2)
    assert manga["logs"][0] == {"date": "2026-11-20", "total_minutes": 120, "goal": "manga",
                                "skill": "paneling", "goal_minutes": 100, "drawings": 2}
    assert manga["logs"][1]["date"] == "2026-11-21"
    progress = planner.skill_progress(manga, "manga")
    assert progress["paneling"] == 100 and progress["inking"] == 0


def test_r9_edit_log_to_something_else(manga):
    planner.record_log(manga, TODAY, 90, "manga", "inking", 60, 4)
    planner.edit_log(manga, 0, 90, None, None, 0, 4)
    assert planner.goal_minutes(manga, "manga") == 0
    assert planner.total_minutes(manga) == 90


@pytest.mark.parametrize("total, goal, skill, on_goal, drawings", [
    (-1, "manga", "inking", 0, 0),
    (30, "manga", "inking", 40, 0),
    (30, "manga", "lettering", 10, 0),
    (30, None, None, 10, 0),
    (30, "manga", "inking", 10, -2),
])
def test_r9_invalid_edit_is_rejected_and_log_unchanged(manga, total, goal, skill, on_goal,
                                                        drawings):
    planner.record_log(manga, TODAY, 90, "manga", "inking", 60, 4)
    before = dict(manga["logs"][0])
    with pytest.raises(ValueError):
        planner.edit_log(manga, 0, total, goal, skill, on_goal, drawings)
    assert manga["logs"] == [before]


def test_r9_delete_log(manga):
    planner.record_log(manga, TODAY, 90, "manga", "inking", 60, 4)
    planner.record_log(manga, TODAY + days(1), 30, "manga", "paneling", 30, 1)
    planner.delete_log(manga, 0)
    assert [e["skill"] for e in manga["logs"]] == ["paneling"]
    assert planner.goal_drawings(manga, "manga") == 1


def test_r9_unknown_log_number_is_rejected(manga):
    planner.record_log(manga, TODAY, 90, "manga", "inking", 60, 4)
    for index in (1, -1):
        with pytest.raises(ValueError):
            planner.delete_log(manga, index)
        with pytest.raises(ValueError):
            planner.edit_log(manga, index, 10, None, None, 0, 0)
    assert len(manga["logs"]) == 1


def test_r9_edit_log_rechecks_task_completion_but_not_task_length(manga):
    planner.daily_task(manga, TODAY)                                   # 30 minutes
    planner.record_log(manga, TODAY, 40, "manga", "inking", 40, 0)
    assert manga["tasks"]["2026-11-20"]["completed"] and manga["task_minutes"] == 35
    planner.edit_log(manga, 0, 40, "manga", "inking", 20, 0)
    assert manga["tasks"]["2026-11-20"]["completed"] is False
    planner.edit_log(manga, 0, 40, "manga", "inking", 30, 0)
    assert manga["tasks"]["2026-11-20"]["completed"] is True
    assert manga["task_minutes"] == 35


def test_r9_completion_follows_the_first_remaining_log(manga):
    planner.daily_task(manga, TODAY)
    planner.record_log(manga, TODAY, 10, "manga", "inking", 10, 0)      # not done
    planner.record_log(manga, TODAY, 60, "manga", "inking", 60, 0)      # later log
    assert manga["tasks"]["2026-11-20"]["completed"] is False
    planner.delete_log(manga, 0)
    assert manga["tasks"]["2026-11-20"]["completed"] is True
    planner.delete_log(manga, 0)
    assert manga["tasks"]["2026-11-20"]["completed"] is False
    assert manga["task_minutes"] == 25


def test_r9_edits_change_xp(manga):
    planner.daily_task(manga, TODAY)
    planner.record_log(manga, TODAY, 60, "manga", "paneling", 60, 0)
    xp = planner.player_xp(manga)
    planner.delete_log(manga, 0)
    assert planner.player_xp(manga) < xp
    assert planner.skill_xp(manga, "manga", "paneling") == 0


def test_r9_recent_entries_newest_first_at_most_20(manga):
    for i in range(25):
        planner.record_log(manga, TODAY + days(i), 10, None, None, 0, 0)
    recent = planner.find_entries(manga["logs"])
    assert len(recent) == 20
    assert recent[0] == 24 and recent[-1] == 5


def test_r9_entries_of_one_date(manga):
    planner.record_log(manga, TODAY, 10, None, None, 0, 0)
    planner.record_log(manga, TODAY + days(1), 10, None, None, 0, 0)
    planner.record_log(manga, TODAY, 20, None, None, 0, 0)
    assert planner.find_entries(manga["logs"], TODAY) == [2, 0]
    assert planner.find_entries(manga["logs"], TODAY + days(5)) == []


# ---------- editing and deleting art ----------

def test_r9_edit_art_changes_the_skill_tag_only(manga, image, art_dir):
    entry = dict(gallery.save_art(manga, TODAY, str(image), "manga", "inking", art_dir))
    gallery.edit_art(manga, 0, "manga", "paneling")
    assert manga["art"][0] == dict(entry, skill="paneling")


def test_r9_edit_art_rejects_a_pair_not_in_the_goals(manga, image, art_dir):
    gallery.save_art(manga, TODAY, str(image), "manga", "inking", art_dir)
    with pytest.raises(ValueError):
        gallery.edit_art(manga, 0, "figure", "gesture")
    with pytest.raises(ValueError):
        gallery.edit_art(manga, 3, "manga", "paneling")
    assert manga["art"][0]["skill"] == "inking"


def test_r9_delete_art_removes_entry_and_copy_but_not_original(manga, image, art_dir):
    entry = gallery.save_art(manga, TODAY, str(image), "manga", "inking", art_dir)
    gallery.delete_art(manga, 0, art_dir)
    assert manga["art"] == []
    assert not (art_dir / entry["file"]).exists()
    assert image.exists()


def test_r9_delete_art_whose_copy_is_already_gone(manga, image, art_dir):
    entry = gallery.save_art(manga, TODAY, str(image), "manga", "inking", art_dir)
    (art_dir / entry["file"]).unlink()
    gallery.delete_art(manga, 0, art_dir)
    assert manga["art"] == []


def test_r9_missing_art_lists_entries_without_their_copy(manga, image, art_dir):
    for _ in range(3):
        gallery.save_art(manga, TODAY, str(image), "manga", "inking", art_dir)
    (art_dir / manga["art"][1]["file"]).unlink()
    assert gallery.missing_art(manga, art_dir) == [1]


# ---------- CLI ----------

def test_r9_cli_start_offers_to_remove_missing_art(monkeypatch, capsys, manga, image,
                                                   art_dir, data_file):
    gallery.save_art(manga, TODAY, str(image), "manga", "inking", art_dir)
    kept = gallery.save_art(manga, TODAY, str(image), "manga", "paneling", art_dir)
    gone = manga["art"][0]["file"]
    (art_dir / gone).unlink()
    storage.save(manga, data_file)
    out = run_cli(monkeypatch, capsys, data_file, ["y", "q"], TODAY)
    assert gone in out and "missing" in out.lower()
    assert storage.load(data_file)["art"] == [kept]


def test_r9_cli_kept_missing_art_is_asked_about_again(monkeypatch, capsys, manga, image,
                                                      art_dir, data_file):
    gallery.save_art(manga, TODAY, str(image), "manga", "inking", art_dir)
    gone = manga["art"][0]["file"]
    (art_dir / gone).unlink()
    storage.save(manga, data_file)
    run_cli(monkeypatch, capsys, data_file, ["n", "q"], TODAY)
    assert len(storage.load(data_file)["art"]) == 1
    out = run_cli(monkeypatch, capsys, data_file, ["n", "q"], TODAY)
    assert gone in out


def test_r9_cli_edits_a_log(monkeypatch, capsys, manga, data_file):
    planner.record_log(manga, TODAY, 90, "manga", "inking", 60, 4)
    storage.save(manga, data_file)
    # menu 9, logs, Enter = recent, entry 1, edit, then the four R4 answers
    answers = ["9", "1", "", "1", "1", "45", "1", "30", "2", "q"]
    run_cli(monkeypatch, capsys, data_file, answers, TODAY)
    assert storage.load(data_file)["logs"] == [
        {"date": "2026-11-20", "total_minutes": 45, "goal": "manga", "skill": "paneling",
         "goal_minutes": 30, "drawings": 2}]


def test_r9_cli_deletes_a_log_only_after_confirming(monkeypatch, capsys, manga, data_file):
    planner.record_log(manga, TODAY, 90, "manga", "inking", 60, 4)
    storage.save(manga, data_file)
    run_cli(monkeypatch, capsys, data_file, ["9", "1", "", "1", "2", "n", "q"], TODAY)
    assert len(storage.load(data_file)["logs"]) == 1
    run_cli(monkeypatch, capsys, data_file, ["9", "1", "2026-11-20", "1", "2", "y", "q"],
            TODAY)
    assert storage.load(data_file)["logs"] == []


def test_r9_cli_retags_and_deletes_art(monkeypatch, capsys, manga, image, art_dir,
                                       data_file):
    entry = gallery.save_art(manga, TODAY, str(image), "manga", "inking", art_dir)
    storage.save(manga, data_file)
    run_cli(monkeypatch, capsys, data_file, ["9", "2", "", "1", "1", "2", "q"], TODAY)
    assert storage.load(data_file)["art"][0]["skill"] == "anatomy"
    run_cli(monkeypatch, capsys, data_file, ["9", "2", "", "1", "2", "y", "q"], TODAY)
    assert storage.load(data_file)["art"] == []
    assert not (art_dir / entry["file"]).exists()


def test_r9_cli_nothing_to_edit(monkeypatch, capsys, manga, data_file):
    storage.save(manga, data_file)
    out = run_cli(monkeypatch, capsys, data_file, ["9", "1", "", "q"], TODAY)
    assert "no logs" in out.lower()
