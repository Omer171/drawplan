# Handoff: end of round 2

Read this with `problem.md`, `spec.md` (the source of truth for behaviour), `CLAUDE.md`
and `docs/decisions/`.

## State at handoff

- Rounds 1 (R1–R4) and 2 (R5–R6) are implemented. `python -m pytest`: **104 passed**.
- Working tree clean on `main`. Round 2 commits: `648f653` (spec) through `7242fe6`
  (decision records).
- No handoff file existed from round 1. This is the first one.

## What round 2 added

- **R5, art history** (`drawplan/gallery.py`, new):
  - `save_art` checks the image (it must exist, have an image extension and belong to an
    active goal/skill pair). It then copies it to `drawplan_art/` next to the data file
    and appends to `state["art"]`.
  - `monthly_comparison` picks and records one eligible pair per calendar month. A pair is
    eligible when its oldest and newest pieces are at least 28 days apart. It rotates to
    the pair compared least recently.
  - `write_comparison` writes `drawplan_art/compare.html` with the oldest piece on the
    left and the newest on the right.
- **R6, XP** (`drawplan/planner.py`, "R6" section):
  - XP sources: 10 XP per on-goal hour, 20 XP per completed task (given to the task's
    skill), and 100 XP per milestone reached.
  - Levels: reaching level n takes `25*n*(n-1)` XP (0, 50, 150, 300, ...). The same curve
    is used for each goal/skill and for the player.
  - The XP-based player level **replaced** the round 1 rule (`1 + hours // 10`).
  - The streak now counts only days with a log of more than 0 minutes, or a saved art
    piece.
- **CLI** (`drawplan/cli.py`):
  - Menu: 1 add goal, 2 roadmap, 3 task, 4 log, 5 save art, 6 compare art, 7 quit.
  - On start it shows the monthly comparison if one is due.
  - After each log it reports the XP earned and any level-ups.
- **Data**: new keys `art` and `comparisons`, and `completed` on tasks. The file version
  is still 1. Older files load because missing keys get defaults in `storage.new_state()`.

## Decisions to respect

- **0001:** progress is derived from the logs, never stored as counters. Round 2 follows
  this: XP and levels are recomputed from logs, tasks and art every time.
- **0002:** art is copied into `drawplan_art/`, not linked by its original path.
- **0003:** the comparison is an HTML page opened with `webbrowser`, because the app is
  standard library only.
- The product owner accepted every proposed default for round 2. They are recorded under
  "Round 2 clarifications" in `spec.md`.

## Tests

- One test file per requirement: `tests/test_r<N>_*.py`. Test names start with
  `test_r<N>_`.
- In round 2, `test_r2_level_goes_up_every_ten_hours` was removed because R6 replaced the
  rule. `test_r2_roadmap_marks_reached_milestones` now expects `Level 2`.
- **`cli.py` has no automated tests.** It was checked once by hand, with a scripted
  `input()` and a stubbed `webbrowser.open`. A next round that touches the menu should
  consider adding CLI tests the same way.

## Known limitations and loose ends

- The monthly comparison is only checked **at startup**. A session left open across a
  month boundary won't trigger one until the next start.
- If a copied image in `drawplan_art/` is deleted by hand, its `art` entry remains and
  the comparison page shows a broken image. There is no command to delete or edit art.
- Image files are checked by extension only. The file contents aren't checked.
- The image is copied before the data file is saved. A crash between the two leaves an
  orphan file in `drawplan_art/`, which does no harm.
- Milestone bonuses are recomputed from current progress, not awarded once. Changing the
  milestone rules would change past XP.
- A log with drawings but 0 total minutes does not count for the streak, by design.
- `skill_xp` rescans the logs for every pre-round-2 task that has no `completed` flag.
  This is fine at one log a day; cache it if the data gets large.
- The roadmap header line is about 90 characters, wider than an 80-column terminal.
- Git warns about LF→CRLF on Windows checkouts. This is harmless; no `.gitattributes`
  has been added.

## How to continue

1. Add the new round's requirements to `problem.md`. Ask the product owner about anything
   unclear before writing code.
2. Update `spec.md` and commit it. Write failing tests named with requirement IDs, then
   implement in small commits. Never amend or undo commits.
3. Keep `planner.py`, `storage.py` and `gallery.py` free of `input()`/`print()`, and pass
   `today` in explicitly.
4. Add decision records as `docs/decisions/0004-...`.
