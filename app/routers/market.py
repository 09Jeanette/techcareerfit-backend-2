from fastapi import APIRouter, Depends, HTTPException, status

from ..config import get_settings
from ..models import User
from ..security import current_user
from ..services.market import roles

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/roles")
def list_roles(user: User = Depends(current_user)):
    return {"roles": list(roles(get_settings().market_csv_path).keys())}


@router.get("/insights")
def role_insights(role: str, user: User = Depends(current_user)):
    data = roles(get_settings().market_csv_path)
    if role not in data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Role not found")
    have = {s.lower() for s in (user.skills or [])} | {s for c in user.cvs for s in (c.skills or [])}
    item = data[role]
    return {"role": role, **item, "skills": [{"skill": k, "share": v, "have": k in have} for k, v in item["skills"]],
            "source": "AI Jobs Market 2025-2026 (Kaggle)"}
