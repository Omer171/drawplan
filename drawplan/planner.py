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
