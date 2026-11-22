"""Interactive menu. The only module that reads input or prints."""

import datetime as dt
import sys
import webbrowser

from drawplan import gallery, planner, storage

MENU = """
drawplan
  1) Add a goal
  2) Show roadmap
  3) Today's task
  4) Log today
  5) Save today's art
  6) Compare old and new art
  7) Weekly summary
  8) Set a skill target
  9) Edit or delete a log or art piece
 10) Plan a rest day
 11) Look back at notes
 12) Quit"""

QUIT = ("12", "q", "quit")
NEEDS_GOALS = ("4", "5", "8")


def ask_int(prompt, lo=0, hi=None):
    while True:
        raw = input(prompt).strip()
        if raw.isdigit() and int(raw) >= lo and (hi is None or int(raw) <= hi):
            return int(raw)
        print("Please enter a whole number{}.".format(
            "" if hi is None else " from {} to {}".format(lo, hi)))


def ask_yes(prompt):
    return input(prompt + " (y/n): ").strip().lower() in ("y", "yes")


def add_goal(state, today):
    for i, name in enumerate(planner.CATALOG, 1):
        print("  {}) {}: {}".format(i, name, ", ".join(planner.CATALOG[name])))
    try:
        name = planner.add_goal(state, input("Goal (number or name): "), today)
    except ValueError as exc:
        print(exc)
        return False
    print("Added goal: {}".format(name))
    return True


def show_task(state, today):
    if planner.is_rest_day(state, today):
        print("Today is your planned rest day: no task. Enjoy the break; your streak "
              "is safe. You can still log if you draw anyway.")
        return False
    task = planner.daily_task(state, today)
    if task is not None:
        print("Today: " + task["text"])
        fix = planner.open_fix(state, task["goal"], task["skill"])
        if fix:  # R11: remind the user what they wanted to fix on this skill
            print("Last time you wanted to fix: {}".format(fix))
        return True
    if planner.all_mastered(state):
        print("Every skill is mastered and no review is due today. Raise a target "
              "(menu 8) or add a goal to keep going.")
    else:
        print("No goals yet. Add a goal first.")
    return False


def _levels(state):
    skills = {p: planner.skill_level(state, *p) for p in planner.work_options(state)}
    return planner.player_xp(state), planner.level(state), skills


def report_xp(before, after):
    """R6: tell the user what a log earned, and any level-ups."""
    xp0, lvl0, skills0 = before
    xp1, lvl1, skills1 = after
    print("+{} XP (total {} XP).".format(xp1 - xp0, xp1))
    if lvl1 > lvl0:
        print("LEVEL UP! You are now level {}.".format(lvl1))
    for (goal, skill), lvl in skills1.items():
        if lvl > skills0.get((goal, skill), 1):
            print("{} ({}) reached lvl {}!".format(skill, goal, lvl))


def pick_pair(pairs, prompt):
    for i, (goal, skill) in enumerate(pairs, 1):
        print("  {}) {} / {}".format(i, goal, skill))
    return pairs[ask_int(prompt, 1, len(pairs)) - 1]


def save_art(state, today, folder):
    source = input("Path to today's image: ")
    goal, skill = pick_pair(planner.work_options(state), "Which skill was it for? ")
    try:
        entry = gallery.save_art(state, today, source, goal, skill, folder)
    except (ValueError, OSError) as exc:
        print(exc)
        return False
    print("Saved as {}.".format(folder / entry["file"]))
    return True


def show_comparison(state, goal, skill, folder):
    page = gallery.write_comparison(state, goal, skill, folder)
    print("Then vs now for {} / {}: {}".format(goal, skill, page))
    webbrowser.open(page.resolve().as_uri())


def compare_art(state, folder):
    pairs = gallery.comparable_pairs(state, folder)
    if not pairs:
        print("Save at least two pieces for a skill to compare them.")
        return False
    goal, skill = pick_pair(pairs, "Compare which skill? ")
    show_comparison(state, goal, skill, folder)
    return False  # manual comparisons are not recorded (R5)


def monthly_comparison(state, today, folder):
    """R5: on start, once a month, show an old piece next to a recent one."""
    pair = gallery.monthly_comparison(state, today, folder)
    if pair is None:
        return False
    print("Monthly look back: see how far you have come!")
    show_comparison(state, pair[0], pair[1], folder)
    return True


def weekly_summary(state, today):
    """R7: show the last finished week's summary (menu item; not recorded)."""
    monday = planner.last_finished_week(today)
    print("Weekly summary")
    print(planner.render_week_summary(planner.week_summary(state, monday)))
    return False


def due_weekly_summary(state, today):
    """R7: on start, once a week has ended, show its summary once."""
    summary = planner.due_week_summary(state, today)
    if summary is None:
        return False
    print("Your week is done. Here is how it went:")
    print(planner.render_week_summary(summary))
    return True


