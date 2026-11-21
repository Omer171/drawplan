# Handoff: end of round 5

Read this with `problem.md`, `spec.md` (the source of truth for behaviour), `CLAUDE.md`
and `docs/decisions/`.

## State at handoff

- Rounds 1 (R1–R4), 2 (R5–R6), 3 (R7 and the changed R3), 4 (R8–R9) and 5 (R10) are
  implemented. `python -m pytest`: **240 passed** (201 from earlier rounds, 39 new).
- Branch `main`. Round 5 commits: `069c6a2` (the R10 text in `problem.md`, which was
  left uncommitted at the start of the round) through `0005e19` (decisions 0009 and
  0010). This handoff file itself is not committed yet.
- `2f54e4f` contains only tests and fails on its own on purpose (tests first): 33 of
  them failed until the code was added. `13dad6f` made everything except the CLI tests
  pass, and `ff91246` is the first fully green commit.
- `41bad6f` updated the README and `3faf83a` only rewraps one of its paragraphs.

## What round 5 added

- **R10: free practice** (`drawplan/planner.py`, "R10" section at the end):
  - `has_practice(state, date)` is true when any log on that ISO date has more than 0
    total minutes.
  - When `daily_task` first picks a task on a date that already has practice logged,
    it saves the task with `"free_practice": true`. This is the only stored part of
    free practice (decision 0009), because neither logs nor tasks record a time of day.
  - `_adjust_task_length` and `_recheck_completion` skip free-practice tasks, so they
    never change `task_minutes`, are never `completed` and earn no task XP, whatever is
    logged or edited later.
  - `day_status(state, day)` returns `"rest"`, `"completed"`, `"free practice"` or
    `"skipped"`, checked in that order. It is derived from the logs, tasks and
    `rest_days` every time, so R9 edits and deletes re-derive the day.
- **R10: rest days:**
  - `state["rest_days"]` is a sorted list of ISO dates, `[]` by default
    (`storage.new_state()`), so older files load unchanged. The file version is still 1.
  - `mark_rest_day(state, day, today)` accepts only dates after today, at most one per
    calendar week (Mon–Sun, using `week_start`), and raises ValueError otherwise.
    `cancel_rest_day(state, day, today)` works only for a planned date after today.
    `upcoming_rest_days(state, today)` returns the dates after today as `date` objects.
    `is_rest_day(state, day)`.
  - `daily_task` returns None on a rest day and saves nothing, so the rotation carries
    on from the last task given the day before.
- **R2 changed:** `streak` passes over rest days. A rest day without drawing neither
  breaks the streak nor adds to it; a rest day with drawing counts as a drawing day.
  Counting still starts today if today is a drawing day, otherwise yesterday.
- **R7 changed:** `week_summary` now also returns `free_practice` and `rest`, and
  `skipped` counts only days that `day_status` calls skipped. The four counts add up to
  the counted days. The text always shows all four: "Tasks: 1 completed, 0 free
  practice, 0 rest days, 6 skipped" ("rest day" is singular for 1).
- **CLI** (`drawplan/cli.py`):
  - Menu: 1–9 as before, **10 plan a rest day**, **11 quit** (`q`/`quit` still work).
    Menu 10 does not need a goal.
  - Menu 10 lists the upcoming rest days, numbered with weekday. Typing a date marks a
    rest day, typing a listed number cancels that one, and Enter goes back. An invalid
    date or a rejected one prints the message and returns to the main menu.
  - Menu 3 on a rest day says "Today is your planned rest day..." and gives no task.

## Decisions to respect

- **0001–0008** as before (derived progress, art copied into `drawplan_art/`, HTML
  comparison page, derived weekly focus, mid-week goals never neglected, rotation with a
  weekly focus, derived mastery that keeps earlier targets, focus before review).
- **0009 (new, our own default):** free practice is recorded only as `"free_practice":
  true` on a task picked after practice was logged. Everything else about the day is
  derived.
- **0010 (new, our own default):** a rest day on a focus day (Mon, Wed, Fri, Sun) just
  has no task. The focus days are not moved, so the focus skill gets one day less that
  week.
