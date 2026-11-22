# drawplan — specification (rounds 1–6)

drawplan is a command-line app for people learning to draw. They pick art goals and get a
roadmap with a progress bar for each skill and milestones to reach. Each day it gives them
one task, rotating through their skills, and after they log what they actually did it
adjusts the plan. Each week it sums up what they did and focuses the next week on the
skill they neglected. A skill that reaches its hour target is mastered: it leaves the
rotation and gets a short review task every two weeks. Logs and art can be edited or
deleted from the menu. Practising without asking for the task counts as free practice,
and one rest day a week can be planned ahead without breaking the streak. After each
log the user notes one thing that went well and one thing to fix; the next task for that
skill shows the open fix note, and a look-back shows which problems were fixed and which
keep coming back.

Clarifications agreed with the product owner before this spec was written:

- A user can have **several goals at once** (R1).
- R4 asks for two different times. **Total study time** is all art practice that day.
  **On-goal time** is the part of it spent on a goal's skill. Only on-goal time fills
  skill bars. Total time counts toward the overall-hours milestones.
- The daily log also asks **how many drawings were finished**, so count milestones like
  "draw 100 figures" can work.
- The R4 "adjust" step does three things: it credits the skill actually worked on, it
  points the next task at the most neglected skill, and it scales the task length.

Round 2 clarifications (agreed before this update):

- R5 art is **copied** into a `drawplan_art/` folder next to the data file, and is
  tagged with one active goal/skill pair.
- The monthly comparison fires **when the app starts**. It shows the **oldest and newest**
  piece of one skill side by side in an **HTML page opened in the browser**.
- R6 XP: **10 XP per on-goal hour**, **20 XP per completed task**, **100 XP per milestone
  reached**. Each level costs 50 XP more than the one before. The XP-based player level
  **replaces** the R2 hours-based level.
- The streak only counts days the user actually drew: a log with total minutes > 0, or a
  saved art piece.

Round 3 clarifications (agreed before this update):

- R3 changed: tasks **rotate** through every goal/skill pair in roadmap order. Each day
  takes the pair after the last task given, so a missed day never skips a skill. This
  replaces the round 1 rule "the task goes to the skill furthest behind". Pointing tasks
  at a neglected skill is now done weekly by R7.
- R7 weeks are **calendar weeks, Monday to Sunday**. The summary of the week that just
  ended is shown **once, the first time the app starts after it ends**, and a menu item
  shows it at any time. "Next week" is the week right after the summarized one.
- The **neglected** skill is the goal/skill pair with the fewest on-goal minutes that
  week, but only if that is **less than half the average** of all pairs. A balanced week
  has none. Next week it gets the task on **4 of 7 days (Mon, Wed, Fri, Sun)**, and the
  other days rotate. Each week is checked again, so the focus continues until the skill
  catches up.
- (Our own default, see docs/decisions/0005: only goals active the whole week can be
  neglected.)
- **Skipped** = every counted day of the week without a completed task, including days
  the app was not opened. Completed + skipped = the number of counted days.

Round 4 clarifications (agreed before this update):

- R8 review: a mastered skill is due for a review **14 days** after the later of the day
  it was mastered and its last task. The review **takes that day's task slot** and is
  **half the normal length** (at least 10 minutes). If several are due, the one waiting
  longest goes first.
- R8 targets are set from a **menu item, any time**, in whole hours from 1 to 1000, with
  20 as the default. Before mastery a target can go up or down. Once a skill is mastered,
  its target can only be raised, which takes it out of mastered again.
- R8 raising a mastered target **keeps the earlier mastery**: "Master inking (15h)" stays
  reached with its XP, and a new "Master inking" milestone for the new target appears.
- R7 neglect now compares each skill's minutes **as a share of its own target**.
  Mastered skills take no part.
- R9 editing or deleting a log **rechecks that day's task completion** against the day's
  first remaining log. The task length (`task_minutes`) is not rewound.
- R9 a log's four R4 answers can be edited, and an art piece's goal/skill tag. Dates and
  images stay fixed.
- R9 deleting an art piece also deletes its copy in `drawplan_art/`, never the original.
- R9 a missing image the user chooses to keep is **not remembered**: the app asks again
  at every start. Comparisons skip missing pieces meanwhile.
- (Our own defaults, see docs/decisions/0008: on a focus day the focus task wins over a
  due review, which then waits for the next non-focus day.)

