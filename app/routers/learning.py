from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import ATSReport, ResourceProgress, User
from ..schemas import ProgressIn
from ..security import current_user
from ..serializers import report_out
from ..services.learning import resources_for, roadmap

router = APIRouter(prefix="/learning", tags=["learning"])


@router.get("/recommend")
def recommend(skills: str = Query("", description="Comma-separated skills"), user: User = Depends(current_user), db: Session = Depends(get_db)):
    wanted = [s.strip().lower() for s in skills.split(",") if s.strip()]
    return {"resources": [r for s in wanted for r in resources_for(db, s)]}


@router.get("/roadmap")
def get_roadmap(report_id: str | None = None, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if report_id:
        report = db.get(ATSReport, report_id)
        if not report or report.user_id != user.id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Report not found")
    else:
        report = db.scalars(select(ATSReport).where(ATSReport.user_id == user.id).order_by(ATSReport.created_at.desc())).first()
    if not report:
        return {"report": None, "items": []}
    return {"report": report_out(report), "items": roadmap(db, user.id, report.missing_skills or [])}


@router.put("/progress")
def set_progress(body: ProgressIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    row = db.scalar(select(ResourceProgress).where(ResourceProgress.user_id == user.id, ResourceProgress.key == body.key))
    if row:
        row.state = body.state
    else:
        db.add(ResourceProgress(user_id=user.id, key=body.key, state=body.state))
    db.commit()
    return {"key": body.key, "state": body.state}
