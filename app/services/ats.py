"""Explainable ATS scoring (the emerging-technology component).

The score is a weighted sum of three parts so every point can be traced to evidence:
    keywords (50%) + experience (30%) + certifications (20%)

`score_cv` is the single interface the rest of the app uses. A spaCy or
Sentence Transformers model can replace the internals later without changing
callers, as long as it returns the same fields.
"""
import re

# Canonical skill -> aliases that should count as that skill.
SKILL_ALIASES: dict[str, list[str]] = {
    "python": ["python", "python3"],
    "fastapi": ["fastapi", "fast api"],
    "django": ["django"],
    "flask": ["flask"],
    "sql": ["sql", "postgresql", "postgres", "mysql", "sqlite", "t-sql"],
    "sql window functions": ["window functions", "window function"],
    "react": ["react", "react.js", "reactjs"],
    "javascript": ["javascript", "ecmascript"],
    "typescript": ["typescript"],
    "node.js": ["node.js", "nodejs"],
    "docker": ["docker", "containerisation", "containerization", "containers"],
    "kubernetes": ["kubernetes", "k8s"],
    "git": ["git", "github", "gitlab"],
    "unit testing": ["unit testing", "unit tests", "pytest", "jest", "tdd"],
    "rest api": ["rest api", "rest apis", "restful", "api development"],
    "java": ["java"],
    "c#": ["c#", ".net", "dotnet"],
    "aws": ["aws", "amazon web services"],
    "azure": ["azure"],
    "linux": ["linux", "ubuntu", "bash"],
    "networking": ["networking", "tcp/ip", "ccna"],
    "excel": ["excel", "spreadsheets"],
    "power bi": ["power bi", "powerbi"],
    "figma": ["figma"],
    "machine learning": ["machine learning", "scikit-learn"],
}

EXPERIENCE_TERMS = ["experience", "developer", "engineer", "intern", "internship", "project", "projects",
                    "built", "developed", "deployed", "led", "maintained", "years", "months", "freelance", "volunteer"]
CERT_TERMS = ["certified", "certificate", "certification", "az-900", "ccna", "comptia", "scrum", "itil"]

WEIGHTS = {"keywords": 50, "experience": 30, "certifications": 20}


def _has(term: str, text: str) -> bool:
    pattern = r"(?<![a-z0-9])" + re.escape(term) + r"(?![a-z0-9])"
    return re.search(pattern, text) is not None


def extract_skills(text: str) -> list[str]:
    """Return canonical skills mentioned in the text, in a stable order."""
    t = (text or "").lower()
    return [skill for skill, aliases in SKILL_ALIASES.items() if any(_has(a, t) for a in aliases)]


def find_matched_skills(cv_skills: list[str], required: list[str]) -> list[str]:
    return [s for s in required if s in cv_skills]


def find_missing_skills(cv_skills: list[str], required: list[str]) -> list[str]:
    return [s for s in required if s not in cv_skills]


def _signals(text: str, terms: list[str]) -> list[str]:
    t = (text or "").lower()
    return [term for term in terms if _has(term, t)]


def score_cv(cv_text: str, job_description: str) -> dict:
    """Score a CV against a job description and explain the result."""
    cv_skills = extract_skills(cv_text)
    required = extract_skills(job_description)
    matched = find_matched_skills(cv_skills, required)
    missing = find_missing_skills(cv_skills, required)

    keywords = round(len(matched) / len(required) * 100) if required else 50
    exp_signals = _signals(cv_text, EXPERIENCE_TERMS)
    experience = min(95, 40 + 6 * len(exp_signals))
    cert_signals = _signals(cv_text, CERT_TERMS)
    certifications = min(95, 40 + 15 * len(cert_signals))

    score = round(keywords * 0.5 + experience * 0.3 + certifications * 0.2)
    calculation = f"({keywords} x 50%) + ({experience} x 30%) + ({certifications} x 20%) = {score}%"
    return {
        "score": score,
        "keywords": keywords,
        "experience": experience,
        "certifications": certifications,
        "matched_skills": matched,
        "missing_skills": missing,
        "details": {
            "keyword_match": {
                "weight": WEIGHTS["keywords"], "requested": len(required), "matched": len(matched),
                "evidence": matched,
                "explanation": "Half of the score comes from technical requirements found in both the job description and the CV.",
            },
            "experience_match": {
                "weight": WEIGHTS["experience"], "signals": exp_signals,
                "explanation": "Counts role, project, internship and duration language in the CV.",
            },
            "certifications": {
                "weight": WEIGHTS["certifications"], "signals": cert_signals,
                "explanation": "Checks for certificates named in the CV.",
            },
            "calculation": calculation,
            "cv_skills": cv_skills,
        },
    }
