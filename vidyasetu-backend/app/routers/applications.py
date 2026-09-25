from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_role
from app.models.models import User, StudentProfile, Application, ApplicationStatus, Company, Notification

router = APIRouter(prefix="/applications", tags=["applications"])


@router.get("/me")
def my_applications(db: Session = Depends(get_db), user: User = Depends(require_role("student"))):
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()
    apps = db.query(Application).filter(Application.student_id == profile.id).all()
    return [{
        "id": a.id,
        "opportunity_title": a.opportunity.title,
        "company_name": a.opportunity.company.name,
        "status": a.status.value,
        "match_score_at_apply": a.match_score_at_apply,
        "applied_at": a.applied_at,
    } for a in apps]


@router.get("/for-opportunity/{opportunity_id}")
def applications_for_opportunity(
    opportunity_id: str, db: Session = Depends(get_db), user: User = Depends(require_role("industry"))
):
    """Industry can only see applications for opportunities their OWN
    company posted — this is enforced here, not just hidden in the UI.
    """
    company = db.query(Company).filter(Company.user_id == user.id).first()
    apps = db.query(Application).join(Application.opportunity).filter(
        Application.opportunity_id == opportunity_id,
    ).all()
    if apps and apps[0].opportunity.company_id != company.id:
        raise HTTPException(403, "You may only view applications for your own company's opportunities.")

    return [{
        "id": a.id,
        "student_name": a.student.user.full_name,
        "institution": a.student.institution.name if a.student.institution else None,
        "status": a.status.value,
        "match_score_at_apply": a.match_score_at_apply,
        "applied_at": a.applied_at,
    } for a in apps]


@router.patch("/{application_id}/status")
def update_status(
    application_id: str, new_status: str,
    db: Session = Depends(get_db), user: User = Depends(require_role("industry")),
):
    if new_status not in [s.value for s in ApplicationStatus]:
        raise HTTPException(400, f"Invalid status. Must be one of {[s.value for s in ApplicationStatus]}")

    app_row = db.query(Application).filter(Application.id == application_id).first()
    if not app_row:
        raise HTTPException(404, "Application not found.")

    company = db.query(Company).filter(Company.user_id == user.id).first()
    if app_row.opportunity.company_id != company.id:
        raise HTTPException(403, "You may only update applications for your own company's opportunities.")

    app_row.status = new_status
    db.add(Notification(
        user_id=app_row.student.user_id,
        message=f"Your application for {app_row.opportunity.title} is now: {new_status}",
    ))
    db.commit()
    return {"id": app_row.id, "status": app_row.status.value}
