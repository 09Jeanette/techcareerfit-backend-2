import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .database import Base, engine
from .routers import admin, applications, ats, auth, cvs, journal, learning, market, notifications

logging.basicConfig(level=logging.INFO)
settings = get_settings()

app = FastAPI(title="TechCareerFit API", version="2.0.0",
              description="Explainable ATS analysis, learning roadmaps and application tracking for ICT job seekers.")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_list, allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])


@app.on_event("startup")
def create_tables() -> None:
    # Creates missing tables only. For changes to existing tables, add a migration (see README).
    Base.metadata.create_all(bind=engine)


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}


for r in (auth.router, cvs.router, ats.router, learning.router, applications.router, journal.router,
          market.router, notifications.router, admin.router):
    app.include_router(r)
