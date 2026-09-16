from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_role
from app.models.models import User, FacultyProfile, CollaborationRequest

router = APIRouter(prefix="/faculty", tags=["faculty"])


@router.get("/me/profile")
def my_profile(db: Session = Depends(get_db), user: User = Depends(require_role("faculty"))):
    profile = db.query(FacultyProfile).filter(FacultyProfile.user_id == user.id).first()
    if not profile:
        raise HTTPException(404, "Faculty profile not found.")
    return {
        "full_name": user.full_name,
        "institution": profile.institution.name if profile.institution else None,
        "department": profile.department.name if profile.department else None,
        "research_interests": (profile.research_interests or "").split(",") if profile.research_interests else [],
        "available_for_consultancy": profile.available_for_consultancy,
    }


@router.patch("/me/profile")
def update_profile(
    research_interests: str | None = None,
    available_for_consultancy: bool | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("faculty")),
):
    profile = db.query(FacultyProfile).filter(FacultyProfile.user_id == user.id).first()
    if not profile:
        raise HTTPException(404, "Faculty profile not found.")
    if research_interests is not None:
        profile.research_interests = research_interests
    if available_for_consultancy is not None:
        profile.available_for_consultancy = available_for_consultancy
    db.commit()
    return {"status": "updated"}


@router.get("/me/collaboration-matches")
def collaboration_matches(db: Session = Depends(get_db), user: User = Depends(require_role("faculty"))):
    """Simple keyword match between a faculty member's research interests and
    open collaboration requests targeting faculty — transparent, no ML needed
    at this scale.
    """
    profile = db.query(FacultyProfile).filter(FacultyProfile.user_id == user.id).first()
    interests = [i.strip().lower() for i in (profile.research_interests or "").split(",") if i.strip()]

    open_requests = db.query(CollaborationRequest).filter(
        CollaborationRequest.to_type.in_(["Faculty", "Institution"]),
        CollaborationRequest.status.in_(["Requested", "Under Review"]),
    ).all()

    matches = []
    for r in open_requests:
        text = (r.title + " " + (r.description or "")).lower()
        hits = [i for i in interests if i and i in text]
        if hits or not interests:
            matches.append({"id": r.id, "title": r.title, "from_type": r.from_type, "matched_on": hits})
    return matches
