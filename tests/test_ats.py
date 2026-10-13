from app.services.ats import extract_skills, score_cv

CV = """Jeanette Kgabe. Junior developer. Built a FastAPI project with PostgreSQL and React.
Internship: 6 months as a developer. Experience with Git and GitHub. Deployed projects on Render."""
AD = "We need Python, FastAPI, SQL, React and Docker. Git and unit testing are a plus."


def test_extract_skills_uses_aliases():
    skills = extract_skills("PostgreSQL, ReactJS and k8s")
    assert "sql" in skills and "react" in skills and "kubernetes" in skills


def test_no_false_positive_for_java_in_javascript():
    assert "java" not in extract_skills("I write JavaScript")


def test_score_is_explainable_and_weighted():
    r = score_cv(CV, AD)
    assert r["missing_skills"] == ["docker", "unit testing", "python"] or set(r["missing_skills"]) == {"docker", "unit testing", "python"}
    assert set(r["matched_skills"]) == {"fastapi", "sql", "react", "git"}
    expected = round(r["keywords"] * 0.5 + r["experience"] * 0.3 + r["certifications"] * 0.2)
    assert r["score"] == expected
    assert r["details"]["calculation"].endswith(f"= {r['score']}%")
    assert 0 <= r["score"] <= 100


def test_no_required_skills_gives_neutral_keywords():
    assert score_cv(CV, "A friendly team player wanted for our office.")["keywords"] == 50
