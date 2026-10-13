"""Turn ORM objects into JSON-friendly dicts (one place, so the API shape stays consistent)."""
from .models import CV, Application, ATSReport, CareerJournalEntry, LearningResource, User


def iso(d):
    return d.isoformat() if d else None


def user_out(u: User) -> dict:
    return {"id": u.id, "name": u.name, "email": u.email, "role": u.role, "headline": u.headline, "city": u.city,
            "experience": u.experience, "skills": u.skills or [], "settings": u.settings or {}, "is_active": u.is_active,
            "created_at": iso(u.created_at)}


def cv_out(c: CV, best: int | None = None) -> dict:
    return {"id": c.id, "user_id": c.user_id, "filename": c.filename, "extracted_text": c.extracted_text,
            "skills": c.skills or [], "best_score": best, "created_at": iso(c.created_at)}


def report_out(r: ATSReport) -> dict:
    return {"id": r.id, "cv_id": r.cv_id, "job_title": r.job_title, "job_description": r.job_description, "score": r.score,
            "keywords": r.keywords, "experience": r.experience, "certifications": r.certifications,
            "matched_skills": r.matched_skills or [], "missing_skills": r.missing_skills or [], "details": r.details or {},
            "created_at": iso(r.created_at)}


def app_out(a: Application) -> dict:
    return {"id": a.id, "cv_id": a.cv_id, "report_id": a.report_id, "job_title": a.job_title, "company": a.company,
            "location": a.location, "job_link": a.job_link, "application_source": a.application_source, "status": a.status,
            "ats_score": a.ats_score, "notes": a.notes, "follow_up_on": iso(a.follow_up_on), "interview_on": iso(a.interview_on),
            "deadline_on": iso(a.deadline_on), "remind": a.remind, "status_history": a.status_history or [],
            "created_at": iso(a.created_at)}


def journal_out(j: CareerJournalEntry) -> dict:
    return {"id": j.id, "report_id": j.report_id, "application_id": j.application_id, "title": j.title, "went_well": j.went_well,
            "needs_improvement": j.needs_improvement, "next_action": j.next_action, "mood": j.mood, "guidance": j.guidance,
            "created_at": iso(j.created_at)}


def resource_out(r: LearningResource) -> dict:
    return {"id": r.id, "title": r.title, "category": r.category, "provider": r.provider, "url": r.url, "skill": r.skill,
            "level": r.level, "minutes": r.minutes, "reason": r.reason, "created_at": iso(r.created_at)}
