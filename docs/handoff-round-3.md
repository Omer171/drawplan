# Handoff: end of round 3

Read this with `problem.md`, `spec.md` (the source of truth for behaviour), `CLAUDE.md`
and `docs/decisions/`.

## State at handoff

- Rounds 1 (R1–R4), 2 (R5–R6) and 3 (R7, plus the changed R3) are implemented.
  `python -m pytest`: **136 passed**.
- Branch `main`. Round 3 commits: `b6cc035` (spec) through `149a965` (decision 0006).
  This handoff file itself is not committed yet.
- Two commits contain only tests and fail on their own on purpose (tests first):
  `b320078` (R3) and `4324e01` (R7). The commit right after each one makes the suite
  pass again.

## What round 3 added

- **R3 changed, rotating task** (`drawplan/planner.py`, "R3" section):
  - The round 1 rule "the task goes to the skill furthest behind" is gone.
  - The task goes to the goal/skill pair right after the **anchor**, in roadmap order,
    wrapping around (`_next_in_rotation`). The anchor is the pair of the latest task
    saved for an earlier date, so a missed day never skips a skill. With no earlier task,
    the first pair is used. A goal added later joins the rotation in its roadmap place.
  - **Focus week:** if last week's summary found a neglected pair (`focus_pair`), that
    pair gets the task on Mon, Wed, Fri and Sun (`FOCUS_WEEKDAYS`). On the other days the
    rotation skips it: the anchor is the latest earlier task not for the focus pair. A
    focus-day task's text adds a sentence saying it is this week's focus skill.
  - R4's "target the neglected skill" bullet no longer acts after a single log. That job
    moved to R7. Credit to the skill worked on and task-length scaling are unchanged.
- **R7, weekly summary** (`drawplan/planner.py`, "R7" section):
  - Weeks are calendar weeks, Monday to Sunday (`week_start`, `last_finished_week`).
  - `week_summary(state, monday)` returns:
    - `total_minutes`: every log in the week, including off-goal time;
    - `skill_minutes`: on-goal minutes per pair, for every goal added by Sunday;
    - `completed` / `skipped`: the counted days are the days on or after the first goal
      was added. A day is completed if its task was completed (the R4 rule) and skipped
      otherwise, including days the app was not opened;
    - `neglected`: the pair with the fewest minutes, if that is less than half the
      average. Only goals added on or before Monday take part. Ties go to roadmap order.
      None if no goal took part or the average is 0.
  - `due_week_summary` returns the last finished week's summary once and records its
    Monday in `state["summaries"]`. It returns None when that week was already shown or
    no goal existed by its Sunday. Only the last finished week is shown, never a backlog.
  - `render_week_summary` builds the text.
- **CLI** (`drawplan/cli.py`):
  - Menu: 1 add goal, 2 roadmap, 3 task, 4 log, 5 save art, 6 compare art,
    **7 weekly summary**, **8 quit** (quit moved from 7 to 8).
  - On start it shows the due weekly summary first, then the monthly art comparison, and
    saves once if either was shown.
  - Menu item 7 shows the last finished week's summary any time. This is not recorded.
- **Data**: new key `summaries` (a list of Mondays as ISO dates). The file version is
  still 1. Older files load because `storage.new_state()` gives the default `[]`.

## Decisions to respect

- **0001:** progress is derived from the logs, never stored as counters.
- **0002:** art is copied into `drawplan_art/`.
- **0003:** the art comparison is an HTML page opened with `webbrowser`.
- **0004 (new):** the weekly focus is **computed** from the previous week's logs every
  time a task is picked, never stored. It applies whether or not the summary was shown.
  Only the "shown" weeks are stored, so the startup display happens once.
- **0005 (new):** goals added mid-week can't be flagged as neglected that week. Their
  hours are still listed.
- **0006 (new):** why R3 moved from weakest-skill targeting to rotation plus a weekly
  focus. The product owner's reason: variety, while still fixing neglect.
- The product owner picked the recommended answer to all four round 3 questions
  (rotation after the last task, Mon–Sun weeks shown at startup and from the menu, the
  "under half the average" rule with 4 focus days, and skipped = any counted day without
  a completed task). They are recorded under "Round 3 clarifications" in `spec.md`. The
  mid-week rule (0005) is marked there as our own default.

## Tests

- One test file per requirement: `tests/test_r<N>_*.py`. Test names start with
  `test_r<N>_`.
- New: `tests/test_r7_weekly.py` (22 tests). `tests/test_r3_daily_task.py` gained 11
  rotation/focus tests.
- **Removed** in round 3, because the changed R3 replaces the rule they checked:
  `test_r4_next_task_targets_most_neglected_skill` and
  `test_r4_neglect_is_compared_across_goals`. They were replaced by
  `test_r4_single_log_does_not_redirect_next_task`. The cross-goal case now lives in
  `test_r7_neglect_is_compared_across_goals`.
- **First automated CLI tests:** `test_r7_cli_*` drive `cli.main(today=...)` with a
  scripted `input`, a stubbed `webbrowser.open` and `DRAWPLAN_DATA` pointing at a temp
  file. Reuse the `run_cli` helper in `test_r7_weekly.py` for other menu items. Only the
  R7 menu paths are covered so far.
- The tests use fixed dates: `TODAY` = Fri 2026-11-20, so its week starts Mon 2026-11-16,
  and the week before starts Mon 2026-11-09.

## Known limitations and loose ends

- The weekly summary, like the monthly comparison, is only checked **at startup**. A
  session left open over a week boundary won't show it until the next start. The focus
  still applies, because it is computed and not tied to the display.
- A skill that is already mastered (100% of its 20 hours) still takes part in the
  rotation and can still be flagged as neglected. Neither rule looks at overall progress.
- Neglect compares raw on-goal minutes. That works only because every skill has the same
  20-hour target. If targets ever differ per skill, compare fractions of the target
  instead.
- Days the app was never opened count as skipped, by the product owner's choice. A user
  who logs practice without asking for the task still gets "skipped" for that day,
  because no task existed.
- Changing logs for a past week by editing the JSON changes that week's focus for tasks
  not yet picked. Tasks already picked are saved and don't change (see 0004).
- `daily_task` calls `focus_pair`, which re-scans the previous week's logs, and
  `week_summary` calls `task_completed` per day. This is negligible at one log a day.
- The rotation anchor looks at tasks for earlier dates only. A task saved for a future
  date (not possible from the CLI) would be ignored until that date passes.
- The "Most neglected" summary line is about 100 characters, wider than an 80-column
  terminal, like the roadmap header noted in round 2.
- Loose ends carried over from round 2 still apply: comparisons only at startup, deleted
  art files leave broken images, images are checked by extension only, milestone XP is
  recomputed rather than awarded once, and Git's LF→CRLF warnings on Windows
  (harmless, still no `.gitattributes`).

## How to continue

1. Add the new round's requirements to `problem.md`. Ask the product owner about anything
   unclear before writing code.
2. Update `spec.md` and commit it. Write failing tests named with requirement IDs, then
   implement in small commits. Never amend or undo commits.
3. Keep `planner.py`, `storage.py` and `gallery.py` free of `input()`/`print()`, and pass
   `today` in explicitly. Use the `run_cli` pattern for anything that changes the menu.
4. Add decision records as `docs/decisions/0007-...`.
