"""Planner logic: goals (R1), roadmap (R2), daily task (R3), logging (R4), XP (R6),
weekly summary (R7), mastery and targets (R8), editing logs (R9).

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

DEFAULT_TARGET_HOURS = 20
SKILL_TARGET_MINUTES = DEFAULT_TARGET_HOURS * 60  # the default; see target_minutes (R8)
MAX_TARGET_HOURS = 1000


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


def _log_index(state, index):
    if isinstance(index, bool) or not isinstance(index, int) \
            or not 0 <= index < len(state["logs"]):
        raise ValueError("There is no log number {}".format(index))
    return index


def edit_log(state, index, total_minutes, goal, skill, goal_minutes, drawings):
    """R9: replace a log's four R4 answers (same checks); the date stays the same."""
    old = state["logs"][_log_index(state, index)]
    _validate_log(state, total_minutes, goal, skill, goal_minutes, drawings)
    entry = {"date": old["date"], "total_minutes": total_minutes, "goal": goal,
             "skill": skill, "goal_minutes": goal_minutes, "drawings": drawings}
    state["logs"][index] = entry
    _recheck_completion(state, entry["date"])
    return entry


def delete_log(state, index):
    """R9: remove a log. Everything derived from the logs follows by itself."""
    entry = state["logs"].pop(_log_index(state, index))
    _recheck_completion(state, entry["date"])
    return entry


def find_entries(entries, date=None, limit=20):
    """R9: indexes of logs or art pieces to choose from, newest first.

    With a date: every entry of that date. Without: the `limit` most recent.
    """
    order = sorted(range(len(entries)), key=lambda i: (entries[i]["date"], i), reverse=True)
    if date is not None:
        return [i for i in order if entries[i]["date"] == date.isoformat()]
    return order[:limit]


TASK_STEP, TASK_MIN, TASK_MAX = 5, 10, 120


def _recheck_completion(state, date):
    """R4/R9: an adjusted task's completion follows the first remaining log of its date.

    task_minutes is never rewound: later tasks were already picked with it.
    """
    task = state["tasks"].get(date)
    if task is None or not task["adjusted"]:
        return
    first = next((e for e in state["logs"] if e["date"] == date), None)
    task["completed"] = first is not None and first["goal_minutes"] >= task["minutes"]


def _adjust_task_length(state, entry):
    """R4: lengthen the next task if today's was done in full, shorten it if not.

    Only the first log on a date that has a task counts; which skill was worked on
    does not matter (credit to the actual skill happens via the log itself). A task
    already adjusted is not adjusted again, but if its logs were deleted (R9) the new
    first log decides whether it was completed.
    """
    task = state["tasks"].get(entry["date"])
    if task is None:
        return
    if task["adjusted"]:
        _recheck_completion(state, entry["date"])
        return
    done = entry["goal_minutes"] >= task["minutes"]
    # task_minutes, not the task's own minutes: a review task (R8) is shorter
    new = state["task_minutes"] + (TASK_STEP if done else -TASK_STEP)
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
    for skill, m in skill_progress(state, goal).items():
        marks += [("Master {} ({}h)".format(skill, h), m >= h * 60)
                  for h in earlier_targets(state, goal, skill)]
        marks.append(("Master {}".format(skill), m >= target_minutes(state, goal, skill)))
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
            frac = minutes / target_minutes(state, goal, skill)
            line = "  {:<{w}} {} {:>3}%  {:>4.1f}/{}h  lvl {:<2} {:>4} XP".format(
                skill, progress_bar(frac), int(min(frac, 1) * 100), minutes / 60,
                target_hours(state, goal, skill), skill_level(state, goal, skill),
                skill_xp(state, goal, skill), w=width)
            lines.append(line + ("  MASTERED" if frac >= 1 else ""))
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


FOCUS_WEEKDAYS = (0, 2, 4, 6)  # Mon, Wed, Fri, Sun: the focus skill's days (R7)


def _next_in_rotation(state, today, skip=None):
    """R3: the pair after the latest earlier task (ignoring `skip`), wrapping around.

    Only pairs that are not mastered (R8) take part. None if every pair is mastered.
    """
    pairs = work_options(state)
    rotation = [p for p in pairs if not is_mastered(state, *p)]
    candidates = [p for p in rotation if p != skip] or rotation
    if not candidates:
        return None
    anchor = None
    for date in sorted(state["tasks"], reverse=True):
        task = state["tasks"][date]
        pair = (task["goal"], task["skill"])
        if date < today.isoformat() and pair in candidates:
            anchor = pair
            break
    if anchor is None:
        return candidates[0]
    start = pairs.index(anchor)
    for step in range(1, len(pairs) + 1):
        pair = pairs[(start + step) % len(pairs)]
        if pair in candidates:
            return pair
    return anchor


