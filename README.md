# drawplan

Learning to draw is a long road, and each day's progress feels too small to notice.
drawplan is a command-line planner that makes the progress visible and makes practice
feel like a game:

- **Goals:** pick one or more art goals: portraits, figure, anatomy, manga, comic,
  animation. Each one is broken into skills (manga: paneling, anatomy, penning, inking,
  expressions).
- **Roadmap:** a progress bar for every skill (20 hours each unless you set your own
  target, such as anatomy 50 hours, inking 15 hours), plus milestones to check off
  (1/10/50/100 hours, 10/50/100 drawings, mastering each skill), and a streak of days
  in a row you drew.
- **Mastered skills:** a skill that reaches its target is mastered. It leaves the daily
  rotation, and every two weeks you get a short review task for it so you don't lose
  it. Raise its target from menu item 8 to keep going. Your old mastery stays on the
  roadmap.
- **XP and levels:** earn 10 XP per hour on your goal, 20 XP per completed daily task
  and 100 XP per milestone. Every skill levels up on its own (anatomy lvl 4, paneling
  lvl 2), and so does your player level.
- **Daily task:** one concrete exercise a day, rotating through every skill of your
  goals in turn, so none gets left out (a day you skip doesn't skip a skill).
- **Weekly summary:** when a week (Monday to Sunday) ends, the next time you start the
  app it shows your total hours, hours per skill and tasks completed vs skipped. If one
  skill got less than half the average time, next week's task is that skill on Monday,
  Wednesday, Friday and Sunday, until it catches up. Time is compared against each
  skill's own target, and mastered skills are never flagged. Menu item 7 shows the
  summary any time.
- **Daily log:** tell it how long you studied, what you actually worked on, how much of
  that was on your goal, and how many drawings you finished. Progress goes to what you
  really did, and tomorrow's task gets 5 minutes longer if you did the full task, or
  5 minutes shorter if you didn't.
- **Art history:** save the image you made today for a skill. drawplan keeps a copy in
  `drawplan_art/` next to the data file. Once a month, when you start the app, it opens
  your oldest piece next to your newest for one skill in the browser, so you can see how
  far you've come. You can also compare any time from the menu.
- **Fix mistakes:** menu item 9 edits or deletes a log or a saved art piece, so you
  never have to touch the JSON file. On start, drawplan checks that every saved image
  is still in `drawplan_art/` and asks whether to remove entries whose image is gone.

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