Round 5 clarifications (agreed before this update):

- R10 a day is **free practice** when its first log with more than 0 total minutes came
  **before** that day's task was asked for, or the day never got a task. Asking for the
  task later that day still gives one, but the day stays free practice: that task can't
  be completed and doesn't change the task length.
- R10 a rest day can be marked for **any date from tomorrow on**, **at most one per
  calendar week** (Mon–Sun). It can be cancelled until that day arrives. Today and past
  days can never be marked or cancelled.
- R10 a rest day **bridges** the streak: it doesn't break it and doesn't add to it.
- R10 a rest day gets **no task**. The rotation continues the next day where it stopped.
  The user can still log on a rest day; the log counts for hours, XP and the streak like
  any other, but the weekly summary still lists the day as a rest day.
- (Our own defaults, see docs/decisions/0009 and 0010: free practice is remembered on the
  task as `"free_practice": true` when a task is picked after practice was logged; a rest
  day on a focus day costs the focus skill that day.)

Round 6 clarifications (agreed before this update):

- R11 the two notes (went well, want to fix) are asked after **every log that picked a
  goal/skill**, not after "something else". **Enter leaves a note blank**; both are
  optional. Editing a log (R9) does not ask them again.
- R11 "fixed or keeps coming back" is **asked at the next log of that skill**: "Last time
  you wanted to fix: X. Did you fix it?" Yes marks it fixed. No keeps it open and counts
  one "came back". The look-back lists fixed problems and open ones with their count.
- R11 the look-back is a **menu item that works any time**, plus a **reminder at startup
  once per calendar month** (like the R5 monthly comparison).
- (Our own defaults, see docs/decisions/0011 and 0012: notes are stored on the log they
  were written with; every open fix note from an earlier date is checked at the next log
  of its skill, and the task shows the newest open one.)

## Data

Everything is saved in one JSON file, `drawplan_data.json`, in the current directory. The
`DRAWPLAN_DATA` environment variable can point somewhere else. If the file is missing, the
app starts empty. If the file is unreadable, the app shows an error and does not overwrite
it. Writes go through a temp file followed by a rename, so a crash cannot leave a
half-written file.

```json
{
  "version": 1,
  "goals": [{"name": "manga", "added": "2026-11-20"}],
  "logs": [{"date": "2026-11-20", "total_minutes": 60, "goal": "manga",
            "skill": "inking", "goal_minutes": 45, "drawings": 3}],
  "tasks": {"2026-11-20": {"goal": "manga", "skill": "inking", "minutes": 30,
                           "text": "...", "adjusted": true, "completed": true}},
  "task_minutes": 35,
  "art": [{"date": "2026-11-20", "goal": "manga", "skill": "inking",
           "file": "2026-11-20_manga_inking_1.png", "original": "C:/pics/ink.png"}],
  "comparisons": [{"date": "2026-11-20", "goal": "manga", "skill": "inking"}],
  "summaries": ["2026-11-09"],
  "targets": {"manga": {"inking": 15}},
  "mastered_targets": {"manga": {"inking": [10]}},
  "rest_days": ["2026-11-24"],
  "notes_reminder": "2026-11"
}
```

The logs are the source of truth. Skill progress, hours, drawing counts, XP and levels
are always computed from the logs, tasks and art and are never stored (see
docs/decisions/0001). `art` and `comparisons` were added in round 2, and `summaries`
(the Monday of each week whose summary was shown at startup) in round 3. A file without
them loads as if they were empty lists, so the file version stays 1. The weekly focus
skill is computed from the logs and is never stored (see docs/decisions/0004).
Round 4 adds `targets` (hour targets the user changed; any skill not listed has 20 hours)
and `mastered_targets` (earlier targets of a skill that was mastered and then raised).
Both default to `{}`. A review task has `"review": true`. Whether a skill is mastered is
always computed from the logs and its target, never stored (see docs/decisions/0007).
Round 5 adds `rest_days` (planned rest days, ISO dates, sorted), default `[]`. A task
picked on a date that already had practice logged has `"free_practice": true` (R10).
Round 6 (R11) adds two text fields to a log with a goal/skill, `"went_well"` and `"fix"`
(`""` when left blank; a log without them reads as blank). Once a fix note has been
checked, its log also gets `"came_back"` (the dates the user said it was not fixed) and,
when fixed, `"fixed"` (the date they said it was). `notes_reminder` is the `YYYY-MM` of
the last monthly look-back reminder, default `null`. The file version stays 1.