- The product owner picked the recommended answer to all 4 round 5 questions: free
  practice means practice logged before the task was asked for (or no task at all, and
  a task asked later still exists but can't be scored), rest days from tomorrow on with
  one per calendar week and cancellable until the day, rest days bridge the streak
  without adding to it, and a rest day gets no task. They are under "Round 5
  clarifications" in `spec.md`.
- Other choices made this round without the product owner (listed for them at the end
  of round 5): decisions 0009 and 0010, the order rest → completed → free practice →
  skipped (drawing on a rest day still counts as rest in the summary), "practice" meaning
  more than 0 total minutes, keeping the `free_practice` mark when its practice is
  deleted, the calendar week for "one a week" with no limit on how far ahead, no task
  ever shown on a rest day, always showing all four counts in the summary, the menu 10
  layout and numbering, and committing the user's uncommitted `problem.md` edit.

## Tests

- New: `tests/test_r10_rest_free.py` (37 functions, 39 collected tests including
  parametrized cases). It covers free practice (R4 scaling, XP, R9 edit/delete), marking
  and cancelling rest days, R3 (no task, rotation continues), R7 (four counts and the
  text), the R2 streak, and the CLI.
- Changed: `test_r7_summary_text_shows_hours_tasks_and_neglected_skill` now expects
  "1 completed, 0 free practice, 0 rest days, 6 skipped" (marked `# R10 wording`).
- CLI tests use `run_cli` from `tests/test_r7_weekly.py` and quit with `"q"`. Remember
  that a CLI run on `TODAY` with a goal added on `LAST_MONDAY` prints last week's summary
  at startup, which now contains the words "rest days". Assert on exact messages, not on
  loose words such as "rest day".
- Fixed dates as before: `TODAY` = Fri 2026-11-20, so tomorrow (Sat 11-21) and Sun 11-22
  share a week, and Mon 11-23 starts the next one. Past rest days in tests are set
  directly in `state["rest_days"]`, since `mark_rest_day` only accepts future dates.

## Known limitations and loose ends

- A `free_practice` mark stays on the task if the practice that caused it is deleted
  (R9). That task can then never be scored, and the day counts as skipped unless new
  practice is logged (decision 0009).
- A task asked for after a **0-minute** log is not free practice, and it is only
  adjusted by the next log of that day. The round 4 edge case, where scaling and a later
  recheck can use different logs, still exists for that narrow case.
- Free-practice status depends on when the task was asked for, so editing or deleting
  logs can't turn a scored task into a free-practice one or back.
- Rest days have no limit on how far ahead they can be planned, so a typo like
  2062-01-01 is accepted (it can be cancelled from menu 10).
- Days logged without a task before round 5 now count as free practice in past weekly
  summaries instead of skipped. That is intended, but older summaries now read
  differently.
- A rest day on a focus day costs the focus skill a task (decision 0010). A due review
  on a rest day simply waits for the next day.
- `has_practice`, `day_status` and the weekly summary re-scan all logs for each day.
  This is fine at one log a day, as with the earlier rounds.
- Carried over from round 4: past summaries use current targets, reviews use the
  normal exercise list, re-tagged art keeps its old file name, menu 9 lists only the 20
  most recent entries without a date, `minutes_on` duplicates part of
  `skill_progress`/`skill_xp`, startup-only checks, images checked by extension only,
  milestone XP recomputed rather than awarded once, lines over 80 columns, and Git's
  LF→CRLF warnings on Windows (no `.gitattributes`).

## How to continue

1. Add the new round's requirements to `problem.md`. Ask the product owner about anything
   unclear before writing code.
2. Update `spec.md` and commit it. Write failing tests named with requirement IDs, then
   implement in small commits. Never amend or undo commits.
3. Keep `planner.py`, `storage.py` and `gallery.py` free of `input()`/`print()`, and pass
   `today` in explicitly. Use `run_cli` and `"q"` for CLI tests.
4. Use `day_status` for anything about how a day counts, `target_minutes`/`is_mastered`
   for progress against a target, and `is_rest_day` before giving a task.
5. Add decision records as `docs/decisions/0011-...`.
