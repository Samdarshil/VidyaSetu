from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_role
from app.models.models import User, FacultyProfile, CollaborationRequest, StudentProfile

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


@router.get("/students")
def list_students(db: Session = Depends(get_db), user: User = Depends(require_role("faculty"))):
    """Students in the faculty member's own institution — this scoping is
    the actual authorization boundary (enforced here, at the API, not by
    the frontend hiding a list): a faculty account can only browse
    students belonging to their own institution.
    """
    profile = db.query(FacultyProfile).filter(FacultyProfile.user_id == user.id).first()
    if not profile or not profile.institution_id:
        return []
    students = db.query(StudentProfile).filter(StudentProfile.institution_id == profile.institution_id).all()
    return [{
        "student_id": s.id,
        "name": s.user.full_name,
        "program": s.program,
        "target_role": s.target_role.title if s.target_role else None,
    } for s in students]


@router.get("/students/{student_id}/skills")
def student_skills_for_faculty(
    student_id: str, db: Session = Depends(get_db), user: User = Depends(require_role("faculty")),
):
    """Read-only view of a student's real evidence-backed skills, scoped to
    faculty in the same institution as the student — a faculty account
    cannot pull up a student from a different institution.
    """
    faculty_profile = db.query(FacultyProfile).filter(FacultyProfile.user_id == user.id).first()
    student = db.query(StudentProfile).filter(StudentProfile.id == student_id).first()
    if not student:
        raise HTTPException(404, "Student not found.")
    if not faculty_profile or student.institution_id != faculty_profile.institution_id:
        raise HTTPException(403, "You may only view students from your own institution.")

    return {
        "name": student.user.full_name,
        "program": student.program,
        "target_role": student.target_role.title if student.target_role else None,
        "skills": [{
            "skill_name": ss.skill.name,
            "competency_score": ss.competency_score,
            "evidence_confidence": ss.evidence_confidence,
        } for ss in student.skills],
    }


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
