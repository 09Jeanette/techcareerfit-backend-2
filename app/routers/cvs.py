from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..models import CV, ATSReport, User
from ..schemas import CVTextIn
from ..security import current_user
from ..serializers import cv_out
from ..services.ats import extract_skills
from ..services.cv_parser import CVParseError, extract_text

router = APIRouter(prefix="/cvs", tags=["cvs"])


def _best_scores(db: Session, user_id: str) -> dict:
    rows = db.execute(select(ATSReport.cv_id, func.max(ATSReport.score)).where(ATSReport.user_id == user_id).group_by(ATSReport.cv_id))
    return {cv_id: best for cv_id, best in rows}


def _save(db: Session, user: User, filename: str, text: str) -> CV:
    cv = CV(user_id=user.id, filename=filename[:255], extracted_text=text, skills=extract_skills(text))
    db.add(cv)
    db.commit()
    return cv


@router.get("")
def list_cvs(user: User = Depends(current_user), db: Session = Depends(get_db)):
    best = _best_scores(db, user.id)
    cvs = db.scalars(select(CV).where(CV.user_id == user.id).order_by(CV.created_at.desc())).all()
    return [cv_out(c, best.get(c.id)) for c in cvs]


@router.post("/upload")
async def upload_cv(file: UploadFile = File(...), user: User = Depends(current_user), db: Session = Depends(get_db)):
    data = await file.read()
    if len(data) > get_settings().max_upload_mb * 1024 * 1024:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "File is larger than 5 MB.")
    try:
        text = extract_text(file.filename or "cv", data)
    except CVParseError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))
    return cv_out(_save(db, user, file.filename or "cv", text))


@router.post("/text")
def paste_cv(body: CVTextIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    count = db.scalar(select(func.count()).select_from(CV).where(CV.user_id == user.id)) or 0
    return cv_out(_save(db, user, body.filename or f"pasted-cv-{count + 1}.txt", body.text.strip()))


@router.delete("/{cv_id}", status_code=204)
def delete_cv(cv_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    cv = db.get(CV, cv_id)
    if not cv or cv.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "CV not found")
    db.delete(cv)
    db.commit()
    return Response(status_code=204)
