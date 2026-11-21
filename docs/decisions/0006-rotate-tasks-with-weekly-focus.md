# 0006: Rotate the daily task through all skills, with a weekly focus from R7

- Status: accepted
- Date: 2026-11-21
- Decided by: the product owner (round 3 change to R3)

## Decision (Y-statement)

In the context of **R3 choosing which skill each day's task is for, across every skill of
the user's active goals**, facing **the problem that the round 1 rule ("always target
the skill furthest behind") gave the same skill day after day: when the furthest-behind
skill is only slightly ahead of the next one, it stays the lowest until it catches up,
so the daily task felt repetitive and not like a game, and the other skills went
untouched**, we decided for **rotating the task through every goal/skill pair in roadmap
order (continuing after the last task given, so a missed day skips nothing), and once a
week letting R7's summary pick the skill that got less than half the average time,
which then gets Monday, Wednesday, Friday and Sunday of the next week until it catches
up**, and neglected **keeping weakest-skill targeting (it fixes imbalance fastest, but
it is the repetitive behaviour this change is meant to remove, and one day's numbers
decide too much), and pure rotation with no focus (the most variety and the simplest
rule, but a skill the user keeps avoiding in their own practice would never get extra
attention, since rotation ignores what was actually logged)**, to achieve **variety:
every skill keeps moving and the user sees a different skill most days, while real
neglect is still fixed, now measured over a whole week of actual practice instead of a
single log**, accepting **that a weak skill is pulled up more slowly than before: at most
4 days a week, and only from the week after it was neglected. It also means the R4
"target the neglected skill" step no longer acts after a single log. That role moved to
R7 (see spec.md, R3 and R4). The weekly focus itself is derived from the logs, as
decision 0004 explains.**
