# drawplan — specification (rounds 1–2)

drawplan is a command-line app for people learning to draw. They pick art goals and get a
roadmap with a progress bar for each skill and milestones to reach. Each day it gives them
one task, and after they log what they actually did it adjusts the plan.

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
  "comparisons": [{"date": "2026-11-20", "goal": "manga", "skill": "inking"}]
}
```

The logs are the source of truth. Skill progress, hours, drawing counts, XP and levels
are always computed from the logs, tasks and art and are never stored (see
docs/decisions/0001). `art` and `comparisons` were added in round 2. A round 1 file
without them loads as if they were empty lists, so the file version stays 1.

## R1 — Choose and save an art goal

- The goal catalog is: portraits, figure, anatomy, manga, comic, animation. Each catalog
  goal has a fixed list of skills, and every skill has a target of 20 hours.
- The user picks a goal from the catalog by number or by name. The pick is saved right away.
- Adding a goal that is already active is rejected. So is a name that isn't in the catalog.
- More than one goal can be active at a time. Goals stay in the order they were added.

## R2 — Game-like roadmap

For each active goal, the roadmap shows:

- One text progress bar per skill, such as `inking      [######--------------]  30%  6.0/20h`.
  A skill bar is filled by the on-goal minutes logged for that goal and skill, and stops
  at 100%.
- Milestones, each shown as reached `[x]` or not yet `[ ]`:
  - goal hours: 1, 10, 50 and 100 on-goal hours for this goal;
  - drawings: 10, 50 and 100 drawings logged for this goal;
  - one "Master <skill>" milestone for each skill (skill at 100%).

Overall (across all goals), it shows:

- The player **level** and XP from R6. (Round 1 used 1 + total study hours // 10. R6
  replaces that.)
- Overall study milestones: 10, 50, 100 and 250 total hours (total study time, every log).
- The **streak**: how many days in a row the user drew, ending today or yesterday. A day
  counts if it has a log with total minutes > 0, or a saved art piece (changed in R6).

The roadmap uses plain ASCII so it renders in any terminal.

## R3 — One task per day

- The first time the user asks for the task on a given date, drawplan picks it and saves
  it. Asking again on the same date returns the same task.
- The task's skill is the one furthest behind across all active goals, measured as minutes
  logged divided by the skill's target. A tie goes to the goal added first, then to the
  skill listed first.
- The task length is the saved `task_minutes`, which starts at 30.
- The task text names the goal, the skill, the minutes and one concrete exercise. The
  exercise is chosen from that skill's exercise list based on the date, so it changes from
  day to day.
- With no active goals, there is no task, and the user is told to add a goal.

## R4 — Log the day and adjust

The log asks for:

1. total study time today (minutes, whole number, 0 or more);
2. what they actually worked on: one of the active goal/skill pairs, or "something else";
3. on-goal minutes (0 up to the total). This is 0 automatically for "something else";
4. drawings finished (whole number, 0 or more).

Invalid values are rejected with a message, and nothing is saved.

Adjustment:

- **Credit the actual skill.** The on-goal minutes go to the goal/skill the user picked,
  even if that day's task assigned a different one.
- **Target the neglected skill.** Since progress is computed from the logs, the next day's
  task automatically goes to whatever skill is furthest behind after this log.
- **Scale the task length.** On the first log of a date that has a task, if on-goal
  minutes ≥ the task's minutes, `task_minutes` goes up by 5 (max 120) and the task is
  marked `completed`. Otherwise it goes down by 5 (min 10). Which skill they worked on
  doesn't matter for this. Later logs on the same date, and logs on dates without a task,
  do not change `task_minutes` or `completed`.

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

## Running

`python -m drawplan` opens a menu: add goal, show roadmap, today's task, log today, save
art, compare art, quit. On start it shows the monthly comparison if one is due (R5).
