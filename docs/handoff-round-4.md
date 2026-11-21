# Handoff: end of round 4

Read this with `problem.md`, `spec.md` (the source of truth for behaviour), `CLAUDE.md`
and `docs/decisions/`.

## State at handoff

- Rounds 1 (R1–R4), 2 (R5–R6), 3 (R7 and the changed R3) and 4 (R8–R9) are
  implemented. `python -m pytest`: **201 passed** (136 from earlier rounds, 65 new).
- Branch `main`. Round 4 commits: `26ed29e` (spec) through `293ec9a` (decisions 0007
  and 0008). This handoff file itself is not committed yet.
- `2bda444` contains only tests and fails on its own on purpose (tests first). The
  commits after it make the suite pass again (`cc172f4` is the first fully green one).
- `0a6088d` holds both the R8 planner logic and the R9 log edit/delete functions,
  because both went into `planner.py` before either was committed.
- pytest was not installed in this machine's Python 3.9 at the start of round 4.
  `python -m pip install -r requirements-dev.txt` fixed it.

## What round 4 added

- **R8: targets, mastery and reviews** (`drawplan/planner.py`, "R8" section at the end):
  - Every pair has an hour target: `target_hours` / `target_minutes`, 20 by default
    (`DEFAULT_TARGET_HOURS`). `state["targets"]` stores only targets the user changed,
    as `{goal: {skill: hours}}`. `SKILL_TARGET_MINUTES` still exists, but only as the
    default value. Use `target_minutes` instead.
  - `set_target` accepts whole hours from 1 to 1000. Before mastery a target can go up
    or down. A mastered skill can only be raised, and its old target is appended to
    `state["mastered_targets"][goal][skill]`. A new target must also be above every
    earlier mastered target.
  - `is_mastered(state, goal, skill, until=None)` means on-goal minutes ≥ target. It is
    **computed, never stored** (decision 0007). `minutes_on` gives a pair's minutes,
    optionally only from logs dated up to `until`. `all_mastered` is true when every
    active pair is mastered.
  - Milestones: "Master <skill>" for the current target, plus "Master <skill> (<N>h)"
    for each earlier target, checked when hours ≥ N. That way XP doesn't drop when a
    target is raised.
  - The rotation (`_next_in_rotation`) only uses pairs that aren't mastered. It returns
    None when every pair is mastered.
  - Reviews: `mastery_date` is the date of the log that first reached the current target.
    `review_due_date` is 14 days (`REVIEW_EVERY_DAYS`) after the later of the mastery
    date and the pair's last task before today. `due_reviews` lists the due pairs,
    earliest due date first, ties in roadmap order.
  - `_pick_skill` now returns `(pair, kind)` with kind "focus", "review" or "rotation",
    in that order of priority (decision 0008). A focus pair that is mastered by now is
    ignored.
  - A review task is `max(10, task_minutes // 2)` minutes long, has `"review": true`,
    and its text says it is a review of a mastered skill. With every pair mastered and
    no review due, `daily_task` returns None and saves nothing.
  - The roadmap uses each skill's own target and appends `MASTERED` to mastered lines.
- **R7 changed:** neglect compares each pair's **share of its target** (minutes ÷ target
  minutes). Pairs mastered by the week's Sunday (`until=sunday`) take no part.
  `week_summary` also returns `mastered`, and the summary text marks those pairs
  `(mastered)`.
- **R4 changed / bug fix:** scaling now steps `state["task_minutes"]` instead of the
  task's own minutes. Before, a completed 15-minute review would have set the next task
  to 20 minutes. `_recheck_completion(state, date)` sets an adjusted task's `completed`
  from the **first remaining log** of its date. It runs after `edit_log`/`delete_log`
  and on every later log for an already adjusted date. `task_minutes` is never rewound.
- **R9: logs** (`planner.py`, next to `record_log`): `edit_log(state, index, ...)` uses
  the same checks as `record_log` and keeps the date. `delete_log(state, index)`.
  Invalid indexes raise ValueError. `find_entries(entries, date=None, limit=20)` returns
  indexes newest first and works for both logs and art.
- **R9: art** (`drawplan/gallery.py`, "R9" section): `edit_art` (re-tags the goal/skill
  only; file name and date stay), `delete_art` (removes the entry and its copy, never
  the original), `forget_art` (removes the entry only), `missing_art(state, folder)`.
- **R5 changed:** `pieces`, `oldest_newest`, `comparable_pairs`, `eligible_pairs`,
  `comparison_due`, `monthly_comparison` and `write_comparison` take an optional
  `folder`. When it is given, pieces whose copy is missing are left out. The CLI always
  passes it. Without it, the old behaviour stays, so the round 2 tests are unchanged.
