"""Planner logic: goals (R1), roadmap (R2), daily task (R3), logging and adjusting (R4).

Pure functions over a state dict. No input/print here; dates are passed in.
"""

import datetime as dt

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


# ---------- R3: one task per day ----------

EXERCISES = {
    "proportions": ["measure and draw 5 heads using the half-way eye line",
                    "draw 10 quick figures checking head-count proportions",
                    "copy 3 photos, measuring angles with your pencil"],
    "features": ["fill a page with 10 eyes from different angles",
                 "draw 8 noses and 8 mouths from reference",
                 "draw 6 ears, then 6 hairlines"],
    "values": ["make a 9-step value scale, then shade 3 spheres",
               "do 5 small 3-value thumbnail studies of faces",
               "shade a portrait photo using only 4 values"],
    "likeness": ["draw one portrait from a photo, then check it against a tracing",
                 "do 4 ten-minute portraits of the same person",
                 "draw a friend or family member from life for the whole session"],
    "gesture": ["do 20 one-minute gesture drawings",
                "do 10 two-minute gestures focusing on the line of action",
                "draw 30 thirty-second gestures of people in motion"],
    "anatomy": ["study and draw the torso muscles from 3 angles",
                "draw 5 arms and 5 legs with muscle groups labelled",
                "copy 2 pages from an anatomy reference"],
    "poses": ["draw 8 dynamic poses from reference",
              "draw one pose from 3 different camera angles",
              "invent 5 action poses using a mannequin first"],
    "skeleton": ["draw the skull from front, side and 3/4",
                 "draw the rib cage and pelvis from 3 angles",
                 "draw a full skeleton standing, then sitting"],
    "muscles": ["draw the shoulder and arm muscles as simple shapes",
                "draw the leg muscles from front and back",
                "draw the back muscles over a skeleton sketch"],
    "forms": ["draw 30 boxes, cylinders and spheres in perspective",
              "build a figure out of simple 3D forms only",
              "draw hands as boxes and cylinders, 6 times"],
    "paneling": ["thumbnail a 6-panel page from a short scene you invent",
                 "copy the panel layout of 2 pages you like",
                 "draw 3 layouts of the same page and pick the clearest"],
    "penning": ["fill a page with line-weight practice: thick to thin strokes",
                "pen over 3 of your old sketches with confident lines",
                "draw 50 controlled straight lines and 50 curves"],
    "inking": ["ink one finished panel with spotted blacks",
               "do a hatching and cross-hatching texture sheet",
               "ink the same sketch twice: brush, then pen"],
    "expressions": ["draw one face with 12 different emotions",
                    "draw 6 expressions from a mirror",
                    "draw a character reacting to 4 different events"],
    "storytelling": ["write and thumbnail a 4-panel strip",
                     "redraw one page to make its story clearer",
                     "thumbnail a scene from 3 different camera angles"],
    "lettering": ["practice a full alphabet of comic lettering, twice",
                  "letter 3 panels with balloons and tails",
                  "design 5 sound effects"],
    "timing": ["animate a bouncing ball in 12 frames",
               "chart the timing of a pendulum swing",
               "animate a ball bounce with ease in and ease out"],
    "keyframes": ["draw the 3 keyframes of a jump",
                  "draw key poses for a walk cycle",
                  "draw keyframes of a character turning their head"],
    "character design": ["design one character in 3 silhouettes, pick the best",
                         "draw a turnaround of a character: front, side, back",
                         "draw your character with 5 different props"],
}


def _pick_skill(state):
    """The (goal, skill) furthest behind its target; ties go to earlier goal, then skill."""
    best = None
    for goal in active_goals(state):
        for skill, minutes in skill_progress(state, goal).items():
            frac = minutes / SKILL_TARGET_MINUTES
            if best is None or frac < best[0]:
                best = (frac, goal, skill)
    return best[1], best[2]


def daily_task(state, today):
    """Return today's task, picking and saving it the first time it is asked for."""
    key = today.isoformat()
    if key in state["tasks"]:
        return state["tasks"][key]
    if not active_goals(state):
        return None
    goal, skill = _pick_skill(state)
    minutes = state["task_minutes"]
    exercises = EXERCISES[skill]
    exercise = exercises[today.toordinal() % len(exercises)]
    task = {"goal": goal, "skill": skill, "minutes": minutes, "adjusted": False,
            "text": "Spend {} minutes on {} ({}): {}.".format(minutes, skill, goal, exercise)}
    state["tasks"][key] = task
    return task
