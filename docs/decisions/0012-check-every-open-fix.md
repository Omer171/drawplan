# 0012: Check every open fix note at the next log, and show the newest one

- Status: accepted
- Date: 2026-11-22
- Decided by: us (the product owner chose "ask at the next log for that skill; no keeps
  it open and counts one came back"; which notes are asked about is our own default)

## Decision (Y-statement)

In the context of **R11, where the task for a skill shows the user's "last fix note" and
the next log of that skill asks whether a fix note was fixed**, facing **a skill that
can have several open fix notes at once (the user answers "no" and also writes a new
one), so "the last note" and "the note to ask about" are not always the same**, we
decided for **asking at each log about every open fix note of that skill written on an
earlier date, oldest first, at most once per date, and showing with the task the newest
fix note that is still open (a note already marked fixed is not shown again)**, and
neglected **asking only about the single newest note (older open notes would stay
"open" for ever once a newer one is written, so the look-back could not tell "still a
problem" from "never asked again"), asking about notes written earlier the same day (the
user has had no chance to work on them yet), and showing the newest note even when
fixed (it would tell the user to focus on a problem they said is gone)**, to achieve
**a look-back where every open problem is either confirmed fixed or has an honest
came-back count, and a reminder that always points at something still to work on**,
accepting **that a user who keeps adding new fix notes without fixing old ones gets one
more yes/no question per open note at each log of that skill, and that the same problem
written twice in different words counts as two notes**.
