import datetime as dt

import pytest

from drawplan import gallery, planner, storage
from tests.conftest import TODAY


@pytest.fixture
def art_dir(tmp_path):
    return tmp_path / "drawplan_art"


@pytest.fixture
def image(tmp_path):
    def make(name="sketch.png", data=b"fake image bytes"):
        path = tmp_path / "src" / name
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(data)
        return path
    return make


@pytest.fixture
def manga(state):
    planner.add_goal(state, "manga", TODAY)
    return state


def days(n):
    return dt.timedelta(days=n)


# ---------- saving ----------

def test_r5_art_dir_is_next_to_data_file(tmp_path):
    assert gallery.art_dir(tmp_path / "x" / "data.json") == tmp_path / "x" / "drawplan_art"


def test_r5_save_copies_image_and_records_date_and_skill(manga, image, art_dir):
    src = image(data=b"abc")
    entry = gallery.save_art(manga, TODAY, str(src), "manga", "inking", art_dir)
    assert entry == {"date": "2026-11-20", "goal": "manga", "skill": "inking",
                     "file": "2026-11-20_manga_inking_1.png", "original": str(src)}
    assert manga["art"] == [entry]
    assert (art_dir / entry["file"]).read_bytes() == b"abc"
    assert src.exists()  # copied, not moved


def test_r5_several_pieces_same_day_get_distinct_names(manga, image, art_dir):
    a = gallery.save_art(manga, TODAY, str(image()), "manga", "inking", art_dir)
    b = gallery.save_art(manga, TODAY, str(image()), "manga", "inking", art_dir)
    assert a["file"] != b["file"]
    assert b["file"] == "2026-11-20_manga_inking_2.png"
    assert len(manga["art"]) == 2


def test_r5_spaces_in_skill_name_become_dashes(state, image, art_dir):
    planner.add_goal(state, "animation", TODAY)
    entry = gallery.save_art(state, TODAY, str(image("a.JPG")), "animation",
                             "character design", art_dir)
    assert entry["file"] == "2026-11-20_animation_character-design_1.JPG"


@pytest.mark.parametrize("ext", [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".PNG"])
def test_r5_accepts_image_extensions(manga, image, art_dir, ext):
    gallery.save_art(manga, TODAY, str(image("x" + ext)), "manga", "inking", art_dir)


def test_r5_rejects_missing_file(manga, tmp_path, art_dir):
    with pytest.raises(ValueError):
        gallery.save_art(manga, TODAY, str(tmp_path / "nope.png"), "manga", "inking", art_dir)
    assert manga["art"] == []


def test_r5_rejects_non_image_and_copies_nothing(manga, image, art_dir):
    with pytest.raises(ValueError):
        gallery.save_art(manga, TODAY, str(image("notes.txt")), "manga", "inking", art_dir)
    assert manga["art"] == []
    assert not art_dir.exists() or not any(art_dir.iterdir())


def test_r5_rejects_directory(manga, tmp_path, art_dir):
    (tmp_path / "folder.png").mkdir()
    with pytest.raises(ValueError):
        gallery.save_art(manga, TODAY, str(tmp_path / "folder.png"), "manga", "inking",
                         art_dir)


def test_r5_rejects_skill_not_in_active_goals(manga, image, art_dir):
    with pytest.raises(ValueError):
        gallery.save_art(manga, TODAY, str(image()), "comic", "lettering", art_dir)
    assert manga["art"] == []


def test_r5_art_survives_save_and_load(manga, image, art_dir, data_file):
    gallery.save_art(manga, TODAY, str(image()), "manga", "inking", art_dir)
    storage.save(manga, data_file)
    assert storage.load(data_file)["art"] == manga["art"]


def test_r5_round1_file_without_art_loads_empty(data_file):
    data_file.write_text('{"version": 1, "goals": [], "logs": [], "tasks": {}, '
                         '"task_minutes": 30}', encoding="utf-8")
    state = storage.load(data_file)
    assert state["art"] == [] and state["comparisons"] == []


