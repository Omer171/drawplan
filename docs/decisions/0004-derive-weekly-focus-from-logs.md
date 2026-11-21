# 0004: Derive the weekly focus skill from last week's logs instead of storing it

- Status: accepted
- Date: 2026-11-21

## Decision (Y-statement)

In the context of **R7 finding the most neglected skill each week and the changed R3
giving that skill 4 of the next week's 7 tasks**, facing **the choice of when the focus
gets decided: when the summary is shown (but the user may not open the app for days, or
at all, after a week ends), or from data that is already there**, we decided for
**computing the focus for any date as `week_summary(previous calendar week)["neglected"]`,
recomputed from the logs and tasks whenever a task is picked, and storing only which
weeks' summaries were shown (`summaries`, so the startup display happens once)**, and
neglected **storing a `focus` record (`{week, goal, skill}`) at the moment the startup
summary is shown (the focus would depend on whether and when the app was opened, and a
week whose summary was never shown would get no focus), and storing running weekly
counters per skill (they drift from the logs, as 0001 explains)**, to achieve **a focus
that follows only from what the user logged, the same whether or not they saw the
summary, and that stays consistent with decision 0001, while the summary page and task
picking can never disagree about which skill is neglected**, accepting **that a log
added or changed later for a past week (not possible in the app today, but possible by
editing the JSON file) changes that week's focus for any task not yet picked. Tasks
already picked are saved, so past days never change. Task picking also re-scans the
previous week's logs, which is negligible at one log a day.**