def ask_log_answers(state, when="today"):
    """The four R4 questions. Returns (total, goal, skill, on_goal, drawings)."""
    total = ask_int("Total minutes you studied {}: ".format(when))
    options = planner.work_options(state)
    for i, (goal, skill) in enumerate(options, 1):
        print("  {}) {} / {}".format(i, goal, skill))
    print("  {}) something else".format(len(options) + 1))
    pick = ask_int("What did you actually work on? ", 1, len(options) + 1)
    if pick <= len(options):
        goal, skill = options[pick - 1]
        on_goal = ask_int("Minutes of that spent on the goal: ", 0, total)
    else:
        goal, skill, on_goal = None, None, 0
    drawings = ask_int("Drawings finished: ")
    return total, goal, skill, on_goal, drawings


def ask_notes(state, today, goal, skill):
    """R11: ask about open fix notes, then for today's two notes (Enter skips)."""
    fixed = {}
    for i in planner.fixes_to_check(state, goal, skill, today):
        entry = state["logs"][i]
        print("Last time you wanted to fix: {}. ({})".format(entry["fix"], entry["date"]))
        fixed[i] = ask_yes("Did you fix it?")
    went_well = input("One thing that went well (Enter to skip): ")
    fix = input("One thing you want to fix (Enter to skip): ")
    return {"went_well": went_well, "fix": fix, "fixed": fixed}


def log_today(state, today):
    before = _levels(state)
    answers = ask_log_answers(state)
    notes = ask_notes(state, today, answers[1], answers[2]) if answers[1] else {}
    try:
        planner.record_log(state, today, *answers, **notes)
    except ValueError as exc:
        print(exc)
        return False
    print("Logged. Tomorrow's task will be {} minutes.".format(state["task_minutes"]))
    report_xp(before, _levels(state))
    return True


def set_target(state, today):
    """R8: change a skill's hour target."""
    goal, skill = pick_pair(planner.work_options(state), "Which skill? ")
    hours = planner.target_hours(state, goal, skill)
    mastered = planner.is_mastered(state, goal, skill)
    print("{} ({}): {:.1f}h done of a {}h target{}.".format(
        skill, goal, planner.minutes_on(state, goal, skill) / 60, hours,
        ", mastered" if mastered else ""))
    new = ask_int("New target in hours ({}-{}): ".format(1, planner.MAX_TARGET_HOURS),
                  1, planner.MAX_TARGET_HOURS)
    try:
        planner.set_target(state, goal, skill, new)
    except ValueError as exc:
        print(exc)
        return False
    print("{} ({}) now has a {}h target.{}".format(
        skill, goal, new, " Mastered!" if planner.is_mastered(state, goal, skill) else ""))
    return True


# ---------- R9: edit or delete a log or an art piece ----------

def describe_log(entry):
    worked = ("something else" if entry["goal"] is None
              else "{} / {}, {} min on goal".format(entry["goal"], entry["skill"],
                                                    entry["goal_minutes"]))
    return "{}  {} min total, {}, {} drawings".format(
        entry["date"], entry["total_minutes"], worked, entry["drawings"])


def describe_art(entry):
    return "{}  {} / {}  {}".format(entry["date"], entry["goal"], entry["skill"],
                                    entry["file"])


def choose_entry(entries, kind, describe):
    """List entries (recent, or one date) and return the chosen index, or None."""
    raw = input("Date (YYYY-MM-DD), or Enter for the 20 most recent: ").strip()
    try:
        date = dt.date.fromisoformat(raw) if raw else None
    except ValueError:
        print("Not a date: {}".format(raw))
        return None
    found = planner.find_entries(entries, date)
    if not found:
        print("No {} found.".format(kind))
        return None
    for n, i in enumerate(found, 1):
        print("  {}) {}".format(n, describe(entries[i])))
    return found[ask_int("Which one? ", 1, len(found)) - 1]


def edit_log(state, index):
    print("Editing " + describe_log(state["logs"][index]))
    try:
        planner.edit_log(state, index, *ask_log_answers(state, "that day"))
    except ValueError as exc:
        print(exc)
        return False
    print("Saved: " + describe_log(state["logs"][index]))
    return True


def edit_art(state, index):
    goal, skill = pick_pair(planner.work_options(state), "Which skill is it for? ")
    try:
        gallery.edit_art(state, index, goal, skill)
    except ValueError as exc:
        print(exc)
        return False
    print("Saved: " + describe_art(state["art"][index]))
    return True


