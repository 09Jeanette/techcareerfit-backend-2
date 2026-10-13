from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Application, ATSReport, User
from ..security import current_user

router = APIRouter(tags=["notifications"])


@router.get("/notifications")
def notifications(user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Derived from the user's data, so nothing extra is stored. The client tracks read state."""
    out, today = [], date.today()
    for a in db.scalars(select(Application).where(Application.user_id == user.id)):
        if a.status in ("Rejected", "Hired"):
            continue
        if a.follow_up_on and a.follow_up_on < today:
            out.append({"id": f"fu-{a.id}-{a.follow_up_on}", "kind": "overdue", "title": "Follow-up is overdue",
                        "body": f"{a.company} · {a.job_title}", "link": f"app/{a.id}", "date": a.follow_up_on.isoformat()})
        if a.interview_on and 0 <= (a.interview_on - today).days <= 7:
            out.append({"id": f"iv-{a.id}-{a.interview_on}", "kind": "interview", "title": "Upcoming interview",
                        "body": f"{a.company} · {a.interview_on.strftime('%d %b')}", "link": f"app/{a.id}", "date": a.interview_on.isoformat()})
    for r in db.scalars(select(ATSReport).where(ATSReport.user_id == user.id).order_by(ATSReport.created_at.desc()).limit(3)):
        out.append({"id": f"rp-{r.id}", "kind": "report", "title": f"Report ready: {r.score}%", "body": r.job_title,
                    "link": f"report/{r.id}", "date": r.created_at.date().isoformat()})
    return sorted(out, key=lambda n: n["date"], reverse=True)