## R1 — Choose and save an art goal

- The goal catalog is: portraits, figure, anatomy, manga, comic, animation. Each catalog
  goal has a fixed list of skills. Every skill starts with a target of 20 hours, which the
  user can change (R8).
- The user picks a goal from the catalog by number or by name. The pick is saved right away.
- Adding a goal that is already active is rejected. So is a name that isn't in the catalog.
- More than one goal can be active at a time. Goals stay in the order they were added.

## R2 — Game-like roadmap

For each active goal, the roadmap shows:

- One text progress bar per skill, such as `inking      [######--------------]  30%  6.0/20h`.
  A skill bar is filled by the on-goal minutes logged for that goal and skill against
  that skill's own target (R8), and stops at 100%. A mastered skill's line ends with
  `MASTERED`.
- Milestones, each shown as reached `[x]` or not yet `[ ]`:
  - goal hours: 1, 10, 50 and 100 on-goal hours for this goal;
  - drawings: 10, 50 and 100 drawings logged for this goal;
  - one "Master <skill>" milestone for each skill (skill at 100% of its current target);
  - one "Master <skill> (<N>h)" milestone for each earlier target in `mastered_targets`,
    reached when the skill's on-goal hours are at least N (R8).

Overall (across all goals), it shows:

- The player **level** and XP from R6. (Round 1 used 1 + total study hours // 10. R6
  replaces that.)
- Overall study milestones: 10, 50, 100 and 250 total hours (total study time, every log).
- The **streak**: how many days in a row the user drew, ending today or yesterday. A day
  counts if it has a log with total minutes > 0, or a saved art piece (changed in R6).
  A planned rest day (R10) on which the user did not draw is passed over: it neither
  breaks the streak nor adds to it (changed in round 5). Counting starts today if today
  is a drawing day, otherwise yesterday, as before.

The roadmap uses plain ASCII so it renders in any terminal.

## R3 — One task per day, rotating through the skills (changed in round 3)

- The first time the user asks for the task on a given date, drawplan picks it and saves
  it. Asking again on the same date returns the same task.
- **Rotation.** The pairs are every active goal/skill pair that is not mastered (R8), in
  roadmap order (goals in the order added, skills in catalog order). The task goes to the pair right after the
  **anchor**, wrapping around at the end. The anchor is the pair of the latest task saved
  for an earlier date. With no earlier task, the task goes to the first pair. A goal added
  later joins the rotation in its roadmap place.
- **Focus week (R7).** If the summary of the previous calendar week found a neglected
  pair, then on Monday, Wednesday, Friday and Sunday of this week the task goes to that
  pair. On the other days the rotation skips the focus pair: the anchor is the latest
  earlier task that was not for the focus pair, and the next pair after it that is not the
  focus pair is chosen. A focus-day task says in its text that it is this week's focus
  skill. If the focus pair is mastered by the time the task is picked, there is no focus.
- **Review (R8).** On a day that is not a focus day, if a mastered pair's review is due,
  the task is a review of it instead of the rotation task.
- The order is: focus day, then due review, then rotation. If every pair is mastered and
  no review is due, there is no task, and the user is told to raise a target or add a
  goal.
- (Round 1 rule, replaced in round 3: the task went to the skill furthest behind.)
- The task length is the saved `task_minutes`, which starts at 30. A review task is half
  of it, rounded down, and at least 10.
- The task text names the goal, the skill, the minutes and one concrete exercise. The
  exercise is chosen from that skill's exercise list based on the date, so it changes from
  day to day.
- With no active goals, there is no task, and the user is told to add a goal.
- **Rest day (R10).** On a planned rest day there is no task and nothing is saved, and
  the user is told it is a rest day. This comes before everything above. The next day's
  rotation continues from the last task given.
- **Free practice (R10).** If the date already has a log with total minutes > 0 when the
  task is first picked, the task is saved with `"free_practice": true`.
- **Fix reminder (R11).** Whenever a task is shown (rotation, focus or review), it is
  followed by the newest open fix note for its goal/skill: `Last time you wanted to fix:
  <note>`. Nothing is added when that skill has no open fix note. The reminder is not
  saved in the task.

