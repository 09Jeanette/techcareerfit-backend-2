from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import CV, ATSReport, User
from ..schemas import ScoreIn
from ..security import current_user
from ..serializers import report_out
from ..services.ats import extract_skills, score_cv

router = APIRouter(tags=["ats"])


@router.post("/ats/score")
def score(body: ScoreIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if body.cv_id:
        cv = db.get(CV, body.cv_id)
        if not cv or cv.user_id != user.id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "CV not found")
    elif body.cv_text and len(body.cv_text.strip()) >= 20:
        cv = CV(user_id=user.id, filename="pasted-cv.txt", extracted_text=body.cv_text.strip(), skills=extract_skills(body.cv_text))
        db.add(cv)
        db.flush()
    else:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Provide cv_id or cv_text")

    result = score_cv(cv.extracted_text, body.job_description)
    report = ATSReport(user_id=user.id, cv_id=cv.id, job_title=(body.job_title or "Untitled role").strip()[:160],
                       job_description=body.job_description, **result)
    db.add(report)
    db.commit()
    return report_out(report)


@router.get("/reports")
def list_reports(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(ATSReport).where(ATSReport.user_id == user.id).order_by(ATSReport.created_at)).all()
    return [report_out(r) for r in rows]


@router.get("/reports/{report_id}")
def get_report(report_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    r = db.get(ATSReport, report_id)
    if not r or r.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Report not found")
    return report_out(r)
