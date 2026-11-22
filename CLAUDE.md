# CLAUDE.md

- Python 3.9. The app uses the standard library only. pytest is the one dev dependency
  and is used for tests only.
- Run: `python -m drawplan`. Data is saved in `drawplan_data.json` in the current
  directory (override with `DRAWPLAN_DATA`).
- Test: `python -m pytest`.
- `spec.md` is the source of truth for behaviour. Every test name includes its
  requirement ID (`test_r1_...`).
- Keep the logic (`drawplan/planner.py`, `drawplan/storage.py`) free of `input()`/`print()`.
  Only `drawplan/cli.py` talks to the user. Pass `today` explicitly so tests control dates.
- Commit in small steps. Never amend or undo commits.
- The product owner writes, commits and pushes each round's requirements in `problem.md`
  before the session starts. Never write, edit or commit requirements yourself; if
  `problem.md` has uncommitted changes, ask first.
- Never commit a handoff file or changes to `CLAUDE.md`. The product owner reads and
  edits them first, then commits.