## R4 — Log the day and adjust

The log asks for:

1. total study time today (minutes, whole number, 0 or more);
2. what they actually worked on: one of the active goal/skill pairs, or "something else";
3. on-goal minutes (0 up to the total). This is 0 automatically for "something else";
4. drawings finished (whole number, 0 or more).

Invalid values are rejected with a message, and nothing is saved.

When a goal/skill was picked, the log then asks the R11 questions (see R11): first
whether each open fix note of that skill was fixed, then the two new notes. The log, the
notes and the answers are saved together.

Adjustment:

- **Credit the actual skill.** The on-goal minutes go to the goal/skill the user picked,
  even if that day's task assigned a different one.
- **Target the neglected skill.** Changed in round 3: a single log no longer redirects the
  next day's task. The skill neglected over a week gets more task days the next week (R7,
  R3).
- **Scale the task length.** On the first log of a date that has a task, if on-goal
  minutes ≥ the task's minutes, `task_minutes` goes up by 5 (max 120) and the task is
  marked `completed`. Otherwise it goes down by 5 (min 10). Which skill they worked on
  doesn't matter for this. Later logs on the same date, and logs on dates without a task,
  do not change `task_minutes` or `completed`. Review tasks follow the same rule.
  A free-practice task (R10) is never adjusted: it never changes `task_minutes` and is
  never `completed`, whatever is logged later that day.
- `completed` always follows the **first** log of the date. Editing or deleting logs (R9)
  rechecks it: completed if the first remaining log's on-goal minutes are at least the
  task's minutes, not completed if no log remains. `task_minutes` is never rewound, and a
  task already adjusted is not adjusted again.

## R5 — Save the day's art and compare old with new

Saving a piece:

- The user enters the path to an image file and picks one of the active goal/skill pairs.
  The file must exist and have one of the extensions .png, .jpg, .jpeg, .gif, .bmp or .webp
  (any letter case). Otherwise the save is rejected with a message, and nothing is saved
  or copied.
- The image is copied into `drawplan_art/`, in the same folder as the data file. The copy
  is named `<date>_<goal>_<skill>_<n><ext>`, with spaces in names replaced by `-` and `n`
  the first number that doesn't collide with an existing file. The entry in `art`
  records the date, goal, skill, copied file name and original path.
- Several pieces can be saved on the same day.
- Pieces whose copy is missing from `drawplan_art/` (R9) are left out of every comparison:
  oldest/newest, eligibility and "Compare art".

Monthly comparison:

- A goal/skill pair is **eligible** when its newest piece is at least 28 days newer than
  its oldest one. The oldest piece is the one with the earliest date, and the first saved
  if dates tie. The newest piece has the latest date, and the last saved if dates tie.
- A comparison is **due** when no automatic comparison has been recorded in the current
  calendar month and at least one pair is eligible.
- When the app starts and a comparison is due, it picks the eligible pair compared least
  recently (never-compared first, ties in roadmap order). It writes
  `drawplan_art/compare.html` with the oldest piece on the left and the newest on the
  right, each labelled with its date, opens that page in the browser and records
  `{date, goal, skill}` in `comparisons`.
- The menu also has "Compare art", which shows the same page for any chosen pair with at
  least two pieces, whatever the gap between them. Manual comparisons are not recorded and
  do not affect the monthly one.

## R6 — XP, per-skill levels and streak

XP is computed from the logs, tasks and art, never stored:

- **Study:** 10 XP per on-goal hour. A skill's study XP is
  `(on-goal minutes for that goal/skill) * 10 // 60`. Off-goal time earns no XP.
- **Completed task:** 20 XP for each task marked `completed` (R4), given to that task's
  goal/skill.
- **Skill XP** = study XP + completed-task XP for that goal/skill.
- **Milestone bonus:** 100 XP for every milestone reached, both per-goal and overall (R2).
- **Player XP** = the sum of all skill XP + all milestone bonuses.

Levels (the same curve for skills and the player): reaching level n takes
`25 * n * (n - 1)` XP in total, so level 1 is at 0 XP, level 2 at 50, level 3 at 150 and
level 4 at 300. Each level is 50 XP more than the one before.

Roadmap additions:

- The header shows the player level, player XP and the XP needed for the next level.
- Each skill line shows `lvl N` and its XP.
- After a log, the app reports how much player XP the log earned, and any level-ups.

