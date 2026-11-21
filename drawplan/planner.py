"""Planner logic: goals (R1), roadmap (R2), daily task (R3), logging (R4), XP (R6).

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


def parse_date(text):
    return dt.date.fromisoformat(text)


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
    _adjust_task_length(state, entry)
    return entry


TASK_STEP, TASK_MIN, TASK_MAX = 5, 10, 120


def _adjust_task_length(state, entry):
    """R4: lengthen the next task if today's was done in full, shorten it if not.

    Only the first log on a date that has a task counts; which skill was worked on
    does not matter (credit to the actual skill happens via the log itself).
    """
    task = state["tasks"].get(entry["date"])
    if task is None or task["adjusted"]:
        return
    done = entry["goal_minutes"] >= task["minutes"]
    new = task["minutes"] + (TASK_STEP if done else -TASK_STEP)
    state["task_minutes"] = max(TASK_MIN, min(TASK_MAX, new))
    task["adjusted"] = True
    task["completed"] = done  # R6: a completed task earns XP


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


def drawing_days(state):
    """R6: dates the user actually drew: a log with time > 0, or a saved art piece."""
    days = {e["date"] for e in state["logs"] if e["total_minutes"] > 0}
    return days | {a["date"] for a in state.get("art", [])}


def streak(state, today):
    """Consecutive drawing days, ending today (or yesterday if today has none yet)."""
    days = drawing_days(state)
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


# ---------- R6: XP and levels (all derived from logs and tasks) ----------

XP_PER_HOUR = 10
XP_PER_TASK = 20
XP_PER_MILESTONE = 100
XP_LEVEL_STEP = 50  # each level costs this much more XP than the one before


def xp_for_level(n):
    """Total XP needed to reach level n: 0, 50, 150, 300, 500, ..."""
    return XP_LEVEL_STEP * n * (n - 1) // 2


def level_for_xp(xp):
    n = 1
    while xp_for_level(n + 1) <= xp:
        n += 1
    return n


def task_completed(state, date, task):
    """Whether a day's task was completed (R4 rule: first log's on-goal minutes >= task).

    Tasks adjusted before round 2 have no "completed" flag, so it is derived from logs.
    """
    if "completed" in task:
        return task["completed"]
    if not task.get("adjusted"):
        return False
    first = next((e for e in state["logs"] if e["date"] == date), None)
    return first is not None and first["goal_minutes"] >= task["minutes"]


def skill_xp(state, goal, skill):
    minutes = sum(e["goal_minutes"] for e in state["logs"]
                  if e["goal"] == goal and e["skill"] == skill)
    tasks = sum(1 for date, t in state["tasks"].items()
                if t["goal"] == goal and t["skill"] == skill
                and task_completed(state, date, t))
    return minutes * XP_PER_HOUR // 60 + tasks * XP_PER_TASK


def skill_level(state, goal, skill):
    return level_for_xp(skill_xp(state, goal, skill))


def milestones_reached(state):
    marks = [d for g in active_goals(state) for _, d in goal_milestones(state, g)]
    marks += [d for _, d in overall_milestones(state)]
    return sum(marks)


def player_xp(state):
    skills = sum(skill_xp(state, g, s) for g, s in work_options(state))
    return skills + milestones_reached(state) * XP_PER_MILESTONE


def level(state):
    """Player level from player XP (R6 replaces the round 1 hours-based level)."""
    return level_for_xp(player_xp(state))


def next_level_xp(state):
    return xp_for_level(level(state) + 1)


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
    lines = ["Level {}  |  {} XP, next level at {} XP  |  {:.1f} total study hours  |  "
             "Streak: {} day{}".format(
                 level(state), player_xp(state), next_level_xp(state),
                 total_minutes(state) / 60, days, "" if days == 1 else "s"), ""]
    width = max(len(s) for g in goals for s in CATALOG[g])
    for goal in goals:
        lines.append("== {} ==  {:.1f}h, {} drawings".format(
            goal.upper(), goal_minutes(state, goal) / 60, goal_drawings(state, goal)))
        for skill, minutes in skill_progress(state, goal).items():
            frac = minutes / SKILL_TARGET_MINUTES
            lines.append("  {:<{w}} {} {:>3}%  {:>4.1f}/{}h  lvl {:<2} {:>4} XP".format(
                skill, progress_bar(frac), int(min(frac, 1) * 100), minutes / 60,
                SKILL_TARGET_MINUTES // 60, skill_level(state, goal, skill),
                skill_xp(state, goal, skill), w=width))
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
            "completed": False, "text": "Spend {} minutes on {} ({}): {}.".format(minutes, skill, goal, exercise)}
    state["tasks"][key] = task
    return task
