from app.services import courses

PATH = "data/courses.csv"


def test_catalogue_loads_with_links_and_skills():
    rows = courses.load(PATH)
    assert len(rows) > 500
    assert all(r["url"].startswith("https://") and r["skills"] for r in rows)
    assert {r["platform"] for r in rows} == {"Coursera", "edX"}


def test_recommendations_match_the_skill_and_prefer_named_courses():
    picks = courses.for_skill(PATH, "docker")
    assert 1 <= len(picks) <= 3
    assert all("docker" in c["skills"] for c in picks)
    assert "docker" in picks[0]["title"].lower()


def test_beginner_courses_rank_first_for_python():
    picks = courses.for_skill(PATH, "python")
    assert picks[0]["level"] == "Beginner"


def test_unknown_skill_returns_nothing():
    assert courses.for_skill(PATH, "underwater basket weaving") == []