The streak is defined under R2.

## R7 — Weekly summary and neglected skill

A week runs Monday to Sunday. The summary of a week covers:

- **Total hours:** the total study minutes of every log dated in the week, in hours.
- **Hours per skill:** the on-goal minutes for each goal/skill pair of every goal added
  on or before the week's Sunday, in roadmap order, in hours.
- **Tasks completed vs skipped:** the counted days are the days of the week on or after
  the day the first goal was added. Each counted day is exactly one of (changed in
  round 5, R10), checked in this order:
  - **rest** if it is a planned rest day;
  - **completed** if its task was completed (the R4 rule);
  - **free practice** if it has a log with total minutes > 0 and either no task or a
    free-practice task;
  - **skipped** otherwise, including days with no task and no practice.
  Completed + free practice + rest + skipped = the number of counted days. The summary
  text shows all four. (Rounds 3–4 counted free practice and rest days as skipped.)
- **Most neglected skill:** only goals added on or before the week's Monday take part, so
  a goal added mid-week is never flagged. Mastered pairs take no part either (changed in
  round 4, R8). Here mastered means mastered by the logs dated up to the week's Sunday,
  against the current target. Each remaining pair's **share** is its on-goal minutes in
  the week divided by its target minutes. The pair with the lowest share is neglected if
  its share is less than half the average share for those pairs. A tie goes to roadmap
  order. If no pair took part, or the average is 0, or the lowest pair is not under half
  the average, nothing is neglected. (Rounds 1–3 compared raw minutes, which gives the
  same result while every target is 20 hours.)
- In "hours per skill", a pair mastered by the week's Sunday is marked `(mastered)`.
- The summary text ends by naming the neglected skill and saying that next week's tasks
  focus on it on Mon, Wed, Fri and Sun. Otherwise it says the tasks will rotate through
  all skills.

Showing it:

- The **last finished week** is the week before the current one. When the app starts, if
  that week has not been shown yet (its Monday is not in `summaries`) and the first goal
  was added on or before its Sunday, the app shows its summary and records its Monday in
  `summaries`. Only the last finished week is shown, never a backlog of older weeks.
- The menu item "Weekly summary" shows the last finished week's summary at any time.
  This is not recorded.
- The focus for a week comes only from the previous week's summary, whether or not that
  summary was ever shown.

## R8 — Mastered skills, review tasks and hour targets

Targets:

- Every active goal/skill pair has an hour target. It is 20 unless the user set another
  one in `targets`.
- Menu item "Set a skill target": pick a pair, then enter whole hours from 1 to 1000.
  - If the pair is not mastered, any value in that range is accepted, as long as it is
    above every earlier target in `mastered_targets` for that pair.
  - If the pair is mastered, the new target must be above the current one. The current
    target is appended to `mastered_targets[goal][skill]` and the new one is saved. The
    skill is then no longer mastered (unless its hours already reach the new target too).
  - Anything else is rejected with a message, and nothing is saved.

Mastery:

- A pair is **mastered** while its on-goal minutes (all logs) are at least its target
  minutes. It is computed, never stored, so a lower target or an edited log can change it.
- A mastered pair leaves the R3 rotation and is never neglected (R7).
- Its **mastery date** is the date of the log that first brought its running on-goal
  total (logs in date order) up to its current target.
- Its review is **due** 14 days after the later of its mastery date and the date of its
  latest task before today (of any kind), and stays due on every later day until a task
  is given for it.
- When reviews are due for several pairs, the one with the earliest due date goes first;
  ties go to roadmap order.
- A review task's text names the goal, skill, minutes and an exercise from the skill's
  list, and says it is a short review of a mastered skill.

XP (R6) counts the "Master <skill> (<N>h)" milestones like any other milestone, so
raising a target never takes XP away.

## R9 — Edit and delete logs and art; check for missing art

Choosing an entry (menu item "Edit or delete a log or art piece"):

- The user picks logs or art, then either presses Enter to list the 20 most recent
  entries (newest first) or types a date (YYYY-MM-DD) to list that day's entries. Each
  line shows the entry's date and what it records. The user picks one by number, then
  edits it, deletes it or goes back.

Logs:

