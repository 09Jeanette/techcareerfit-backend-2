import os

os.environ["DATABASE_URL"] = "sqlite:///./test_api.db"
os.environ["ADMIN_EMAILS"] = "admin@test.com"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="module")
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)


def auth(client, email="jk@test.com"):
    r = client.post("/register", json={"name": "Jeanette Kgabe", "email": email, "password": "Passw0rd!"})
    if r.status_code == 409:
        r = client.post("/login", json={"email": email, "password": "Passw0rd!"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_register_login_and_invalid_password(client):
    h = auth(client)
    assert client.get("/me", headers=h).json()["email"] == "jk@test.com"
    assert client.post("/login", json={"email": "jk@test.com", "password": "wrong"}).status_code == 401


def test_full_candidate_flow(client):
    h = auth(client)
    cv = client.post("/cvs/text", headers=h, json={"text": "Developer with Python, SQL and React projects. Internship 6 months."}).json()
    rep = client.post("/ats/score", headers=h, json={"cv_id": cv["id"], "job_title": "Junior Python Developer",
                                                     "job_description": "Python, SQL, React and Docker experience required."}).json()
    assert rep["missing_skills"] == ["docker"]
    road = client.get("/learning/roadmap", headers=h).json()
    assert road["items"] and road["items"][0]["skill"] == "docker"
    assert client.put("/learning/progress", headers=h, json={"key": road["items"][0]["key"], "state": "done"}).status_code == 200
    # D-01: blank optional dates are accepted and stored as null
    app = client.post("/applications", headers=h, json={"job_title": "Software Engineer", "company": "TUT", "cv_id": cv["id"],
                                                         "follow_up_on": "", "interview_on": "", "deadline_on": ""})
    assert app.status_code == 201 and app.json()["follow_up_on"] is None and app.json()["ats_score"] == rep["score"]
    upd = client.patch(f"/applications/{app.json()['id']}", headers=h, json={"status": "Interview"}).json()
    assert [s["status"] for s in upd["status_history"]] == ["Applied", "Interview"]
    assert client.get("/applications/insights", headers=h).json()["summary"]["interviews"] == 1
    j = client.post("/journal", headers=h, json={"report_id": rep["id"], "went_well": "Clear demo", "mood": "confident"})
    assert j.status_code == 201 and j.json()["guidance"]


def test_users_cannot_see_each_other(client):
    h1, h2 = auth(client, "a@test.com"), auth(client, "b@test.com")
    cv = client.post("/cvs/text", headers=h1, json={"text": "Python developer with SQL experience and projects."}).json()
    assert client.delete(f"/cvs/{cv['id']}", headers=h2).status_code == 404
    assert client.get("/reports", headers=h2).json() == []


def test_admin_only_routes(client):
    assert client.get("/admin/stats", headers=auth(client)).status_code == 403
    ha = auth(client, "admin@test.com")
    assert client.get("/admin/stats", headers=ha).status_code == 200
    r = client.post("/admin/resources", headers=ha, json={"title": "Docker crash course", "skill": "Docker"})
    assert r.status_code == 201 and r.json()["skill"] == "docker"


def test_responses_never_expose_password_hash(client):
    body = client.get("/me", headers=auth(client)).text
    assert "password" not in body
