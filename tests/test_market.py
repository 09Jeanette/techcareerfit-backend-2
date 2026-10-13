import pytest

from app.services import market

PATH = "data/ai_jobs_market_2025_2026.csv"


def test_roles_come_from_the_dataset():
    roles = market.roles(PATH)
    assert roles[0]["role"] == market.ALL_ROLES and roles[0]["postings"] == 1500
    assert len(roles) == 26 and any(r["role"] == "Data Scientist" for r in roles)


def test_insights_shape_and_labels():
    ins = market.insights(PATH, "Data Scientist", "Entry", {"python", "sql"})
    assert ins["postings"] == 61 and ins["salary"]["currency"] == "USD"
    assert ins["salary"]["p25"] <= ins["salary"]["median"] <= ins["salary"]["p75"]
    assert len(ins["series"]) == 15 and ins["series"][0]["label"] == "Jan 25"
    assert sum(p["count"] for p in ins["series"]) == 61
    py = next(s for s in ins["skills"] if s["skill"] == "Python")
    assert py["have"] is True and 0 < py["share"] <= 100


def test_unknown_role_raises():
    with pytest.raises(KeyError):
        market.insights(PATH, "Astronaut")
