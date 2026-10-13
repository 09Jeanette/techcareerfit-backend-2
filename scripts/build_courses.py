"""Build data/courses.csv from the raw Kaggle course datasets.

Inputs (data/raw/):
  coursera_course_dataset_v3.csv  Title, Organization, Skills, Ratings, course_url, Review Count, Difficulty, Type, Duration
  edx.csv                         title, link, institution, subject, level, language, associatedskills

Run from the repo root:  python -m scripts.build_courses
"""
import csv
import re
from pathlib import Path

from app.services.ats import extract_skills

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "courses.csv"
FIELDS = ["title", "platform", "provider", "url", "link_type", "skills", "level", "rating", "reviews", "duration", "type"]


def reviews_to_int(text: str) -> int:
    m = re.match(r"\s*([\d.]+)\s*([KkMm]?)", text or "")
    if not m:
        return 0
    n = float(m.group(1))
    return int(n * {"k": 1_000, "m": 1_000_000}.get(m.group(2).lower(), 1))


def slug_matches(title: str, url: str) -> bool:
    """A few rows in the Coursera file have a URL that belongs to another course. Keep only matching ones."""
    slug = url.rstrip("/").split("/")[-1].replace("-", " ").lower()
    words = [w for w in re.findall(r"[a-z0-9]+", title.lower()) if len(w) > 3]
    return not words or any(w in slug for w in words)


# The edX file lost spaces at line breaks ("forEverybody"). Split lowerUpper joins, but keep real product names.
KEEP = ["JavaScript", "TypeScript", "PyTorch", "TensorFlow", "GitHub", "GitLab", "DevOps", "MLOps", "DataOps", "DevSecOps",
        "MongoDB", "PostgreSQL", "MySQL", "NoSQL", "OpenShift", "PowerShell", "ChatGPT", "OpenAI", "LinkedIn", "YouTube",
        "BigQuery", "WordPress", "iOS", "macOS", "SharePoint", "PowerPoint", "OneDrive", "QuickBooks", "HubSpot", "SalesForce",
        "DeepLearning", "FinTech", "EdTech", "HealthTech", "BlockChain", "CyberSecurity", "SciPy", "NumPy", "PySpark", "IoT"]


def fix_spacing(title: str) -> str:
    fixed = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", title)
    for word in KEEP:
        fixed = fixed.replace(re.sub(r"(?<=[a-z])(?=[A-Z])", " ", word), word)
    fixed = re.sub(r",(?=\S)", ", ", fixed)  # "Analyze,Improve" -> "Analyze, Improve"
    return re.sub(r"\s+", " ", fixed).strip()


def search_url(platform: str, title: str) -> str:
    q = re.sub(r"\s+", "+", title.strip())
    return f"https://www.coursera.org/search?query={q}" if platform == "Coursera" else f"https://www.edx.org/search?q={q}"


def coursera() -> list[dict]:
    out = []
    with open(RAW / "coursera_course_dataset_v3.csv", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            title = r["Title"].strip()
            skills = extract_skills(f"{r['Skills']} {title}")
            if not title or not skills:
                continue
            url = r["course_url"].strip()
            direct = url.startswith("http") and slug_matches(title, url)
            try:
                rating = float(r["Ratings"])
            except ValueError:
                rating = ""
            out.append({"title": title, "platform": "Coursera", "provider": r["Organization"].strip(),
                        "url": url if direct else search_url("Coursera", title), "link_type": "direct" if direct else "search",
                        "skills": ";".join(skills), "level": r["Difficulty"].strip() or "Mixed", "rating": rating,
                        "reviews": reviews_to_int(r["Review Count"]), "duration": r["Duration"].strip(), "type": r["Type"].strip()})
    return out


def edx() -> list[dict]:
    out = []
    with open(RAW / "edx.csv", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["language"].strip() != "English":
                continue
            title = fix_spacing(r["title"])
            skills = extract_skills(f"{r['associatedskills']} {title} {r['subject']}")
            if not title or not skills or not r["link"].startswith("http"):
                continue
            level = {"Introductory": "Beginner"}.get(r["level"].strip(), r["level"].strip())
            out.append({"title": title, "platform": "edX", "provider": r["institution"].strip(), "url": r["link"].strip(),
                        "link_type": "direct", "skills": ";".join(skills), "level": level, "rating": "", "reviews": 0,
                        "duration": "", "type": "Course"})
    return out


def main() -> None:
    rows, seen = [], set()
    for r in coursera() + edx():
        key = (r["platform"], r["title"].lower())
        if key not in seen:
            seen.add(key)
            rows.append(r)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {len(rows)} courses to {OUT}")


if __name__ == "__main__":
    main()
