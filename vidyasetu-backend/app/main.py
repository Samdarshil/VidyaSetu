from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.models import models  # noqa: F401 — ensures models are registered before create_all
from app.routers import (
    auth, skills, opportunities, applications, industry, institutions,
    faculty, collaboration, notifications, ai, assessments,
)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="VidyaSetu API",
    description="Evidence-based Skill Intelligence & Academia-Industry Collaboration platform.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(skills.router)
app.include_router(opportunities.router)
app.include_router(applications.router)
app.include_router(industry.router)
app.include_router(institutions.router)
app.include_router(faculty.router)
app.include_router(collaboration.router)
app.include_router(notifications.router)
app.include_router(ai.router)
app.include_router(assessments.router)


@app.get("/")
def health_check():
    return {"status": "ok", "service": "VidyaSetu API"}
