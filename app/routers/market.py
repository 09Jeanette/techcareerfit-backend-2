from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..config import get_settings
from ..models import User
from ..security import current_user
from ..services import market
from ..services.ats import extract_skills

router = APIRouter(prefix="/market", tags=["market"])


def _path() -> str:
    return get_settings().market_csv_path


@router.get("/roles")
def list_roles(user: User = Depends(current_user)):
    try:
        return {"roles": market.roles(_path()), "source": market.SOURCE}
    except market.MarketDataMissing as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc))


@router.get("/insights")
def role_insights(role: str = market.ALL_ROLES, level: str = Query("Entry", pattern="^(Entry|Mid|Senior|Lead)$"),
                  user: User = Depends(current_user)):
    # Skills the user has: from their profile plus every CV they uploaded, normalised the same way as the ATS.
    have = set()
    for s in user.skills or []:
        have.add(s.lower())
        have.update(extract_skills(s))
    for c in user.cvs:
        have.update(c.skills or [])
    try:
        return market.insights(_path(), role, level, have)
    except market.MarketDataMissing as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc))
    except KeyError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Role not found")
