# 0005: Goals added mid-week cannot be flagged as neglected that week

- Status: accepted
- Date: 2026-11-21

## Decision (Y-statement)

In the context of **R7 choosing the neglected skill as the goal/skill pair with the
fewest on-goal minutes in a week (if under half the average)**, facing **the fact that a
goal added on, say, Saturday has had at most two days of practice, so its skills almost
always have the fewest minutes and would take over the next week's focus days unfairly**,
we decided for **letting only goals added on or before the week's Monday take part in the
neglect check, while still listing the newer goal's skills under "hours per skill"**, and
neglected **including every goal active by Sunday (simple, but a new goal would almost
always be flagged at once), and scaling each pair's minutes by the number of days its
goal was active (fairer in theory, but harder to explain in the summary, and a goal
added on Sunday would still be judged on one day of data)**, to achieve **a neglect rule
that is easy to state ("skills you had all week"), that never punishes the user for
starting something new, and a summary that still shows everything they did**, accepting
**that a goal added mid-week gets no focus help until the end of its first full week, even
if the user really did ignore it. Its skills are still covered by the normal R3
rotation.**
