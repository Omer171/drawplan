# 0009: Mark a task as free practice when it is picked after practice was logged

- Status: accepted
- Date: 2026-11-21
- Decided by: us (the product owner chose the rule "practice logged before the task was
  asked for is free practice"; how to record it is our own default)

## Decision (Y-statement)

In the context of **R10, where a day counts as free practice instead of skipped when its
first log with more than 0 minutes came before that day's task was asked for, and the user
can still ask for the task later that day**, facing **the fact that this rule depends on
the order of two events, and neither logs nor tasks record a time of day. Once the task
exists, the logs and tasks alone can't tell "task, then log" from "log, then task", so
the free-practice status can't be fully derived the way 0001, 0004 and 0007 prefer**, we
decided for **recording the order once, at the only moment it is known: when
`daily_task` first picks a task and the date already has a log with more than 0 total
minutes, the task is saved with `"free_practice": true`. Such a task is never adjusted or
completed. The day's status (rest, completed, free practice, skipped) is still derived
from the logs, tasks and rest days whenever it is needed**, and neglected **adding a
timestamp to every log and task (exact order, but a data change for every entry, and old
entries would have no time), storing a list of free-practice dates (a second record that
can drift from the logs when a log is edited or deleted, as 0001 warns), and refusing to
give a task on a day with practice already logged (simpler, but the product owner chose
to still give one)**, to achieve **one small flag with no migration (old tasks have no
flag and behave as before), while editing or deleting logs still re-derives the day: with
no practice left it is skipped. It also closes the round 4 loose end where a task picked
after the first log was scaled by a later log but rechecked against the first one**,
accepting **that the flag is not undone if the practice that caused it is later deleted.
The task then stays unscorable, and that day counts as skipped unless new practice is
logged, which makes it free practice again.**
