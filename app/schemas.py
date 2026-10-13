from datetime import date
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator

Status = Literal["Applied", "Interview", "Rejected", "Hired"]
Mood = Literal["unsure", "okay", "confident"]


class RegisterIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class ForgotIn(BaseModel):
    email: EmailStr


class ProfileIn(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    headline: str | None = Field(default=None, max_length=120)
    city: str | None = Field(default=None, max_length=80)
    experience: str | None = Field(default=None, max_length=40)
    skills: list[str] | None = None
    settings: dict | None = None


class PasswordIn(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


class CVTextIn(BaseModel):
    text: str = Field(min_length=20, max_length=50_000)
    filename: str | None = None


class ScoreIn(BaseModel):
    job_description: str = Field(min_length=20, max_length=50_000)
    job_title: str = Field(default="Untitled role", max_length=160)
    cv_id: str | None = None
    cv_text: str | None = Field(default=None, max_length=50_000)


class ProgressIn(BaseModel):
    key: str = Field(min_length=1, max_length=300)
    state: Literal["todo", "progress", "done"]


def _blank_to_none(v):
    """Optional dates may arrive as empty strings from HTML date inputs (defect D-01)."""
    if v is None or (isinstance(v, str) and not v.strip()):
        return None
    return v


class ApplicationIn(BaseModel):
    job_title: str = Field(min_length=1, max_length=160)
    company: str = Field(min_length=1, max_length=160)
    location: str = ""
    job_link: str = ""
    application_source: str = ""
    status: Status = "Applied"
    cv_id: str | None = None
    report_id: str | None = None
    ats_score: int | None = Field(default=None, ge=0, le=100)
    notes: str = ""
    follow_up_on: date | None = None
    interview_on: date | None = None
    deadline_on: date | None = None
    remind: bool = True

    @field_validator("follow_up_on", "interview_on", "deadline_on", mode="before")
    @classmethod
    def blank_dates(cls, v):
        return _blank_to_none(v)


class ApplicationPatch(BaseModel):
    job_title: str | None = Field(default=None, min_length=1, max_length=160)
    company: str | None = Field(default=None, min_length=1, max_length=160)
    location: str | None = None
    status: Status | None = None
    notes: str | None = None
    follow_up_on: date | None = None
    interview_on: date | None = None
    deadline_on: date | None = None
    remind: bool | None = None

    @field_validator("follow_up_on", "interview_on", "deadline_on", mode="before")
    @classmethod
    def blank_dates(cls, v):
        return _blank_to_none(v)


class JournalIn(BaseModel):
    report_id: str | None = None
    application_id: str | None = None
    went_well: str = ""
    needs_improvement: str = ""
    next_action: str = ""
    mood: Mood = "okay"


class ResourceIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    url: str = ""
    provider: str = ""
    skill: str = Field(min_length=1, max_length=80)
    level: str = "Beginner"
    minutes: int = Field(default=45, ge=1, le=10_000)
    reason: str = ""


class UserPatch(BaseModel):
    is_active: bool
