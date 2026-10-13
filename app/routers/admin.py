from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Application, ATSReport, LearningResource, User
from ..schemas import ResourceIn, UserPatch
from ..security import admin_user
from ..serializers import resource_out, user_out

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats")
def stats(_: User = Depends(admin_user), db: Session = Depends(get_db)):
    week = datetime.now(timezone.utc) - timedelta(days=7)
    count = lambda model, *where: db.scalar(select(func.count()).select_from(model).where(*where)) or 0  # noqa: E731
    reports = db.scalars(select(ATSReport)).all()
    buckets = {"0-49": 0, "50-69": 0, "70-100": 0}
    missing: dict[str, int] = {}
    for r in reports:
        buckets["0-49" if r.score < 50 else "50-69" if r.score < 70 else "70-100"] += 1
        for m in r.missing_skills or []:
            missing[m] = missing.get(m, 0) + 1
    daily = []
    for i in range(6, -1, -1):
        start = (datetime.now(timezone.utc) - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        daily.append({"day": start.strftime("%a"), "analyses": count(ATSReport, ATSReport.created_at >= start, ATSReport.created_at < end),
                      "signups": count(User, User.created_at >= start, User.created_at < end)})
    return {
        "users": count(User), "users_week": count(User, User.created_at >= week),
        "reports": count(ATSReport), "reports_week": count(ATSReport, ATSReport.created_at >= week),
        "applications": count(Application), "applications_week": count(Application, Application.created_at >= week),
        "resources": count(LearningResource),
        "score_buckets": buckets,
        "top_missing": sorted(missing.items(), key=lambda kv: kv[1], reverse=True)[:8],
        "daily": daily,
    }


@router.get("/users")
def users(_: User = Depends(admin_user), db: Session = Depends(get_db)):
    return [user_out(u) for u in db.scalars(select(User).order_by(User.created_at.desc()))]


@router.patch("/users/{user_id}")
def set_active(user_id: str, body: UserPatch, me: User = Depends(admin_user), db: Session = Depends(get_db)):
    u = db.get(User, user_id)
    if not u:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    if u.id == me.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You cannot deactivate your own account")
    u.is_active = body.is_active
    db.commit()
    return user_out(u)


@router.get("/resources")
def list_resources(_: User = Depends(admin_user), db: Session = Depends(get_db)):
    return [resource_out(r) for r in db.scalars(select(LearningResource).order_by(LearningResource.created_at.desc()))]


@router.post("/resources", status_code=201)
def add_resource(body: ResourceIn, _: User = Depends(admin_user), db: Session = Depends(get_db)):
    r = LearningResource(**body.model_dump(), category=body.skill)
    r.skill = body.skill.strip().lower()
    db.add(r)
    db.commit()
    return resource_out(r)


@router.delete("/resources/{resource_id}", status_code=204)
def delete_resource(resource_id: int, _: User = Depends(admin_user), db: Session = Depends(get_db)):
    r = db.get(LearningResource, resource_id)
    if not r:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Resource not found")
    db.delete(r)
    db.commit()
    return Response(status_code=204)
