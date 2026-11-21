# 0010: A rest day on a focus day costs the focus skill that day

- Status: accepted
- Date: 2026-11-21
- Decided by: us (our own default; the product owner settled that a rest day has no task,
  but not what happens when it falls on one of the weekly focus days)

## Decision (Y-statement)

In the context of **R10 rest days, which get no task, and the weekly focus from R7/R3,
which gives the neglected skill the task on Monday, Wednesday, Friday and Sunday**,
facing **the user planning a rest day on one of those four days, so the focus skill
would get only 3 tasks that week**, we decided for **keeping the focus days fixed: the
rest day simply has no task, the focus skill gets one day less that week, and if it is
still neglected the next week's summary flags it again**, and neglected **moving the
lost focus day to the next non-focus day (keeps all 4, but the "Mon, Wed, Fri, Sun"
promise in the summary text would no longer be true, and two focus days in a row break
the spacing), and not allowing rest days on focus days (protects the focus, but the
product owner asked for a rest day the user picks, and blocking 4 of 7 days would make it
nearly useless in a focus week)**, to achieve **rest days that the user can put on any
day, a focus schedule that stays exactly as the summary describes it, and no new
interaction between the two rules (the rest-day check simply comes first in task
picking)**, accepting **that in a focus week with a rest day on Mon, Wed, Fri or Sun the
neglected skill catches up one task more slowly. Because R7 checks every week again, the
focus continues the next week if the skill is still behind.**
