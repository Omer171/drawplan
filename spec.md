# drawplan — specification (round 1)

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
                           "text": "...", "adjusted": true}},
  "task_minutes": 35
}
```

The logs are the source of truth. Skill progress, hours and drawing counts are always
computed from the logs and are never stored (see docs/decisions/0001).

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

- A player **level**: 1 + (total study hours // 10).
- Overall study milestones: 10, 50, 100 and 250 total hours (total study time, every log).
- The **streak**: how many days in a row, ending today or yesterday, have at least one log.

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
  minutes ≥ the task's minutes, `task_minutes` goes up by 5 (max 120). Otherwise it goes
  down by 5 (min 10). Which skill they worked on doesn't matter for this. Later logs on
  the same date, and logs on dates without a task, do not change `task_minutes`.

## Running

`python -m drawplan` opens a menu: add goal, show roadmap, today's task, log today, quit.
