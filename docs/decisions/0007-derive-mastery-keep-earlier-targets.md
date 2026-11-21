# 0007: Derive mastery from the logs, and keep only the earlier targets of raised skills

- Status: accepted
- Date: 2026-11-21

## Decision (Y-statement)

In the context of **R8, where a skill counts as mastered at 100% of its own hour
target, leaves the rotation, gets a review every 14 days, and can have its target
raised afterwards while the earlier mastery stays as a reached milestone with its
XP (the product owner's choice)**, facing **the fact that mastery can now change in
both directions: logs can be edited or deleted (R9) and a target can be lowered before
mastery or raised after it. A stored "mastered" flag would have to be updated
correctly on every one of those paths, and would drift from the logs when one is
missed**, we decided for **computing mastery every time as "on-goal minutes ≥ current
target" (and the mastery date as the log that first reached it), and storing only two
plain user choices: `targets` (hour targets the user changed) and `mastered_targets`
(the target a skill had when the user raised it after mastering it). Each earlier
target becomes a "Master <skill> (<N>h)" milestone that is checked when the skill's
hours reach N, like any other milestone**, and neglected **storing a `mastered`
record per skill with its date when a log crosses the target (exact history, but it
gets out of date when a log is edited or deleted, the same drift as in 0001), and
having a single "Master <skill>" milestone tied to the current target (simplest, but
raising a target would uncheck it and take 100 XP away, which the product owner
rejected)**, to achieve **mastery, the review schedule, milestones and XP that always
agree with the logs after any edit, while XP never drops when a target is raised, and
no migration for old files (both keys default to `{}`)**, accepting **that deleting
logs can uncheck an earlier "Master (Nh)" milestone, because it is checked against
today's hours, not frozen. A target can't be set back to or below an earlier mastered
target, to avoid two milestones for the same hours. Mastery is re-scanned from the
logs whenever a task is picked or the roadmap is drawn, which is negligible at one log
a day.**
