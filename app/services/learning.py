"""Learning roadmap: maps missing skills to resources (curated by admins, with built-in defaults)."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import LearningResource, ResourceProgress

DEFAULTS: dict[str, list[dict]] = {
    "docker": [
        {"title": "Docker get started guide", "provider": "Docker docs", "url": "https://docs.docker.com/get-started/", "level": "Beginner", "minutes": 30},
        {"title": "Containerise a FastAPI app", "provider": "FastAPI docs", "url": "https://fastapi.tiangolo.com/deployment/docker/", "level": "Hands-on", "minutes": 45},
    ],
    "unit testing": [{"title": "pytest basics", "provider": "pytest.org", "url": "https://docs.pytest.org/en/stable/getting-started.html", "level": "Beginner", "minutes": 60}],
    "java": [{"title": "Learn Java", "provider": "dev.java", "url": "https://dev.java/learn/", "level": "Beginner", "minutes": 120}],
    "aws": [{"title": "AWS Cloud Practitioner essentials", "provider": "AWS Skill Builder", "url": "https://explore.skillbuilder.aws/", "level": "Beginner", "minutes": 360}],
    "kubernetes": [{"title": "Kubernetes basics", "provider": "kubernetes.io", "url": "https://kubernetes.io/docs/tutorials/kubernetes-basics/", "level": "Beginner", "minutes": 60}],
    "power bi": [{"title": "Get started with Power BI", "provider": "Microsoft Learn", "url": "https://learn.microsoft.com/training/powerplatform/power-bi", "level": "Beginner", "minutes": 180}],
    "sql": [{"title": "SQL tutorial", "provider": "Mode", "url": "https://mode.com/sql-tutorial/", "level": "Beginner", "minutes": 90}],
    "sql window functions": [{"title": "SQL window functions", "provider": "Mode", "url": "https://mode.com/sql-tutorial/sql-window-functions/", "level": "Intermediate", "minutes": 40}],
    "react": [{"title": "React quick start", "provider": "react.dev", "url": "https://react.dev/learn", "level": "Beginner", "minutes": 60}],
    "git": [{"title": "About Git", "provider": "GitHub Docs", "url": "https://docs.github.com/en/get-started/using-git/about-git", "level": "Beginner", "minutes": 30}],
    "linux": [{"title": "The Linux command line for beginners", "provider": "Ubuntu", "url": "https://ubuntu.com/tutorials/command-line-for-beginners", "level": "Beginner", "minutes": 60}],
    "azure": [{"title": "Azure Fundamentals (AZ-900) path", "provider": "Microsoft Learn", "url": "https://learn.microsoft.com/training/", "level": "Beginner", "minutes": 240}],
}


def resources_for(db: Session, skill: str) -> list[dict]:
    rows = db.scalars(select(LearningResource).where(LearningResource.skill == skill)).all()
    items = [{"title": r.title, "provider": r.provider, "url": r.url, "level": r.level, "minutes": r.minutes,
              "reason": r.reason, "curated": True} for r in rows]
    if not items:
        items = [dict(d, curated=False) for d in DEFAULTS.get(skill, [])]
    if not items:
        items = [{"title": f"Introduction to {skill}", "provider": "Web search", "curated": False, "level": "Beginner", "minutes": 45,
                  "url": "https://www.google.com/search?q=learn+" + skill.replace(" ", "+")}]
    for it in items:
        it["skill"] = skill
        it["key"] = f"{skill}|{it['title']}"
        if not it.get("reason"):
            it["reason"] = f"{skill} is asked for in the job ad but was not found in your CV."
    return items


def roadmap(db: Session, user_id: str, missing: list[str]) -> list[dict]:
    states = {p.key: p.state for p in db.scalars(select(ResourceProgress).where(ResourceProgress.user_id == user_id))}
    out = []
    for skill in missing:
        for it in resources_for(db, skill):
            it["state"] = states.get(it["key"], "todo")
            out.append(it)
    return out
