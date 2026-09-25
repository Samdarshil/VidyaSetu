from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_role
from app.models.models import User, Institution, Department, StudentProfile, StudentSkill, Skill
from app.schemas.schemas import InterventionSimRequest, InterventionSimResponse

router = APIRouter(prefix="/institutions", tags=["institutions"])


def _own_institution(db: Session, user: User) -> Institution:
    # Institution accounts are matched by name at registration (see
    # /auth/register): the institution row is created with the same name
    # the institution user signs up with.
    inst = db.query(Institution).filter(Institution.name == user.full_name).first()
    if not inst:
        # Admins aren't tied to one institution — fall back to the first
        # institution on record so the analytics view has something to show.
        inst = db.query(Institution).first()
    if not inst:
        raise HTTPException(404, "No institution found.")
    return inst


@router.get("/me/analytics")
def analytics(db: Session = Depends(get_db), user: User = Depends(require_role("institution", "admin"))):
    inst = _own_institution(db, user)
    students = db.query(StudentProfile).filter(StudentProfile.institution_id == inst.id).all()

    heatmap = []
    dept_map: dict[str, list[StudentProfile]] = {}
    for s in students:
        dname = s.department.name if s.department else "Unassigned"
        dept_map.setdefault(dname, []).append(s)

    all_skills = db.query(Skill).all()
    for dname, dept_students in dept_map.items():
        for sk in all_skills:
            scores = [
                ss.competency_score for st in dept_students for ss in st.skills if ss.skill_id == sk.id
            ]
            if scores:
                heatmap.append({
                    "department_name": dname,
                    "skill_name": sk.name,
                    "avg_competency": round(sum(scores) / len(scores), 1),
                })

    critical_gaps = sorted(
        {h["skill_name"] for h in heatmap if h["avg_competency"] < 40},
    )

    all_scores = [ss.competency_score for s in students for ss in s.skills]
    avg_readiness = round(sum(all_scores) / len(all_scores), 1) if all_scores else 0.0

    return {
        "institution_name": inst.name,
        "student_count": len(students),
        "avg_readiness": avg_readiness,
        "heatmap": heatmap,
        "critical_gaps": critical_gaps,
    }


@router.post("/me/intervention-simulator", response_model=InterventionSimResponse)
def intervention_simulator(
    payload: InterventionSimRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("institution", "admin")),
):
    inst = _own_institution(db, user)
    skill = db.query(Skill).filter(Skill.name == payload.skill_name).first()
    if not skill:
        raise HTTPException(404, f"Skill '{payload.skill_name}' not found.")

    students = db.query(StudentProfile).filter(StudentProfile.institution_id == inst.id).all()
    current_scores = []
    for s in students:
        ss = next((x for x in s.skills if x.skill_id == skill.id), None)
        current_scores.append(ss.competency_score if ss else 0.0)

    ready_before = sum(1 for c in current_scores if c >= 60)

    # Training-program effect model: hours-scaled uplift, capped at 100.
    # Transparent and tunable — not a black box — so the simulation can be
    # explained in a demo: "40 hours of training is modeled as a +uplift
    # to every student's current competency in this skill."
    uplift = min(45, payload.duration_hours * 0.9)
    projected_scores = [min(100.0, c + uplift) for c in current_scores]
    ready_after = sum(1 for c in projected_scores if c >= 60)

    readiness_before = sum(current_scores) / len(current_scores) if current_scores else 0.0
    readiness_after = sum(projected_scores) / len(projected_scores) if projected_scores else 0.0

    return InterventionSimResponse(
        skill_name=skill.name,
        students_ready_before=ready_before,
        students_ready_projected=ready_after,
        opportunities_unlocked_estimate=(ready_after - ready_before) * 3,  # avg opportunities per newly-ready student
        readiness_improvement_percent=round(readiness_after - readiness_before, 1),
    )
