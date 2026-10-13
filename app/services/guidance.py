def journal_guidance(went_well: str, needs_improvement: str, next_action: str, mood: str) -> str:
    """Short, rule-based guidance shown with a saved reflection."""
    if needs_improvement and not next_action:
        return "Turn what needs work into one small next action you can finish this week."
    if mood == "unsure":
        return "Feeling unsure is normal. Re-analyse your CV after each change so you can see progress."
    if mood == "confident":
        return "Keep the momentum: apply the same preparation to your next application."
    return "Write down one specific example you can reuse in your next interview."
