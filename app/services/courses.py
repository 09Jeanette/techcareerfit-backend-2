"""Course recommendations from Kaggle course datasets (Coursera and edX), built by scripts/build_courses.py.

Each course is tagged with the same canonical skills the ATS scanner uses, so a missing skill in a report
maps directly to courses that teach it. Ranking prefers courses that name the skill in their title, are
focused on few skills, suit beginners, are highly rated and have a direct link.
"""
import csv
import math
import os
from functools import lru_cache

from .ats import SKILL_ALIASES

SOURCE = "Coursera and edX course datasets (Kaggle)"
LEVEL_WEIGHT = {"Beginner": 1.0, "Mixed": 0.6, "Intermediate": 0.5, "Advanced": 0.1}


@lru_cache
def load(path: str) -> list[dict]:
    if not path or not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["skills"] = [s for s in r["skills"].split(";") if s]
        r["rating"] = float(r["rating"]) if r["rating"] else None
        r["reviews"] = int(r["reviews"] or 0)
    return rows


def _score(course: dict, skill: str) -> float:
    title = course["title"].lower()
    named = skill in title  # the skill itself, e.g. "docker"
    alias = any(a in title for a in SKILL_ALIASES.get(skill, [skill]))  # e.g. "containers"
    return (3.0 * named + 1.5 * (alias and not named)
            + 1.0 / len(course["skills"])
            + LEVEL_WEIGHT.get(course["level"], 0.5)
            + (course["rating"] or 4.3) / 5
            + math.log10(course["reviews"] + 1) / 6
            + (0.5 if course["link_type"] == "direct" else 0))


def for_skill(path: str, skill: str, limit: int = 3) -> list[dict]:
    """Best courses for one skill, at most two from the same platform."""
    ranked = sorted((c for c in load(path) if skill in c["skills"]), key=lambda c: _score(c, skill), reverse=True)
    picked, per_platform = [], {}
    for c in ranked:
        if per_platform.get(c["platform"], 0) >= 2 and len(ranked) > limit:
            continue
        picked.append(c)
        per_platform[c["platform"]] = per_platform.get(c["platform"], 0) + 1
        if len(picked) == limit:
            break
    return picked
