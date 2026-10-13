"""Market insights from the AI Jobs Market 2025-2026 dataset (Kaggle), with built-in sample data.

If MARKET_CSV_PATH points to a CSV with these columns, it is used instead of the sample data:
    role, month (1-12), postings, salary_min, salary_max, remote_share (0-1), region, skills ("python;sql;...")
Rows are aggregated per role. Adjust `load_csv` if your export uses other column names.
"""
import csv
import os
from collections import Counter, defaultdict
from functools import lru_cache

SAMPLE = {
    "Junior Python Developer": {"demand": "High", "growth": "+12% this year", "salary": "R18k-R28k", "remote": "38%", "region": "Gauteng",
                                "series": [40, 46, 44, 52, 58, 61, 66, 72, 70, 78, 84, 90],
                                "skills": [["python", 92], ["sql", 78], ["docker", 61], ["react", 48], ["aws", 40], ["git", 36]]},
    "Data Analyst": {"demand": "High", "growth": "+9% this year", "salary": "R16k-R26k", "remote": "31%", "region": "Western Cape",
                     "series": [50, 52, 55, 54, 58, 60, 63, 62, 66, 68, 71, 74],
                     "skills": [["sql", 88], ["excel", 80], ["power bi", 66], ["python", 52], ["azure", 22], ["git", 18]]},
    "Software Engineer": {"demand": "Very high", "growth": "+15% this year", "salary": "R25k-R45k", "remote": "44%", "region": "Gauteng",
                          "series": [60, 62, 66, 70, 69, 74, 78, 80, 84, 88, 91, 95],
                          "skills": [["java", 64], ["python", 61], ["docker", 58], ["aws", 52], ["kubernetes", 40], ["git", 70]]},
    "IT Support Intern": {"demand": "Medium", "growth": "+4% this year", "salary": "R8k-R14k", "remote": "12%", "region": "KwaZulu-Natal",
                          "series": [30, 32, 31, 34, 36, 35, 37, 39, 38, 40, 41, 43],
                          "skills": [["networking", 74], ["linux", 58], ["excel", 50], ["azure", 30], ["python", 22], ["sql", 20]]},
}


@lru_cache
def load_csv(path: str) -> dict | None:
    if not path or not os.path.exists(path):
        return None
    try:
        rows = defaultdict(list)
        with open(path, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                rows[r["role"].strip()].append(r)
        out = {}
        for role, rs in rows.items():
            series = [0] * 12
            for r in rs:
                series[int(r["month"]) - 1] += int(float(r["postings"]))
            peak = max(series) or 1
            skills = Counter(s.strip().lower() for r in rs for s in r.get("skills", "").split(";") if s.strip())
            total = len(rs) or 1
            lo = min(float(r["salary_min"]) for r in rs)
            hi = max(float(r["salary_max"]) for r in rs)
            remote = sum(float(r["remote_share"]) for r in rs) / total
            region = Counter(r["region"] for r in rs).most_common(1)[0][0]
            growth = (series[-1] - series[0]) / (series[0] or 1)
            out[role] = {
                "demand": "Very high" if growth > 0.4 else "High" if growth > 0.15 else "Medium",
                "growth": f"{growth:+.0%} this year", "salary": f"R{lo / 1000:.0f}k-R{hi / 1000:.0f}k",
                "remote": f"{remote:.0%}", "region": region,
                "series": [round(v / peak * 100) for v in series],
                "skills": [[k, round(v / total * 100)] for k, v in skills.most_common(6)],
            }
        return out or None
    except (KeyError, ValueError):
        return None


def roles(path: str) -> dict:
    return load_csv(path) or SAMPLE
