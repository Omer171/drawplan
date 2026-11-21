# drawplan

Learning to draw is a long road, and each day's progress feels too small to notice.
drawplan is a command-line planner that makes the progress visible and makes practice
feel like a game:

- **Goals:** pick one or more art goals: portraits, figure, anatomy, manga, comic,
  animation. Each one is broken into skills (manga: paneling, anatomy, penning, inking,
  expressions).
- **Roadmap:** a progress bar for every skill (20 hours each), plus milestones to check
  off (1/10/50/100 hours, 10/50/100 drawings, mastering each skill), a player level and
  a daily streak.
- **Daily task:** one concrete exercise a day, for the skill you're furthest behind on.
- **Daily log:** tell it how long you studied, what you actually worked on, how much of
  that was on your goal, and how many drawings you finished. Progress goes to what you
  really did, and tomorrow's task gets 5 minutes longer if you did the full task, or
  5 minutes shorter if you didn't.

Everything is saved in `drawplan_data.json` in the folder you run it from. Set the
`DRAWPLAN_DATA` environment variable to use a different file.

## Run

Needs Python 3.9 or newer. The app itself uses only the standard library.

```
python -m drawplan
```

## Test

```
python -m pip install -r requirements-dev.txt
python -m pytest
```

See `spec.md` for the detailed rules, and `docs/decisions/` for the design decisions.
