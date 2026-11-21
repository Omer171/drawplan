"""Save and load drawplan state as one local JSON file."""

import json
import os
import tempfile
from pathlib import Path

DEFAULT_FILE = "drawplan_data.json"
START_TASK_MINUTES = 30


class StorageError(Exception):
    """The data file exists but cannot be read as drawplan data."""


def new_state():
    # "art" and "comparisons" were added in round 2 (R5). They are only additions, so
    # round 1 files still load (missing keys get these defaults) and the version stays 1.
    # "summaries" (R7, round 3) lists the Mondays of weeks whose summary was shown.
    return {"version": 1, "goals": [], "logs": [], "tasks": {},
            "task_minutes": START_TASK_MINUTES, "art": [], "comparisons": [],
            "summaries": []}


def data_path():
    return Path(os.environ.get("DRAWPLAN_DATA", DEFAULT_FILE))


def load(path):
    path = Path(path)
    if not path.exists():
        return new_state()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise StorageError("Cannot read {}: {}".format(path, exc)) from exc
    if not isinstance(data, dict) or data.get("version") != 1:
        raise StorageError("{} is not a drawplan v1 data file".format(path))
    state = new_state()
    state.update(data)
    return state


def save(state, path):
    """Write atomically: temp file in the same folder, then rename over the target."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".drawplan-", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        os.replace(tmp, str(path))
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise
