"""Interactive menu. The only module that reads input or prints."""

import datetime as dt
import sys

from drawplan import planner, storage

MENU = """
drawplan
  1) Add a goal
  2) Show roadmap
  3) Today's task
  4) Log today
  5) Quit"""


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


def log_today(state, today):
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
    actions = {"1": add_goal, "3": show_task, "4": log_today}
    while True:
        print(MENU)
        choice = input("> ").strip().lower()
        day = today or dt.date.today()
        if choice in ("5", "q", "quit"):
            return
        if choice == "2":
            print(planner.render_roadmap(state, day))
        elif choice == "4" and not planner.active_goals(state):
            print("No goals yet. Add a goal first.")
        elif choice in actions:
            if actions[choice](state, day):  # True means state changed
                storage.save(state, path)
        else:
            print("Choose 1-5.")
