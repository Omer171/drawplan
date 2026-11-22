# 0011: Store R11 notes on the log they were written with

- Status: accepted
- Date: 2026-11-22
- Decided by: us (the product owner chose when the notes are asked and how a fix is
  confirmed; where to store them is our own default)

## Decision (Y-statement)

In the context of **R11, where after each log with a goal/skill the user writes one
thing that went well and one thing to fix, "saved with the skill they worked on", and a
later log answers whether each open fix was fixed**, facing **the need to keep each note
tied to its skill and date, keep it in step with R9 edits and deletes, and record
fixed/came-back answers that arrive on later days**, we decided for **storing the notes
as `went_well` and `fix` fields on the log itself (left out when blank), and recording
the answers on the note's own log as `fixed` (a date) and `came_back` (a list of
dates). The log's goal/skill is the note's skill, so a log edited to another skill takes
its notes along, a "something else" log's notes are ignored, and deleting a log deletes
its notes**, and neglected **a separate `notes` list with its own date and goal/skill
(notes could outlive or contradict the log they came from, which 0001 warns against, and
R9 would need a second edit/delete path), and recording each answer on the later log
that gave it, pointing back to the note (logs have no ids, so a pointer would be a list
index that a delete shifts)**, to achieve **no new top-level list, no ids, old logs that
load unchanged (no notes means no fields), and every R11 view (the fix reminder, the
checks, the look-back) derived from the logs like the rest of the app**, accepting
**that answers stay on a note when the later log that gave them is deleted, that a log's
notes can't be edited from menu 9 yet, and that editing a log to "something else" hides
its notes until it gets a skill again**.
