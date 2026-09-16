from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_role
from app.engine import match_opportunity
from app.models.models import (
    User, StudentProfile, Opportunity, OpportunitySkillRequirement, Skill, Company,
    Application, ApplicationStatus,
)
from app.schemas.schemas import OpportunityCreate, OpportunityMatchOut, ApplyRequest, ApplicationOut

router = APIRouter(prefix="/opportunities", tags=["opportunities"])


@router.get("", response_model=list[OpportunityMatchOut])
def list_opportunities(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Every opportunity comes back with an explainable match score when the
    caller is a student; other roles see 0%/full requirement lists since
    match scoring is a per-student concept.
    """
    opps = db.query(Opportunity).filter(Opportunity.is_active == True).all()  # noqa: E712

    student_skill_map = {}
    if user.role.value == "student":
        profile = db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()
        if profile:
            student_skill_map = {ss.skill.name: ss.competency_score for ss in profile.skills}

    out = []
    for o in opps:
        m = match_opportunity(student_skill_map, o)
        out.append(OpportunityMatchOut(
            id=o.id, title=o.title, company_name=o.company.name, opportunity_type=o.opportunity_type.value,
            location=o.location, work_mode=o.work_mode, compensation=o.compensation,
            match_percent=m["match_percent"], matched_skills=m["matched_skills"], missing_skills=m["missing_skills"],
        ))
    return sorted(out, key=lambda x: x.match_percent, reverse=True)


@router.post("", status_code=201)
def create_opportunity(
    payload: OpportunityCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("industry")),
):
    company = db.query(Company).filter(Company.user_id == user.id).first()
    if not company:
        raise HTTPException(400, "No company profile linked to this account.")

    opp = Opportunity(
        company_id=company.id, title=payload.title, opportunity_type=payload.opportunity_type,
        location=payload.location, work_mode=payload.work_mode, compensation=payload.compensation,
        description=payload.description,
    )
    db.add(opp)
    db.flush()

    for req in payload.skill_requirements:
        skill = db.query(Skill).filter(Skill.name == req.skill_name).first()
        if not skill:
            skill = Skill(name=req.skill_name)
            db.add(skill)
            db.flush()
        db.add(OpportunitySkillRequirement(
            opportunity_id=opp.id, skill_id=skill.id, required_level=req.required_level, weight=req.weight,
        ))

    db.commit()
    return {"id": opp.id, "title": opp.title}


@router.post("/apply", response_model=ApplicationOut, status_code=201)
def apply(payload: ApplyRequest, db: Session = Depends(get_db), user: User = Depends(require_role("student"))):
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()
    opp = db.query(Opportunity).filter(Opportunity.id == payload.opportunity_id).first()
    if not opp:
        raise HTTPException(404, "Opportunity not found.")
    existing = db.query(Application).filter(
        Application.student_id == profile.id, Application.opportunity_id == opp.id
    ).first()
    if existing:
        raise HTTPException(400, "You have already applied to this opportunity.")

    student_skill_map = {ss.skill.name: ss.competency_score for ss in profile.skills}
    match = match_opportunity(student_skill_map, opp)

    app_row = Application(
        student_id=profile.id, opportunity_id=opp.id,
        status=ApplicationStatus.applied, match_score_at_apply=match["match_percent"],
    )
    db.add(app_row)
    db.commit()
    db.refresh(app_row)

    return ApplicationOut(
        id=app_row.id, opportunity_title=opp.title, company_name=opp.company.name,
        status=app_row.status.value, match_score_at_apply=app_row.match_score_at_apply,
        applied_at=app_row.applied_at,
    )
