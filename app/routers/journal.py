from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Application, ATSReport, CareerJournalEntry, User
from ..schemas import JournalIn
from ..security import current_user
from ..serializers import journal_out
from ..services.guidance import journal_guidance

router = APIRouter(prefix="/journal", tags=["journal"])


@router.get("")
def list_entries(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(CareerJournalEntry).where(CareerJournalEntry.user_id == user.id).order_by(CareerJournalEntry.created_at.desc())).all()
    return [journal_out(j) for j in rows]


@router.post("", status_code=201)
def create_entry(body: JournalIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if not (body.went_well.strip() or body.needs_improvement.strip() or body.next_action.strip()):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Write at least one line")
    title = "Reflection"
    if body.report_id:
        r = db.get(ATSReport, body.report_id)
        if not r or r.user_id != user.id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Report not found")
        title = f"{r.job_title} · {r.score}%"
    elif body.application_id:
        a = db.get(Application, body.application_id)
        if not a or a.user_id != user.id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Application not found")
        title = f"{a.job_title} at {a.company}"
    j = CareerJournalEntry(user_id=user.id, title=title, guidance=journal_guidance(body.went_well, body.needs_improvement, body.next_action, body.mood),
                           **body.model_dump())
    db.add(j)
    db.commit()
    return journal_out(j)


@router.delete("/{entry_id}", status_code=204)
def delete_entry(entry_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    j = db.get(CareerJournalEntry, entry_id)
    if not j or j.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Entry not found")
    db.delete(j)
    db.commit()
    return Response(status_code=204)
