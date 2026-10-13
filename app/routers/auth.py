from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..models import User
from ..schemas import ForgotIn, LoginIn, PasswordIn, ProfileIn, RegisterIn
from ..security import create_token, current_user, hash_password, verify_password
from ..serializers import app_out, cv_out, journal_out, report_out, user_out
from ..services import mailer

router = APIRouter(tags=["auth"])


def _auth_payload(user: User) -> dict:
    return {"access_token": create_token(user), "token_type": "bearer", "user": user_out(user)}


@router.post("/register")
def register(body: RegisterIn, db: Session = Depends(get_db)):
    email = body.email.lower()
    if db.scalar(select(User).where(func.lower(User.email) == email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists.")
    role = "admin" if email in get_settings().admin_list else "job_seeker"
    user = User(name=body.name.strip(), email=email, password_hash=hash_password(body.password), role=role, skills=[])
    db.add(user)
    db.commit()
    return _auth_payload(user)


@router.post("/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(func.lower(User.email) == body.email.lower()))
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This account has been deactivated.")
    return _auth_payload(user)


@router.post("/forgot-password")
def forgot_password(body: ForgotIn, db: Session = Depends(get_db)):
    """Always returns 200 so the response does not reveal which emails are registered."""
    user = db.scalar(select(User).where(func.lower(User.email) == body.email.lower()))
    if user:
        link = f"{get_settings().frontend_url}/#login"
        mailer.send(user.email, "Reset your TechCareerFit password",
                    f"Hi {user.name},\n\nWe received a request to reset your password. Open {link} to continue.\n"
                    "If this was not you, you can ignore this email.\n\nTechCareerFit")
    return {"message": "If an account exists for this email, a reset link has been sent."}


@router.get("/me")
def me(user: User = Depends(current_user)):
    return user_out(user)


@router.patch("/me")
def update_me(body: ProfileIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    for field, value in body.model_dump(exclude_none=True).items():
        if field == "skills":
            value = [s.strip() for s in value if s.strip()][:40]
        if field == "settings":
            value = {**(user.settings or {}), **value}
        setattr(user, field, value)
    db.commit()
    return user_out(user)


@router.post("/me/password")
def change_password(body: PasswordIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Current password is incorrect")
    user.password_hash = hash_password(body.new_password)
    db.commit()
    return {"message": "Password updated"}


@router.get("/me/export")
def export_my_data(user: User = Depends(current_user)):
    """POPIA: give the user a copy of everything stored about them."""
    return {"user": user_out(user), "cvs": [cv_out(c) for c in user.cvs], "reports": [report_out(r) for r in user.reports],
            "applications": [app_out(a) for a in user.applications], "journal": [journal_out(j) for j in user.journal]}


@router.delete("/me", status_code=204)
def delete_me(user: User = Depends(current_user), db: Session = Depends(get_db)):
    """POPIA: permanently remove the account and all related records."""
    db.delete(user)
    db.commit()
    return Response(status_code=204)