# ---------- monthly comparison ----------

def save_on(state, day, image, art_dir, skill="inking"):
    return gallery.save_art(state, day, str(image()), "manga", skill, art_dir)


def test_r5_oldest_and_newest_with_ties(manga, image, art_dir):
    first = save_on(manga, TODAY, image, art_dir)
    save_on(manga, TODAY, image, art_dir)
    save_on(manga, TODAY + days(40), image, art_dir)
    last = save_on(manga, TODAY + days(40), image, art_dir)
    save_on(manga, TODAY + days(10), image, art_dir)
    assert gallery.oldest_newest(manga, "manga", "inking") == (first, last)


def test_r5_pair_needs_28_days_between_oldest_and_newest(manga, image, art_dir):
    save_on(manga, TODAY, image, art_dir)
    save_on(manga, TODAY + days(27), image, art_dir)
    assert gallery.eligible_pairs(manga) == []
    save_on(manga, TODAY + days(28), image, art_dir)
    assert gallery.eligible_pairs(manga) == [("manga", "inking")]


def test_r5_comparison_due_once_per_calendar_month(manga, image, art_dir):
    save_on(manga, TODAY - days(60), image, art_dir)
    save_on(manga, TODAY, image, art_dir)
    assert gallery.comparison_due(manga, TODAY)
    assert gallery.monthly_comparison(manga, TODAY) == ("manga", "inking")
    assert manga["comparisons"] == [{"date": "2026-11-20", "goal": "manga",
                                     "skill": "inking"}]
    assert not gallery.comparison_due(manga, dt.date(2026, 11, 30))
    assert gallery.monthly_comparison(manga, dt.date(2026, 11, 30)) is None
    assert gallery.comparison_due(manga, dt.date(2026, 12, 1))


def test_r5_no_comparison_without_eligible_pair(manga, image, art_dir):
    save_on(manga, TODAY, image, art_dir)
    assert not gallery.comparison_due(manga, TODAY)
    assert gallery.monthly_comparison(manga, TODAY) is None
    assert manga["comparisons"] == []


def test_r5_rotates_to_least_recently_compared_skill(manga, image, art_dir):
    for skill in ("inking", "paneling"):
        save_on(manga, dt.date(2026, 6, 1), image, art_dir, skill)
        save_on(manga, dt.date(2026, 8, 1), image, art_dir, skill)
    # roadmap order: paneling comes before inking for manga
    assert gallery.monthly_comparison(manga, dt.date(2026, 9, 1)) == ("manga", "paneling")
    assert gallery.monthly_comparison(manga, dt.date(2026, 10, 1)) == ("manga", "inking")
    assert gallery.monthly_comparison(manga, dt.date(2026, 11, 1)) == ("manga", "paneling")


def test_r5_comparable_pairs_need_two_pieces_any_gap(manga, image, art_dir):
    save_on(manga, TODAY, image, art_dir)
    assert gallery.comparable_pairs(manga) == []
    save_on(manga, TODAY, image, art_dir)
    assert gallery.comparable_pairs(manga) == [("manga", "inking")]


def test_r5_comparison_page_shows_old_left_new_right(manga, image, art_dir):
    old = save_on(manga, TODAY - days(30), image, art_dir)
    new = save_on(manga, TODAY, image, art_dir)
    page = gallery.write_comparison(manga, "manga", "inking", art_dir)
    assert page == art_dir / "compare.html"
    html = page.read_text(encoding="utf-8")
    assert html.index(old["file"]) < html.index(new["file"])
    assert "2026-10-21" in html and "2026-11-20" in html
    assert "inking" in html and "manga" in html


def test_r5_manual_comparison_is_not_recorded(manga, image, art_dir):
    save_on(manga, TODAY - days(30), image, art_dir)
    save_on(manga, TODAY, image, art_dir)
    gallery.write_comparison(manga, "manga", "inking", art_dir)
    assert manga["comparisons"] == []