- **Edit** asks the four R4 questions again, with the same checks. The date stays the
  same. An invalid answer is rejected with a message, and the log is unchanged. The log's
  R11 notes and their fixed/came-back answers are kept and are not asked again; they
  follow the log's new goal/skill, and are ignored while it is "something else".
- **Delete** also removes the log's R11 notes. Answers the deleted log gave about older
  fix notes stay on those notes.
- **Delete** asks for a yes/no confirmation first.
- Afterwards the day's task completion is rechecked (R4). Everything else that is
  derived (skill progress, mastery, milestones, XP, levels, streak, weekly summaries and
  the focus for tasks not yet picked) follows from the changed logs. Tasks already
  picked stay as they are.

Art:

- **Edit** changes the piece's goal/skill tag to another active pair. The date, the copy's
  file name and the original path stay the same.
- **Delete** asks for a yes/no confirmation, then removes the entry and its copy in
  `drawplan_art/` if that copy exists. The user's original file is never touched.
  Recorded monthly comparisons are kept.

Missing art check:

- When the app starts, before the weekly summary and the monthly comparison, it checks
  each art entry's copy in `drawplan_art/`. For each missing one it shows the date, the
  goal/skill and the file name, and asks whether to remove the entry.
- Yes removes the entry. No keeps it, and nothing is recorded, so the app asks again at
  the next start. A kept entry still counts as a drawing day for the streak, but is left
  out of comparisons (R5).

## R10 — Free practice and planned rest days

Free practice:

- A counted day (R7) with practice logged (a log with total minutes > 0) but no task, or
  whose task was picked only after that practice was logged, is **free practice**, not
  skipped.
- A free-practice task can't be completed, earns no task XP and never changes the task
  length (R4). Study XP, skill progress and the streak count the logs as usual.
- Editing or deleting logs (R9) re-derives the day: with no practice left it is skipped.
  The `free_practice` mark on a task stays.

Rest days (menu item "Plan a rest day"):

- The menu lists the upcoming rest days (tomorrow on). The user enters a date
  (YYYY-MM-DD) to mark it as a rest day, or picks an upcoming one to cancel it.
- A date is accepted only if it is after today and its calendar week (Mon–Sun) has no
  other rest day. Otherwise it is rejected with a message, and nothing is saved.
- Only rest days after today can be cancelled. Today's and past rest days stay.
- A rest day gets no task (R3), is counted as rest in the weekly summary (R7), and is
  passed over by the streak (R2).
- Rest days don't change the weekly focus: a focus day (Mon, Wed, Fri, Sun) that is a
  rest day gets no task, and the focus skill gets one day less that week.

## R11 — Went well / want to fix notes

Writing notes (after a log, R4):

- Only a log with a goal/skill gets notes. A "something else" log asks nothing, and
  giving it notes is rejected.
- **Check open fixes first.** A fix note is **open** while it is not blank and not
  marked fixed. The log asks about every open fix note of the same goal/skill written on
  an **earlier date**, oldest first, and not already answered on this date: `Last time
  you wanted to fix: <note>. Did you fix it? (y/n)`. Yes records the log's date as
  `fixed`. No appends the date to `came_back`, and the note stays open.
- Then it asks `One thing that went well` and `One thing you want to fix`. Surrounding
  spaces are trimmed; Enter leaves the note blank.

Monthly look-back:

- Menu item "Look back at notes" lists the active goal/skill pairs that have at least one
  note (in roadmap order) and shows the chosen pair's notes, oldest first: each log's
  date, what went well, what to fix and that fix's status (`fixed <date>`, `came back N
  time(s)` or `not checked yet`). Below the list it sums up the fix notes in three groups:
  **Fixed**, **Keeps coming back** (open, came back at least once, most times first) and
  **Not checked yet** (open, never answered). With no notes at all it says so.
- When the app starts, after the monthly comparison (R5), it reminds the user once per
  calendar month to look back at their notes, if any note is dated before the current
  month and `notes_reminder` is not the current month. Showing the reminder records the
  month in `notes_reminder`. The look-back itself is never recorded.

## Running

`python -m drawplan` opens a menu: add goal, show roadmap, today's task, log today, save
art, compare art, weekly summary, set a skill target, edit or delete a log or art piece,
plan a rest day, look back at notes, quit (`12`, or `q`). On start it checks for missing
art (R9), then shows the weekly summary (R7), the monthly comparison (R5) and the monthly
notes reminder (R11) when they are due.