def edit_or_delete(state, today, folder):
    print("  1) a log\n  2) an art piece")
    if ask_int("Edit or delete which? ", 1, 2) == 1:
        kind, entries, describe = "logs", state["logs"], describe_log
    else:
        kind, entries, describe = "art pieces", state["art"], describe_art
    index = choose_entry(entries, kind, describe)
    if index is None:
        return False
    print("  1) Edit\n  2) Delete\n  3) Back")
    action = ask_int("> ", 1, 3)
    if action == 3:
        return False
    if action == 1:
        return edit_log(state, index) if kind == "logs" else edit_art(state, index)
    if not ask_yes("Delete " + describe(entries[index]) + "?"):
        return False
    if kind == "logs":
        planner.delete_log(state, index)
        print("Log deleted.")
    else:
        gallery.delete_art(state, index, folder)
        print("Art piece and its copy in {} deleted.".format(folder))
    return True


# ---------- R10: planned rest days ----------

def plan_rest_day(state, today):
    """Mark a future date as a rest day, or cancel an upcoming one."""
    print("Plan a rest day (one per week, from tomorrow on)")
    upcoming = planner.upcoming_rest_days(state, today)
    if upcoming:
        print("Upcoming rest days:")
        for i, day in enumerate(upcoming, 1):
            print("  {}) {} ({})".format(i, day.isoformat(), day.strftime("%A")))
    raw = input("Date to rest (YYYY-MM-DD){}, or Enter to go back: ".format(
        ", a number to cancel one" if upcoming else "")).strip()
    if not raw:
        return False
    try:
        if raw.isdigit() and 1 <= int(raw) <= len(upcoming):
            day = upcoming[int(raw) - 1]
            planner.cancel_rest_day(state, day, today)
            print("Rest day on {} cancelled.".format(day.isoformat()))
            return True
        try:
            day = dt.date.fromisoformat(raw)
        except ValueError:
            print("Not a date: {}".format(raw))
            return False
        planner.mark_rest_day(state, day, today)
    except ValueError as exc:
        print(exc)
        return False
    print("{} ({}) is now a rest day. It won't count as skipped or break your "
          "streak.".format(day.isoformat(), day.strftime("%A")))
    return True


# ---------- R11: look back at notes ----------

def look_back(state, today):
    """Show one skill's notes: what was fixed and what keeps coming back."""
    pairs = planner.note_pairs(state)
    if not pairs:
        print("No notes yet. They are asked for after each log (menu 4).")
        return False
    goal, skill = pick_pair(pairs, "Look back at which skill? ")
    print(planner.render_notes(state, goal, skill))
    return False  # looking back is not recorded (R11)


def notes_reminder(state, today):
    """R11: on start, once a month, remind the user to look back at their notes."""
    if not planner.due_notes_reminder(state, today):
        return False
    print("New month: look back at your notes to see which problems you fixed and "
          "which keep coming back (menu 11).")
    return True


def check_missing_art(state, folder):
    """R9: on start, offer to remove entries whose image copy is missing."""
    remove = []
    for i in gallery.missing_art(state, folder):
        entry = state["art"][i]
        print("Saved art is missing: {} ({} / {}, {}).".format(
            folder / entry["file"], entry["goal"], entry["skill"], entry["date"]))
        if ask_yes("Remove this entry?"):
            remove.append(i)
    for i in sorted(remove, reverse=True):
        gallery.forget_art(state, i)
    return bool(remove)


def main(today=None):
    path = storage.data_path()
    try:
        state = storage.load(path)
    except storage.StorageError as exc:
        print(exc, file=sys.stderr)
        return 1
    try:
        _loop(state, path, today)
    except (EOFError, KeyboardInterrupt):
        print()
    return 0


def _loop(state, path, today):
    folder = gallery.art_dir(path)
    actions = {"1": add_goal, "3": show_task, "4": log_today,
               "5": lambda st, d: save_art(st, d, folder),
               "6": lambda st, d: compare_art(st, folder), "7": weekly_summary,
               "8": set_target, "9": lambda st, d: edit_or_delete(st, d, folder),
               "10": plan_rest_day, "11": look_back}
    start = today or dt.date.today()
    changed = check_missing_art(state, folder)
    changed = due_weekly_summary(state, start) or changed
    changed = monthly_comparison(state, start, folder) or changed
    changed = notes_reminder(state, start) or changed
    if changed:
        storage.save(state, path)
    while True:
        print(MENU)
        choice = input("> ").strip().lower()
        day = today or dt.date.today()
        if choice in QUIT:
            return
        if choice == "2":
            print(planner.render_roadmap(state, day))
        elif choice in NEEDS_GOALS and not planner.active_goals(state):
            print("No goals yet. Add a goal first.")
        elif choice in actions:
            if actions[choice](state, day):  # True means state changed
                storage.save(state, path)
        else:
            print("Choose 1-12.")
