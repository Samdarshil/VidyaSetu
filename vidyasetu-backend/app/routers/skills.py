from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_role
from app.engine import gap_analysis, recompute_student_skill, compute_readiness
from app.models.models import (
    User, StudentProfile, StudentSkill, Skill, SkillEvidence, CareerRole, Opportunity
)
from app.schemas.schemas import (
    StudentSkillOut, AddEvidenceRequest, GapAnalysisResponse,
    SimulateSkillRequest, SimulateSkillResponse,
)

router = APIRouter(prefix="/students", tags=["skills"])


def _get_own_student_profile(db: Session, user: User) -> StudentProfile:
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()
    if not profile:
        raise HTTPException(404, "Student profile not found for this account.")
    return profile


@router.get("/me/skills", response_model=list[StudentSkillOut])
def my_skills(db: Session = Depends(get_db), user: User = Depends(require_role("student"))):
    profile = _get_own_student_profile(db, user)
    out = []
    for ss in profile.skills:
        out.append(StudentSkillOut(
            skill_name=ss.skill.name,
            self_declared_level=ss.self_declared_level,
            competency_score=ss.competency_score,
            evidence_confidence=ss.evidence_confidence,
            last_verified_at=ss.last_verified_at,
            industry_demand_score=ss.skill.industry_demand_score,
            evidence=[{
                "evidence_type": e.evidence_type.value,
                "score_contribution": e.score_contribution,
                "source_note": e.source_note,
                "recorded_at": e.recorded_at,
            } for e in ss.evidence],
        ))
    return out


@router.post("/me/skills/evidence", response_model=StudentSkillOut)
def add_evidence(
    payload: AddEvidenceRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("student")),
):
    """Adds one piece of evidence and recomputes competency/confidence from
    the full evidence trail — this is the 'real state flow' the brief
    requires: nothing here is a static display number.
    """
    profile = _get_own_student_profile(db, user)
    skill = db.query(Skill).filter(Skill.name == payload.skill_name).first()
    if not skill:
        skill = Skill(name=payload.skill_name)
        db.add(skill)
        db.flush()

    student_skill = db.query(StudentSkill).filter(
        StudentSkill.student_id == profile.id, StudentSkill.skill_id == skill.id
    ).first()
    if not student_skill:
        student_skill = StudentSkill(student_id=profile.id, skill_id=skill.id)
        db.add(student_skill)
        db.flush()

    db.add(SkillEvidence(
        student_skill_id=student_skill.id,
        evidence_type=payload.evidence_type,
        score_contribution=payload.score_contribution,
        source_note=payload.source_note,
    ))
    db.flush()

    recompute_student_skill(db, student_skill)
    db.commit()
    db.refresh(student_skill)

    return StudentSkillOut(
        skill_name=skill.name,
        self_declared_level=student_skill.self_declared_level,
        competency_score=student_skill.competency_score,
        evidence_confidence=student_skill.evidence_confidence,
        last_verified_at=student_skill.last_verified_at,
        industry_demand_score=skill.industry_demand_score,
        evidence=[{
            "evidence_type": e.evidence_type.value,
            "score_contribution": e.score_contribution,
            "source_note": e.source_note,
            "recorded_at": e.recorded_at,
        } for e in student_skill.evidence],
    )


@router.get("/me/gap-analysis", response_model=GapAnalysisResponse)
def my_gap_analysis(db: Session = Depends(get_db), user: User = Depends(require_role("student"))):
    profile = _get_own_student_profile(db, user)
    if not profile.target_career_role_id:
        raise HTTPException(400, "Set a target career role first (PATCH /students/me/target-role).")
    result = gap_analysis(db, profile, profile.target_role)
    return result


@router.patch("/me/target-role")
def set_target_role(role_title: str, db: Session = Depends(get_db), user: User = Depends(require_role("student"))):
    profile = _get_own_student_profile(db, user)
    role = db.query(CareerRole).filter(CareerRole.title == role_title).first()
    if not role:
        raise HTTPException(404, f"Career role '{role_title}' not found.")
    profile.target_career_role_id = role.id
    db.commit()
    return {"target_role": role.title}


@router.post("/me/simulate-skill", response_model=SimulateSkillResponse)
def simulate_skill(
    payload: SimulateSkillRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("student")),
):
    """'What happens if I learn X?' — computed from real current opportunity
    data, not a canned number: counts how many active opportunities the
    student would newly qualify for if this one skill reached a strong level.
    """
    profile = _get_own_student_profile(db, user)
    skill = db.query(Skill).filter(Skill.name == payload.skill_name).first()
    if not skill:
        raise HTTPException(404, f"Skill '{payload.skill_name}' not found.")

    current_map = {ss.skill.name: ss.competency_score for ss in profile.skills}
    projected_map = dict(current_map)
    projected_map[skill.name] = 85.0  # simulate reaching a strong competency level

    active_opps = db.query(Opportunity).filter(Opportunity.is_active == True).all()  # noqa: E712

    from app.engine import match_opportunity
    before_count = sum(1 for o in active_opps if match_opportunity(current_map, o)["match_percent"] >= 60)
    after_count = sum(1 for o in active_opps if match_opportunity(projected_map, o)["match_percent"] >= 60)

    readiness_before = readiness_after = 0.0
    if profile.target_role:
        required_map = {rs.skill.name: rs.required_level for rs in profile.target_role.required_skills}
        readiness_before = compute_readiness(current_map, required_map)
        readiness_after = compute_readiness(projected_map, required_map)

    demand = "Very High" if skill.industry_demand_score >= 80 else "High" if skill.industry_demand_score >= 60 else "Medium"

    return SimulateSkillResponse(
        skill_name=skill.name,
        opportunities_before=before_count,
        opportunities_after=after_count,
        readiness_before=readiness_before,
        readiness_after=readiness_after,
        estimated_effort_hours=max(15, int(100 - current_map.get(skill.name, 0)) // 2),
        industry_demand=demand,
    )