- **CLI** (`drawplan/cli.py`):
  - Menu: 1–7 as before, **8 set a skill target**, **9 edit or delete a log or art
    piece**, **10 quit** (`q`/`quit` still work). 4, 5 and 8 need a goal.
  - Menu 9: choose log or art, then Enter for the 20 most recent or type a date, pick
    by number, then Edit / Delete (y/n) / Back. Editing a log re-asks the four R4
    questions through `ask_log_answers`, shared with "Log today".
  - Startup order: missing-art check (y/n per missing entry; "no" is not remembered),
    then the weekly summary, then the monthly comparison. It saves once if any of them
    changed state.
  - Menu 3 explains when every skill is mastered and no review is due.
- **Data:** new keys `targets` and `mastered_targets` (both default `{}` in
  `storage.new_state()`), plus `"review": true` on review tasks. The file version is
  still 1, and older files load unchanged.

## Decisions to respect

- **0001–0006** as before: progress is derived from logs, art is copied into
  `drawplan_art/`, the comparison is an HTML page, the weekly focus is computed, goals
  added mid-week are never neglected, and tasks rotate with a weekly focus.
- **0007 (new):** mastery is computed from the logs and the current target. Only user
  choices are stored (`targets`, `mastered_targets`). Earlier masteries are milestones
  checked against today's hours.
- **0008 (new, our own default):** on a focus day the focus task beats a due review. The
  review waits for the next non-focus day.
- The product owner picked the recommended answer to all 8 round 4 questions: a 14-day
  review that takes the slot at half length, a menu item for targets (1–1000h, raise
  only once mastered), keeping the old mastery milestone when raising, neglect by share
  of target, rechecking completion without rewinding the length, editable fields (log
  answers and the art tag, no dates), deleting the art copy too, and asking again about
  missing art at every start. They are under "Round 4 clarifications" in `spec.md`.
- Other choices made this round without the product owner (listed for them at the end
  of round 4): no task when all skills are mastered, the "(Nh)" milestone label, no
  target at or below an earlier mastered one, mastery "as of Sunday" in the weekly
  summary, review tasks earning XP and scaling the length like any task, the menu
  numbering and sub-menu, the 20-most-recent / by-date list, keeping the file name when
  art is re-tagged, and missing-art check before the other startup items.

## Tests

- New: `tests/test_r8_mastery.py` (28 functions) and `tests/test_r9_edit.py` (21
  functions), 59 collected tests including parametrized cases.
- Added to earlier files for the changed rules: one `test_r4_` (new first log after a
  delete), one `test_r5_` (missing copies left out), four `test_r7_` (share of target,
  mastered excluded, mastered-after-the-week case).
- Changed: `test_r7_cli_menu_item_shows_last_week_summary` now quits with `"q"` instead
  of `"8"`. Use `"q"` in CLI tests so menu renumbering doesn't break them.
- CLI tests reuse `run_cli` from `tests/test_r7_weekly.py`. `master(state, day, skill)`
  in `test_r8_mastery.py` is a quick way to master a skill (target 1h plus a 60-minute
  log).
- Fixed dates as before: `TODAY` = Fri 2026-11-20. Weeks before a goal was added on
  Monday don't take part in neglect, which keeps most R8 dates free of focus effects.

## Known limitations and loose ends

- **Log made before the task was asked for:** the first log of a date can come before
  that day's task existed. Scaling and the first `completed` value use the log that
  triggered the adjustment, but any later edit, delete or recheck uses the date's first
  log. In that rare case the two can disagree.
- Deleting logs can make an earlier "Master <skill> (<N>h)" milestone unchecked again
  (by design, see 0007), and can make a mastered skill not mastered, which puts it back
  in the rotation.
- The R7 summary for a past week uses **current** targets. Changing a target later
  changes that week's neglected skill, and so the focus for tasks not yet picked
  (tasks already picked stay, as in 0004).
- A review task always uses the exercise list of the skill, not a dedicated "review"
  list.
- Re-tagged art keeps a file name with the old skill in it.
- Menu 9 only lists the 20 most recent entries without a date. Older entries need the
  exact date.
- Several functions re-scan all logs (`is_mastered` per pair per task pick, per weekly
  summary, per roadmap line). This is fine at one log a day, but would need caching
  for many thousands.
- `planner.minutes_on` duplicates part of `skill_progress`/`skill_xp`. That could be
  tidied up.
- Carried over: the weekly summary and monthly comparison are only checked at startup,
  images are checked by extension only, milestone XP is recomputed rather than awarded
  once, wide summary/roadmap lines are over 80 columns, and Git's LF→CRLF warnings on
  Windows (no `.gitattributes`).

## How to continue

1. Add the new round's requirements to `problem.md`. Ask the product owner about anything
   unclear before writing code.
2. Update `spec.md` and commit it. Write failing tests named with requirement IDs, then
   implement in small commits. Never amend or undo commits.
3. Keep `planner.py`, `storage.py` and `gallery.py` free of `input()`/`print()`, and pass
   `today` in explicitly. Use `run_cli` and `"q"` for CLI tests.
4. Use `target_minutes`/`is_mastered` for anything about progress against a target.
   Don't use `SKILL_TARGET_MINUTES`.
5. Add decision records as `docs/decisions/0009-...`.
