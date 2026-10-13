# TechCareerFit API

FastAPI backend for TechCareerFit: explainable ATS analysis, learning roadmaps, application tracking,
a career journal, market insights and an admin workspace.

## Stack

- Python 3.11, FastAPI, Uvicorn
- SQLAlchemy 2 with PostgreSQL (Supabase in production, SQLite for local tests)
- JWT bearer authentication (PyJWT), bcrypt password hashing
- pypdf and python-docx for CV text extraction
- Docker, deployed on Render

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env             # then fill in the values
uvicorn app.main:app --reload
```

Open http://localhost:8000/docs for the interactive API documentation.
Without `DATABASE_URL`, a local SQLite file (`techcareerfit.db`) is used.

## Environment variables

| Name | Required | Purpose |
|---|---|---|
| `DATABASE_URL` | yes | Supabase Postgres connection string |
| `JWT_SECRET` | yes | Secret for signing access tokens |
| `CORS_ORIGINS` | yes | Comma-separated frontend URLs |
| `JWT_EXPIRE_MINUTES` | no | Token lifetime, default 60 |
| `ADMIN_EMAILS` | no | Emails that become admins when they register |
| `MARKET_CSV_PATH` | no | Kaggle dataset path, see `data/README.md` |
| `SMTP_*`, `FRONTEND_URL` | no | Email reminders and reset emails; disabled when `SMTP_HOST` is empty |

## Tests

```bash
pytest
```

Tests use SQLite and cover scoring, CV parsing, the full candidate flow, data isolation between users,
admin-only routes, blank optional dates (defect D-01) and that responses never expose password hashes.

## Deploy on Render

1. Push this repo to GitHub.
2. In Render, create a **Web Service** from the repo with runtime **Docker** (or use `render.yaml`).
3. Add the environment variables above. For Supabase, use the **connection pooler** URI.
4. Health check path: `/health`.

Tables are created automatically on first start. If you change a model later, add a migration
(for example with Alembic) instead of relying on `create_all`, which does not alter existing tables.

> If you are pointing this at an existing database that already has tables with the same names but a
> different shape, use a new Supabase project or schema first.

## API overview

| Area | Endpoints |
|---|---|
| Auth | `POST /register`, `POST /login`, `POST /forgot-password`, `GET/PATCH/DELETE /me`, `POST /me/password`, `GET /me/export` |
| CVs | `GET /cvs`, `POST /cvs/upload` (multipart), `POST /cvs/text`, `DELETE /cvs/{id}` |
| ATS | `POST /ats/score`, `GET /reports`, `GET /reports/{id}` |
| Learning | `GET /learning/recommend?skills=`, `GET /learning/roadmap?report_id=`, `PUT /learning/progress` |
| Applications | `GET/POST /applications`, `GET/PATCH/DELETE /applications/{id}`, `GET /applications/insights` |
| Journal | `GET/POST /journal`, `DELETE /journal/{id}` |
| Market | `GET /market/roles`, `GET /market/insights?role=` |
| Notifications | `GET /notifications` |
| Admin | `GET /admin/stats`, `GET /admin/users`, `PATCH /admin/users/{id}`, `GET/POST/DELETE /admin/resources` |

### How the score works

`app/services/ats.py` → `score_cv(cv_text, job_description)`:

```
score = keywords x 50% + experience x 30% + certifications x 20%
```

Every part returns the evidence behind it, and `details.calculation` holds the written formula.
A pre-trained NLP model can replace the internals of `score_cv` later without changing any route.
