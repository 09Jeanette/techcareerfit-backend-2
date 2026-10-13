from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import CV, Application, ATSReport, User
from ..schemas import ApplicationIn, ApplicationPatch
from ..security import current_user
from ..serializers import app_out

router = APIRouter(prefix="/applications", tags=["applications"])
CLOSED = {"Rejected", "Hired"}


def _today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _owned(db: Session, user: User, app_id: str) -> Application:
    a = db.get(Application, app_id)
    if not a or a.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Application not found")
    return a


@router.get("")
def list_apps(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(Application).where(Application.user_id == user.id).order_by(Application.created_at)).all()
    return [app_out(a) for a in rows]


@router.get("/insights")
def insights(user: User = Depends(current_user), db: Session = Depends(get_db)):
    apps = db.scalars(select(Application).where(Application.user_id == user.id)).all()
    today = date.today()
    active = [a for a in apps if a.status not in CLOSED]
    overdue = [a for a in active if a.follow_up_on and a.follow_up_on < today]
    recs = []
    if overdue:
        recs.append({"priority": "high", "title": "Follow up today", "body": f"{len(overdue)} follow-up(s) are overdue."})
    if not apps:
        recs.append({"priority": "medium", "title": "Add your first application", "body": "Link it to an analysed CV to track its score."})
    elif not any(a.status == "Interview" for a in apps):
        recs.append({"priority": "medium", "title": "Tailor your CV", "body": "Re-analyse your CV for each role to raise your match."})
    scores = [a.ats_score for a in apps if a.ats_score]
    return {
        "summary": {"total": len(apps), "active": len(active), "interviews": sum(a.status == "Interview" for a in apps),
                    "overdue_follow_ups": len(overdue), "average_score": round(sum(scores) / len(scores)) if scores else 0},
        "recommendations": recs,
        "overdue": [app_out(a) for a in overdue],
    }


@router.post("", status_code=201)
def create_app(body: ApplicationIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    data = body.model_dump()
    if data["cv_id"]:
        cv = db.get(CV, data["cv_id"])
        if not cv or cv.user_id != user.id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "CV not found")
        if data["ats_score"] is None:
            latest = db.scalars(select(ATSReport).where(ATSReport.cv_id == cv.id).order_by(ATSReport.created_at.desc())).first()
            data["ats_score"] = latest.score if latest else 0
            data["report_id"] = data["report_id"] or (latest.id if latest else None)
    data["ats_score"] = data["ats_score"] or 0
    a = Application(user_id=user.id, status_history=[{"status": body.status, "on": _today()}], **data)
    db.add(a)
    db.commit()
    return app_out(a)


@router.get("/{app_id}")
def get_app(app_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return app_out(_owned(db, user, app_id))


@router.patch("/{app_id}")
def update_app(app_id: str, body: ApplicationPatch, user: User = Depends(current_user), db: Session = Depends(get_db)):
    a = _owned(db, user, app_id)
    changes = body.model_dump(exclude_unset=True)
    if "status" in changes and changes["status"] and changes["status"] != a.status:
        a.status_history = [*(a.status_history or []), {"status": changes["status"], "on": _today()}]
    for field, value in changes.items():
        if field == "status" and value is None:
            continue
        setattr(a, field, value)
    db.commit()
    return app_out(a)


@router.delete("/{app_id}", status_code=204)
def delete_app(app_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    db.delete(_owned(db, user, app_id))
    db.commit()
    return Response(status_code=204)
