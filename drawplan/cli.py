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
  7) Quit"""


def ask_int(prompt, lo=0, hi=None):
    while True:
        raw = input(prompt).strip()
        if raw.isdigit() and int(raw) >= lo and (hi is None or int(raw) <= hi):
            return int(raw)
        print("Please enter a whole number{}.".format(
            "" if hi is None else " from {} to {}".format(lo, hi)))


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
    task = planner.daily_task(state, today)
    print("No goals yet. Add a goal first." if task is None else "Today: " + task["text"])
    return task is not None


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
    pairs = gallery.comparable_pairs(state)
    if not pairs:
        print("Save at least two pieces for a skill to compare them.")
        return False
    goal, skill = pick_pair(pairs, "Compare which skill? ")
    show_comparison(state, goal, skill, folder)
    return False  # manual comparisons are not recorded (R5)


def monthly_comparison(state, today, folder):
    """R5: on start, once a month, show an old piece next to a recent one."""
    pair = gallery.monthly_comparison(state, today)
    if pair is None:
        return False
    print("Monthly look back: see how far you have come!")
    show_comparison(state, pair[0], pair[1], folder)
    return True


def log_today(state, today):
    before = _levels(state)
    total = ask_int("Total minutes you studied today: ")
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
    try:
        planner.record_log(state, today, total, goal, skill, on_goal, drawings)
    except ValueError as exc:
        print(exc)
        return False
    print("Logged. Tomorrow's task will be {} minutes.".format(state["task_minutes"]))
    report_xp(before, _levels(state))
    return True


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
               "6": lambda st, d: compare_art(st, folder)}
    if monthly_comparison(state, today or dt.date.today(), folder):
        storage.save(state, path)
    while True:
        print(MENU)
        choice = input("> ").strip().lower()
        day = today or dt.date.today()
        if choice in ("7", "q", "quit"):
            return
        if choice == "2":
            print(planner.render_roadmap(state, day))
        elif choice in ("4", "5") and not planner.active_goals(state):
            print("No goals yet. Add a goal first.")
        elif choice in actions:
            if actions[choice](state, day):  # True means state changed
                storage.save(state, path)
        else:
            print("Choose 1-7.")
