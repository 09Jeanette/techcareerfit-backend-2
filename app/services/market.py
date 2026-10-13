"""Market insights from the Kaggle "AI Jobs Market 2025-2026" dataset.

File: data/ai_jobs_market_2025_2026.csv (1,500 postings, Jan 2025 - Mar 2026).
Columns used: job_title, job_category, experience_level, annual_salary_usd, country,
remote_work, required_skills (pipe-separated), demand_score, demand_growth_yoy_pct,
posting_year, posting_month.

Salaries are annual and in US dollars, and the postings are global (no South African rows),
so the API labels them that way instead of converting them to rands.
"""
import csv
import os
import statistics
from collections import Counter
from functools import lru_cache

from .ats import extract_skills

ALL_ROLES = "All AI roles"
LEVELS = ["Entry", "Mid", "Senior", "Lead"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
SOURCE = "AI Jobs Market 2025-2026 (Kaggle)"


class MarketDataMissing(RuntimeError):
    pass


@lru_cache
def _load(path: str) -> list[dict]:
    if not path or not os.path.exists(path):
        raise MarketDataMissing(f"Market dataset not found at {path}")
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["_salary"] = float(r["annual_salary_usd"])
        r["_level"] = r["experience_level"].split(" ")[0]  # "Entry (0-2 yrs)" -> "Entry"
        r["_skills"] = [s.strip() for s in r["required_skills"].split("|") if s.strip()]
        r["_period"] = (int(r["posting_year"]), int(r["posting_month"]))
    return rows


def roles(path: str) -> list[dict]:
    rows = _load(path)
    counts = Counter(r["job_title"] for r in rows)
    cats = {r["job_title"]: r["job_category"] for r in rows}
    return [{"role": ALL_ROLES, "category": "All", "postings": len(rows)}] + [
        {"role": t, "category": cats[t], "postings": n} for t, n in counts.most_common()
    ]


def _demand_label(score: float) -> str:
    return "Very high" if score >= 90 else "High" if score >= 80 else "Medium" if score >= 65 else "Low"


def _canonical(skill: str) -> str:
    found = extract_skills(skill)
    return found[0] if found else skill.lower()


def insights(path: str, role: str, level: str = "Entry", have: set[str] | None = None) -> dict:
    rows = _load(path)
    subset = rows if role == ALL_ROLES else [r for r in rows if r["job_title"] == role]
    if not subset:
        raise KeyError(role)
    have = {h.lower() for h in (have or set())}
    n = len(subset)

    # Salary for the chosen experience level (falls back to all levels when there are too few rows)
    level = level if level in LEVELS else "Entry"
    lvl_rows = [r for r in subset if r["_level"] == level]
    use_level = len(lvl_rows) >= 3
    salaries = sorted(r["_salary"] for r in (lvl_rows if use_level else subset))
    if len(salaries) >= 4:
        q = statistics.quantiles(salaries, n=4)
        p25, p75 = q[0], q[2]
    else:
        p25, p75 = salaries[0], salaries[-1]

    # Monthly postings across the whole period covered by the file
    periods = sorted({r["_period"] for r in rows})
    per_month = Counter(r["_period"] for r in subset)
    series = [{"label": f"{MONTHS[m - 1]} {str(y)[2:]}", "count": per_month.get((y, m), 0)} for y, m in periods]

    # Skills: share of this role's postings that ask for each skill, and whether the user has it
    skill_counts = Counter(s for r in subset for s in r["_skills"])
    skills = [{"skill": s, "share": round(c / n * 100), "have": _canonical(s) in have or s.lower() in have}
              for s, c in skill_counts.most_common(8)]

    remote = Counter(r["remote_work"] for r in subset)
    demand = statistics.mean(int(r["demand_score"]) for r in subset)
    growth = statistics.mean(float(r["demand_growth_yoy_pct"]) for r in subset)
    return {
        "role": role,
        "postings": n,
        "demand": _demand_label(demand),
        "demand_score": round(demand),
        "growth": f"{growth:+.0f}% year on year",
        "salary": {
            "level": level if use_level else "All levels",
            "median": round(statistics.median(salaries)),
            "p25": round(p25), "p75": round(p75),
            "currency": "USD", "period": "year", "sample": len(salaries),
        },
        "remote_share": round((remote["Fully Remote"] + remote["Hybrid"]) / n * 100),
        "remote_split": {k: round(v / n * 100) for k, v in remote.items()},
        "top_countries": [[c, round(k / n * 100)] for c, k in Counter(r["country"] for r in subset).most_common(3)],
        "series": series,
        "skills": skills,
        "levels": LEVELS,
        "source": SOURCE,
        "note": "Global postings in US dollars per year. The dataset has no South African postings.",
    }
