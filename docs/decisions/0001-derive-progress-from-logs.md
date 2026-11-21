# 0001: Derive progress from the daily logs instead of storing counters

- Status: accepted
- Date: 2026-11-20

## Decision (Y-statement)

In the context of **tracking skill progress, hours, drawings and milestones for a learner
in one local JSON file**, facing **the risk that stored totals drift away from what the
user actually logged (a crash halfway through an update, a bug in one counter, or a later
change to the progress rules)**, we decided for **keeping the list of daily logs as the
only source of truth and recomputing all progress from it whenever it is needed**, and
neglected **storing running counters per skill and goal that get updated on every log**,
to achieve **numbers that always match the history, simpler adjustment logic (crediting
the actual skill and finding the most neglected one follow straight from the logs), and
freedom to change milestone or target rules later without migrating data**, accepting
**that every roadmap view re-scans all logs. That cost is negligible at one entry per day
(about 365 a year), but it would need caching if logs ever grew to many thousands.**
