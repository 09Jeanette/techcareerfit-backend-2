import uuid
from datetime import date, datetime, timezone

from sqlalchemy import JSON, Boolean, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def new_id() -> str:
    return str(uuid.uuid4())


def now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="job_seeker")  # job_seeker | admin
    headline: Mapped[str] = mapped_column(String(120), default="ICT student")
    city: Mapped[str] = mapped_column(String(80), default="")
    experience: Mapped[str] = mapped_column(String(40), default="0-1 years")
    skills: Mapped[list] = mapped_column(JSON, default=list)
    settings: Mapped[dict] = mapped_column(JSON, default=lambda: {"follow_up": True, "interview": True, "tips": False})
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

    cvs = relationship("CV", back_populates="user", cascade="all, delete-orphan")
    reports = relationship("ATSReport", back_populates="user", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="user", cascade="all, delete-orphan")
    journal = relationship("CareerJournalEntry", back_populates="user", cascade="all, delete-orphan")
    progress = relationship("ResourceProgress", back_populates="user", cascade="all, delete-orphan")


class CV(Base):
    __tablename__ = "cvs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    extracted_text: Mapped[str] = mapped_column(Text)
    skills: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    user = relationship("User", back_populates="cvs")


class ATSReport(Base):
    __tablename__ = "ats_reports"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    cv_id: Mapped[str | None] = mapped_column(ForeignKey("cvs.id", ondelete="SET NULL"), nullable=True)
    job_title: Mapped[str] = mapped_column(String(160))
    job_description: Mapped[str] = mapped_column(Text)
    score: Mapped[int] = mapped_column(Integer)
    keywords: Mapped[int] = mapped_column(Integer)
    experience: Mapped[int] = mapped_column(Integer)
    certifications: Mapped[int] = mapped_column(Integer)
    matched_skills: Mapped[list] = mapped_column(JSON, default=list)
    missing_skills: Mapped[list] = mapped_column(JSON, default=list)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    user = relationship("User", back_populates="reports")


class Application(Base):
    __tablename__ = "applications"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    cv_id: Mapped[str | None] = mapped_column(ForeignKey("cvs.id", ondelete="SET NULL"), nullable=True)
    report_id: Mapped[str | None] = mapped_column(ForeignKey("ats_reports.id", ondelete="SET NULL"), nullable=True)
    job_title: Mapped[str] = mapped_column(String(160))
    company: Mapped[str] = mapped_column(String(160))
    location: Mapped[str] = mapped_column(String(160), default="")
    job_link: Mapped[str] = mapped_column(String(500), default="")
    application_source: Mapped[str] = mapped_column(String(60), default="")
    status: Mapped[str] = mapped_column(String(20), default="Applied")  # Applied | Interview | Rejected | Hired
    ats_score: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[str] = mapped_column(Text, default="")
    follow_up_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    interview_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    deadline_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    remind: Mapped[bool] = mapped_column(Boolean, default=True)
    status_history: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    user = relationship("User", back_populates="applications")


class CareerJournalEntry(Base):
    __tablename__ = "career_journal_entries"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    report_id: Mapped[str | None] = mapped_column(ForeignKey("ats_reports.id", ondelete="SET NULL"), nullable=True)
    application_id: Mapped[str | None] = mapped_column(ForeignKey("applications.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String(200), default="")
    went_well: Mapped[str] = mapped_column(Text, default="")
    needs_improvement: Mapped[str] = mapped_column(Text, default="")
    next_action: Mapped[str] = mapped_column(Text, default="")
    mood: Mapped[str] = mapped_column(String(20), default="okay")  # unsure | okay | confident
    guidance: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    user = relationship("User", back_populates="journal")


class LearningResource(Base):
    __tablename__ = "learning_resources"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(80), default="")
    provider: Mapped[str] = mapped_column(String(120), default="")
    url: Mapped[str] = mapped_column(String(500), default="")
    skill: Mapped[str] = mapped_column(String(80), index=True)
    level: Mapped[str] = mapped_column(String(20), default="Beginner")
    minutes: Mapped[int] = mapped_column(Integer, default=45)
    reason: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class ResourceProgress(Base):
    """Tracks a candidate's progress on a roadmap item. `key` is 'skill|title'."""

    __tablename__ = "resource_progress"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    key: Mapped[str] = mapped_column(String(300))
    state: Mapped[str] = mapped_column(String(20), default="todo")  # todo | progress | done
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)
    user = relationship("User", back_populates="progress")
