"""R5: save the day's art and compare an old piece with a recent one.
R9: edit and delete saved pieces, and find pieces whose copy has gone missing.

No input/print here; dates are passed in. Files are copied into an art folder next
to the data file so the history survives the originals being moved or deleted.
"""

import html
import shutil
from pathlib import Path

from drawplan import planner

ART_DIR_NAME = "drawplan_art"
IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp")
MIN_COMPARE_DAYS = 28
COMPARE_PAGE = "compare.html"


def art_dir(data_file):
    return Path(data_file).parent / ART_DIR_NAME


# ---------- saving ----------

def _slug(text):
    return text.replace(" ", "-")


def _free_name(folder, date, goal, skill, ext):
    n = 1
    while True:
        name = "{}_{}_{}_{}{}".format(date, _slug(goal), _slug(skill), n, ext)
        if not (folder / name).exists():
            return name
        n += 1


def save_art(state, today, source, goal, skill, folder):
    """Copy the image at `source` into `folder` and record it for goal/skill."""
    if (goal, skill) not in planner.work_options(state):
        raise ValueError("{} / {} is not part of your goals".format(goal, skill))
    src = Path(str(source).strip().strip('"'))
    if src.suffix.lower() not in IMAGE_EXTENSIONS:
        raise ValueError("Not an image file. Use one of: {}".format(
            ", ".join(IMAGE_EXTENSIONS)))
    if not src.is_file():
        raise ValueError("No image found at {}".format(src))
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    date = today.isoformat()
    name = _free_name(folder, date, goal, skill, src.suffix)
    shutil.copy2(str(src), str(folder / name))
    entry = {"date": date, "goal": goal, "skill": skill, "file": name,
             "original": str(source)}
    state["art"].append(entry)
    return entry


# ---------- picking pieces to compare ----------

def pieces(state, goal, skill, folder=None):
    """A pair's pieces. With `folder`, pieces whose copy is missing are left out (R9)."""
    return [a for a in state["art"] if a["goal"] == goal and a["skill"] == skill
            and (folder is None or (Path(folder) / a["file"]).is_file())]


def oldest_newest(state, goal, skill, folder=None):
    """Earliest-dated piece (first saved on ties) and latest (last saved on ties)."""
    items = pieces(state, goal, skill, folder)
    oldest = min(items, key=lambda a: a["date"])                 # min keeps the first
    newest = max(reversed(items), key=lambda a: a["date"])       # max keeps the last
    return oldest, newest


def _gap_days(state, goal, skill, folder=None):
    old, new = oldest_newest(state, goal, skill, folder)
    return (planner.parse_date(new["date"]) - planner.parse_date(old["date"])).days


def comparable_pairs(state, folder=None):
    """Pairs with at least two pieces, for a manual comparison (any gap)."""
    return [p for p in planner.work_options(state) if len(pieces(state, *p, folder)) >= 2]


def eligible_pairs(state, folder=None):
    """Pairs whose newest piece is at least 28 days newer than the oldest."""
    return [p for p in comparable_pairs(state, folder)
            if _gap_days(state, *p, folder) >= MIN_COMPARE_DAYS]


def comparison_due(state, today, folder=None):
    month = today.isoformat()[:7]
    done = any(c["date"][:7] == month for c in state["comparisons"])
    return not done and bool(eligible_pairs(state, folder))


def _last_compared(state, pair):
    dates = [c["date"] for c in state["comparisons"] if (c["goal"], c["skill"]) == pair]
    return max(dates) if dates else ""  # "" sorts before any date: never compared first


def monthly_comparison(state, today, folder=None):
    """If a comparison is due, pick and record the pair to show. Else None."""
    if not comparison_due(state, today, folder):
        return None
    pairs = eligible_pairs(state, folder)  # roadmap order; min() keeps the first tie
    goal, skill = min(pairs, key=lambda p: _last_compared(state, p))
    state["comparisons"].append({"date": today.isoformat(), "goal": goal, "skill": skill})
    return goal, skill


# ---------- the side-by-side page ----------

PAGE = """<!doctype html>
<html><head><meta charset="utf-8"><title>drawplan: {title}</title>
<style>
body {{ font-family: sans-serif; background: #f4f4f4; margin: 2em; }}
.row {{ display: flex; gap: 2em; }}
figure {{ flex: 1; margin: 0; background: #fff; padding: 1em; text-align: center; }}
img {{ max-width: 100%; max-height: 80vh; }}
</style></head>
<body>
<h1>{title}</h1>
<p>{days} days of practice between these two pieces.</p>
<div class="row">
<figure><img src="{old_src}" alt="older piece"><figcaption>Then: {old_date}</figcaption></figure>
<figure><img src="{new_src}" alt="newer piece"><figcaption>Now: {new_date}</figcaption></figure>
</div>
</body></html>
"""


def write_comparison(state, goal, skill, folder):
    """Write compare.html (oldest on the left, newest on the right) and return its path."""
    old, new = oldest_newest(state, goal, skill, folder)
    esc = html.escape
    page = Path(folder) / COMPARE_PAGE
    page.parent.mkdir(parents=True, exist_ok=True)
    page.write_text(PAGE.format(
        title=esc("{} / {}".format(goal, skill)),
        days=_gap_days(state, goal, skill, folder),
        old_src=esc(old["file"]), old_date=esc(old["date"]),
        new_src=esc(new["file"]), new_date=esc(new["date"])), encoding="utf-8")
    return page


# ---------- R9: edit, delete and check saved pieces ----------

def _art_index(state, index):
    if isinstance(index, bool) or not isinstance(index, int) \
            or not 0 <= index < len(state["art"]):
        raise ValueError("There is no art piece number {}".format(index))
    return index


def edit_art(state, index, goal, skill):
    """Change a piece's goal/skill tag. Its date and copied file stay the same."""
    entry = state["art"][_art_index(state, index)]
    if (goal, skill) not in planner.work_options(state):
        raise ValueError("{} / {} is not part of your goals".format(goal, skill))
    entry["goal"], entry["skill"] = goal, skill
    return entry


def forget_art(state, index):
    """Remove a piece's entry only (its copy is already missing)."""
    return state["art"].pop(_art_index(state, index))


def delete_art(state, index, folder):
    """Remove a piece's entry and its copy in `folder`. The original is never touched."""
    entry = forget_art(state, index)
    copy = Path(folder) / entry["file"]
    if copy.is_file():
        copy.unlink()
    return entry


def missing_art(state, folder):
    """Indexes of pieces whose copy in `folder` no longer exists."""
    return [i for i, a in enumerate(state["art"]) if not (Path(folder) / a["file"]).is_file()]
