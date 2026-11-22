# Handoff: end of round 6

Read this with `problem.md`, `spec.md` (the source of truth for behaviour), `CLAUDE.md`
and `docs/decisions/`.

Note: this handoff was written from the repository (commits, spec, tests and decision
records) by a different session from the one that did round 6. If anything here
disagrees with `spec.md`, trust `spec.md`.

## State at handoff

- Rounds 1 (R1–R4), 2 (R5–R6), 3 (R7 and the changed R3), 4 (R8–R9), 5 (R10) and
  6 (R11) are implemented. `python -m pytest`: **267 passed** (240 from earlier rounds,
  27 new tests in `tests/test_r11_notes.py`).
- Branch `main`, pushed. Round 6 commits: `4660ee1` (the R11 text in `problem.md`,
  pushed before any other round 6 change) through `16728a3` (decisions 0011 and 0012).
- `db839b1` contains only tests and fails on its own on purpose (tests first).
  `e6a3122` adds one late rule (blank notes are not stored) with its spec line and test.

## How to run and test

- Setup once: `python -m venv .venv`, `source .venv/Scripts/activate`,
  `python -m pip install -r requirements-dev.txt`.
- Run: `python -m drawplan`. Data goes to `drawplan_data.json` in the current directory
  (override with `DRAWPLAN_DATA`). Art copies go to `drawplan_art/` (git-ignored).
- Test: `python -m pytest`.

## What round 6 added

- **R11 notes** (`drawplan/planner.py`, R11 section at the end; `drawplan/cli.py`):
  - After every log with a goal/skill (not "something else"), the CLI (`ask_notes`)
    asks "One thing that went well" and "One thing you want to fix". Enter leaves a note
    blank. Blank notes are not stored. Editing a log (R9) does not ask again.
  - Notes are stored on the log itself as `went_well` and `fix` (decision 0011).
    Answers are stored on the note's own log: `fixed` (a date) and `came_back` (a list
    of dates).
  - Before the new notes, the log asks about every open fix note of that goal/skill from
    an earlier date, oldest first (`fixes_to_check`, decision 0012). Yes marks it fixed;
    no adds to `came_back`, and the note stays open.
  - Whenever a task is shown, it shows the newest still-open fix note for that skill
    (`open_fix`).
  - **Menu 11, "Look back at notes"** (`look_back`, `render_notes`, `note_groups`):
    pick a goal/skill, see its notes oldest first, then the fixes grouped as Fixed,
    Keeps coming back, and Not checked yet.
  - A startup reminder once per calendar month (`due_notes_reminder`,
    `notes_reminder`), shown after the R5 monthly comparison. The month is stored in
    `state["notes_reminder"]`.
- **Menu change:** Quit moved from 11 to **12** (`q`/`quit` still work). An R10 CLI
  test was updated for this; it now quits with `"q"` (see
  `test_r11_cli_quit_is_now_12`).
- Old data files load unchanged: a log with no notes has no note fields.

## Decisions made in round 6

- **Product owner's answers** (under "Round 6 clarifications" in `spec.md`): notes are
  asked after every goal/skill log and both are optional; "fixed or keeps coming back"
  is asked at the next log of that skill; the look-back is a menu item plus a monthly
  startup reminder.
- **0011 (our default):** store notes on the log, not in a separate list, so R9
  edits and deletes keep them in step and everything stays derived from logs (as 0001).
- **0012 (our default):** check every open fix note from an earlier date at the next log
  of its skill, and show the newest open one with the task, so the look-back can tell
  "still a problem" from "never asked again".

## Unresolved / known limitations

- A log's notes can't be edited from menu 9 yet (decision 0011).
- Answers stay on a note when the later log that gave them is deleted.
- Editing a log to "something else" hides its notes until it gets a skill again.
- A user who keeps adding fix notes without fixing old ones gets one yes/no question per
  open note at each log of that skill. The same problem written twice counts as two notes.
- Carried over from round 5: a `free_practice` mark stays if its practice is deleted;
  rest days have no limit on how far ahead; past summaries use current targets; menu 9
  lists only the 20 most recent entries; lines over 80 columns; Git LF→CRLF warnings on
  Windows.

## Warnings for the next session

- Do **not** write or commit requirements in `problem.md`. The product owner writes,
  commits and pushes each round's requirements before the session starts (see
  `CLAUDE.md`). In round 5 a session committed them itself; don't repeat that.
- Do not commit the handoff file or `CLAUDE.md` at the end of a round.
- CLI tests use `run_cli` from `tests/test_r7_weekly.py` and quit with `"q"`. Prefer
  `"q"` over a menu number, because menu numbers shift when items are added (as Quit
  did this round).
- Fixed test dates: `TODAY` = Fri 2026-11-20. Startup output can include the weekly
  summary, monthly comparison and notes reminder, so assert on exact messages.
- New decision records start at `docs/decisions/0013-...`.
