"""Planner logic: goals (R1), roadmap (R2), daily task (R3), logging and adjusting (R4).

Pure functions over a state dict. No input/print here; dates are passed in.
"""

CATALOG = {
    "portraits": ["proportions", "features", "values", "likeness"],
    "figure": ["gesture", "proportions", "anatomy", "poses"],
    "anatomy": ["skeleton", "muscles", "forms", "proportions"],
    "manga": ["paneling", "anatomy", "penning", "inking", "expressions"],
    "comic": ["paneling", "anatomy", "inking", "storytelling", "lettering"],
    "animation": ["gesture", "timing", "keyframes", "character design"],
}

SKILL_TARGET_MINUTES = 20 * 60


# ---------- R1: goals ----------

def active_goals(state):
    return [g["name"] for g in state["goals"]]


def add_goal(state, choice, today):
    """Add a catalog goal picked by number (1-based) or name. Returns its name."""
    text = str(choice).strip().lower()
    names = list(CATALOG)
    if text.isdigit() and 1 <= int(text) <= len(names):
        name = names[int(text) - 1]
    elif text in CATALOG:
        name = text
    else:
        raise ValueError("Unknown goal {!r}. Choose one of: {}".format(
            choice, ", ".join(names)))
    if name in active_goals(state):
        raise ValueError("{} is already one of your goals".format(name))
    state["goals"].append({"name": name, "added": today.isoformat()})
    return name


# ---------- logs (validated here; adjustment rules are added for R4) ----------

def work_options(state):
    """Every (goal, skill) pair the user could have worked on, in roadmap order."""
    return [(g, s) for g in active_goals(state) for s in CATALOG[g]]


def _whole(value, name):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError("{} must be a whole number, 0 or more".format(name))


def _validate_log(state, total_minutes, goal, skill, goal_minutes, drawings):
    _whole(total_minutes, "Total study minutes")
    _whole(goal_minutes, "On-goal minutes")
    _whole(drawings, "Drawings")
    if goal_minutes > total_minutes:
        raise ValueError("On-goal minutes cannot be more than total minutes")
    if goal is None and skill is None:
        if goal_minutes:
            raise ValueError("Time outside your goals cannot count as on-goal time")
    elif (goal, skill) not in work_options(state):
        raise ValueError("{} / {} is not part of your goals".format(goal, skill))


def record_log(state, today, total_minutes, goal, skill, goal_minutes, drawings):
    """Record what the user actually did. goal/skill None means 'something else'."""
    _validate_log(state, total_minutes, goal, skill, goal_minutes, drawings)
    entry = {"date": today.isoformat(), "total_minutes": total_minutes, "goal": goal,
             "skill": skill, "goal_minutes": goal_minutes, "drawings": drawings}
    state["logs"].append(entry)
    return entry


# ---------- R2: progress and roadmap (all derived from logs) ----------

GOAL_HOUR_MARKS = (1, 10, 50, 100)
DRAWING_MARKS = (10, 50, 100)
TOTAL_HOUR_MARKS = (10, 50, 100, 250)


def skill_progress(state, goal):
    progress = {s: 0 for s in CATALOG[goal]}
    for entry in state["logs"]:
        if entry["goal"] == goal and entry["skill"] in progress:
            progress[entry["skill"]] += entry["goal_minutes"]
    return progress


def goal_minutes(state, goal):
    return sum(e["goal_minutes"] for e in state["logs"] if e["goal"] == goal)


def goal_drawings(state, goal):
    return sum(e["drawings"] for e in state["logs"] if e["goal"] == goal)


def total_minutes(state):
    return sum(e["total_minutes"] for e in state["logs"])


def level(state):
    return 1 + total_minutes(state) // 600


def streak(state, today):
    """Consecutive days with a log, ending today (or yesterday if today has none yet)."""
    import datetime as dt
    days = {e["date"] for e in state["logs"]}
    day = today if today.isoformat() in days else today - dt.timedelta(days=1)
    count = 0
    while day.isoformat() in days:
        count += 1
        day -= dt.timedelta(days=1)
    return count


def _hours(n):
    return "{} hour{}".format(n, "" if n == 1 else "s")


def goal_milestones(state, goal):
    minutes = goal_minutes(state, goal)
    drawings = goal_drawings(state, goal)
    marks = [("{} on {}".format(_hours(h), goal), minutes >= h * 60)
             for h in GOAL_HOUR_MARKS]
    marks += [("{} drawings".format(n), drawings >= n) for n in DRAWING_MARKS]
    marks += [("Master {}".format(s), m >= SKILL_TARGET_MINUTES)
              for s, m in skill_progress(state, goal).items()]
    return marks


def overall_milestones(state):
    minutes = total_minutes(state)
    return [("{} total study hours".format(h), minutes >= h * 60)
            for h in TOTAL_HOUR_MARKS]


def progress_bar(fraction, width=20):
    filled = int(round(min(max(fraction, 0.0), 1.0) * width))
    return "[" + "#" * filled + "-" * (width - filled) + "]"


def _check(done):
    return "[x]" if done else "[ ]"


def render_roadmap(state, today):
    goals = active_goals(state)
    if not goals:
        return "No goals yet. Add a goal to get your roadmap."
    days = streak(state, today)
    lines = ["Level {}  |  {:.1f} total study hours  |  Streak: {} day{}".format(
        level(state), total_minutes(state) / 60, days, "" if days == 1 else "s"), ""]
    width = max(len(s) for g in goals for s in CATALOG[g])
    for goal in goals:
        lines.append("== {} ==  {:.1f}h, {} drawings".format(
            goal.upper(), goal_minutes(state, goal) / 60, goal_drawings(state, goal)))
        for skill, minutes in skill_progress(state, goal).items():
            frac = minutes / SKILL_TARGET_MINUTES
            lines.append("  {:<{w}} {} {:>3}%  {:.1f}/{}h".format(
                skill, progress_bar(frac), int(min(frac, 1) * 100), minutes / 60,
                SKILL_TARGET_MINUTES // 60, w=width))
        lines.append("  Milestones:")
        lines += ["    {} {}".format(_check(d), label)
                  for label, d in goal_milestones(state, goal)]
        lines.append("")
    lines.append("== OVERALL ==")
    lines += ["    {} {}".format(_check(d), label) for label, d in overall_milestones(state)]
    return "\n".join(lines)