def _pick_skill(state, today):
    """Today's (goal, skill) and why: "focus" (R7), "review" (R8) or "rotation" (R3).

    Returns (None, None) when every pair is mastered and no review is due.
    """
    focus = focus_pair(state, today)
    if focus is not None and is_mastered(state, *focus):
        focus = None                      # mastered since last week: no focus (R8)
    if focus is not None and today.weekday() in FOCUS_WEEKDAYS:
        return focus, "focus"
    reviews = due_reviews(state, today)
    if reviews:
        return reviews[0], "review"
    pair = _next_in_rotation(state, today, skip=focus)
    return (pair, "rotation") if pair else (None, None)


def review_minutes(task_minutes):
    return max(TASK_MIN, task_minutes // 2)


def daily_task(state, today):
    """Return today's task, picking and saving it the first time it is asked for.

    None when there are no goals, or when every skill is mastered and no review is
    due (nothing is saved then, so a later target change or new goal gives a task).
    """
    key = today.isoformat()
    if key in state["tasks"]:
        return state["tasks"][key]
    if not active_goals(state):
        return None
    pair, kind = _pick_skill(state, today)
    if pair is None:
        return None
    goal, skill = pair
    minutes = state["task_minutes"]
    if kind == "review":
        minutes = review_minutes(minutes)
    exercises = EXERCISES[skill]
    exercise = exercises[today.toordinal() % len(exercises)]
    if kind == "review":
        text = ("Review {} ({}), a skill you mastered: spend {} minutes: {}. "
                "A short review keeps it fresh.".format(skill, goal, minutes, exercise))
    else:
        text = "Spend {} minutes on {} ({}): {}.".format(minutes, skill, goal, exercise)
    if kind == "focus":
        text += " This is this week's focus skill: it got the least time last week."
    task = {"goal": goal, "skill": skill, "minutes": minutes, "adjusted": False,
            "completed": False, "text": text}
    if kind == "review":
        task["review"] = True
    state["tasks"][key] = task
    return task


# ---------- R7: weekly summary and the neglected skill ----------

def week_start(day):
    """The Monday of the calendar week (Mon-Sun) that contains `day`."""
    return day - dt.timedelta(days=day.weekday())


def last_finished_week(today):
    return week_start(today) - dt.timedelta(days=7)


def _goals_added_by(state, day):
    return [g["name"] for g in state["goals"] if g["added"] <= day.isoformat()]


def week_summary(state, monday):
    """Everything R7 reports for the week starting `monday`. Derived, never stored."""
    sunday = monday + dt.timedelta(days=6)
    first, last = monday.isoformat(), sunday.isoformat()
    logs = [e for e in state["logs"] if first <= e["date"] <= last]
    pair_minutes = {(g, s): 0 for g in _goals_added_by(state, sunday) for s in CATALOG[g]}
    for e in logs:
        if (e["goal"], e["skill"]) in pair_minutes:
            pair_minutes[(e["goal"], e["skill"])] += e["goal_minutes"]

    starts = [g["added"] for g in state["goals"]]
    counted = [monday + dt.timedelta(days=i) for i in range(7)]
    counted = [d for d in counted if starts and d.isoformat() >= min(starts)]
    completed = sum(1 for d in counted if d.isoformat() in state["tasks"]
                    and task_completed(state, d.isoformat(), state["tasks"][d.isoformat()]))

    whole_week = set(_goals_added_by(state, monday))
    mastered = [p for p in pair_minutes if is_mastered(state, *p, until=sunday)]
    shares = {p: m / target_minutes(state, *p) for p, m in pair_minutes.items()
              if p[0] in whole_week and p not in mastered}
    return {"start": first, "end": last,
            "total_minutes": sum(e["total_minutes"] for e in logs),
            "skill_minutes": pair_minutes, "mastered": mastered,
            "completed": completed, "skipped": len(counted) - completed,
            "neglected": _neglected(shares)}


def _neglected(shares):
    """The pair with the lowest share of its target, if under half the average share.

    Ties go to roadmap order. With equal targets this is the same as comparing minutes.
    """
    if not shares:
        return None
    average = sum(shares.values()) / len(shares)
    pair = min(shares, key=shares.get)  # min keeps the first of equal values
    return pair if shares[pair] < average / 2 else None


def focus_pair(state, day):
    """The pair this week's tasks focus on: last week's neglected skill, or None."""
    return week_summary(state, week_start(day) - dt.timedelta(days=7))["neglected"]


def due_week_summary(state, today):
    """R7: the last finished week's summary if it hasn't been shown yet; records it.

    Returns None when it was already shown or no goal existed by that week's Sunday.
    """
    monday = last_finished_week(today)
    sunday = monday + dt.timedelta(days=6)
    if monday.isoformat() in state["summaries"] or not _goals_added_by(state, sunday):
        return None
    state["summaries"].append(monday.isoformat())
    return week_summary(state, monday)


def render_week_summary(summary):
    lines = ["Week of {} to {}".format(summary["start"], summary["end"]),
             "  {:.1f} total hours studied".format(summary["total_minutes"] / 60),
             "  Hours per skill:"]
    pairs = summary["skill_minutes"]
    width = max((len("{} / {}".format(*p)) for p in pairs), default=0)
    mastered = summary.get("mastered", [])
    lines += ["    {:<{w}}  {:.1f}h{}".format("{} / {}".format(*p), m / 60,
                                               "  (mastered)" if p in mastered else "",
                                               w=width)
              for p, m in pairs.items()]
    lines.append("  Tasks: {} completed, {} skipped".format(
        summary["completed"], summary["skipped"]))
    if summary["neglected"]:
        goal, skill = summary["neglected"]
        lines.append("  Most neglected: {} / {} ({:.1f}h). Next week's tasks focus on it "
                     "on Mon, Wed, Fri and Sun.".format(goal, skill, pairs[(goal, skill)] / 60))
    else:
        lines.append("  No skill was neglected. Next week's tasks rotate through all skills.")
    return "\n".join(lines)



# ---------- R8: hour targets, mastery and review tasks ----------

REVIEW_EVERY_DAYS = 14


def target_hours(state, goal, skill):
    return state.get("targets", {}).get(goal, {}).get(skill, DEFAULT_TARGET_HOURS)


def target_minutes(state, goal, skill):
    return target_hours(state, goal, skill) * 60


def earlier_targets(state, goal, skill):
    """Targets this skill was mastered at before the user raised them (oldest first)."""
    return list(state.get("mastered_targets", {}).get(goal, {}).get(skill, []))


def minutes_on(state, goal, skill, until=None):
    """On-goal minutes for one pair, from every log (or the logs dated up to `until`)."""
    last = until.isoformat() if until else None
    return sum(e["goal_minutes"] for e in state["logs"]
               if e["goal"] == goal and e["skill"] == skill
               and (last is None or e["date"] <= last))


def is_mastered(state, goal, skill, until=None):
    """R8: a skill is mastered while its on-goal minutes reach its target. Never stored."""
    return minutes_on(state, goal, skill, until) >= target_minutes(state, goal, skill)


def all_mastered(state):
    pairs = work_options(state)
    return bool(pairs) and all(is_mastered(state, *p) for p in pairs)


def set_target(state, goal, skill, hours):
    """Set a pair's hour target (1-1000). A mastered skill's target can only be raised;
    its old target is kept in mastered_targets so that mastery stays on the roadmap."""
    if (goal, skill) not in work_options(state):
        raise ValueError("{} / {} is not part of your goals".format(goal, skill))
    if (isinstance(hours, bool) or not isinstance(hours, int)
            or not 1 <= hours <= MAX_TARGET_HOURS):
        raise ValueError("A target must be a whole number of hours from 1 to {}".format(
            MAX_TARGET_HOURS))
    current = target_hours(state, goal, skill)
    mastered = is_mastered(state, goal, skill)
    if mastered and hours <= current:
        raise ValueError("{} is mastered at {}h. You can only raise its target.".format(
            skill, current))
    earlier = earlier_targets(state, goal, skill)
    if earlier and hours <= max(earlier):
        raise ValueError("You already mastered {} at {}h. Choose a higher target.".format(
            skill, max(earlier)))
    if mastered:
        state.setdefault("mastered_targets", {}).setdefault(goal, {}).setdefault(
            skill, []).append(current)
    state.setdefault("targets", {}).setdefault(goal, {})[skill] = hours


def mastery_date(state, goal, skill):
    """The date of the log that first brought the pair up to its current target."""
    need, total = target_minutes(state, goal, skill), 0
    for e in sorted(state["logs"], key=lambda e: e["date"]):
        if e["goal"] == goal and e["skill"] == skill:
            total += e["goal_minutes"]
            if total >= need:
                return parse_date(e["date"])
    return None


def review_due_date(state, goal, skill, today):
    """14 days after the later of mastery and the pair's last task before today."""
    start = mastery_date(state, goal, skill)
    earlier = [d for d, t in state["tasks"].items()
               if d < today.isoformat() and (t["goal"], t["skill"]) == (goal, skill)]
    if earlier:
        start = max(start, parse_date(max(earlier)))
    return start + dt.timedelta(days=REVIEW_EVERY_DAYS)


def due_reviews(state, today):
    """Mastered pairs due for review today, longest waiting first (ties: roadmap order)."""
    due = [(review_due_date(state, *p, today), i, p)
           for i, p in enumerate(work_options(state)) if is_mastered(state, *p)]
    return [p for d, _, p in sorted(due) if d <= today]
