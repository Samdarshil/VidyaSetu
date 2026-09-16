from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_role
from app.engine import match_opportunity
from app.models.models import User, StudentProfile, Opportunity, Company

router = APIRouter(prefix="/industry", tags=["industry"])


@router.get("/candidates")
def discover_candidates(
    opportunity_id: str = Query(..., description="Rank candidates against this opportunity's requirements"),
    min_match: float = Query(0.0, ge=0, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(require_role("industry")),
):
    company = db.query(Company).filter(Company.user_id == user.id).first()
    opp = db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()
    if not opp:
        raise HTTPException(404, "Opportunity not found.")
    if opp.company_id != company.id:
        raise HTTPException(403, "You may only search candidates for your own company's opportunities.")

    students = db.query(StudentProfile).all()
    results = []
    for s in students:
        skill_map = {ss.skill.name: ss.competency_score for ss in s.skills}
        m = match_opportunity(skill_map, opp)
        if m["match_percent"] < min_match:
            continue
        avg_conf = (
            sum(ss.evidence_confidence for ss in s.skills) / len(s.skills) if s.skills else 0.0
        )
        results.append({
            "student_id": s.id,
            "name": s.user.full_name,
            "institution_name": s.institution.name if s.institution else None,
            "target_role": s.target_role.title if s.target_role else None,
            "match_percent": m["match_percent"],
            "matched_skills": m["matched_skills"],
            "missing_skills": m["missing_skills"],
            "avg_evidence_confidence": round(avg_conf, 1),
        })

    return sorted(results, key=lambda r: r["match_percent"], reverse=True)


@router.get("/skill-radar")
def industry_skill_radar(db: Session = Depends(get_db), user: User = Depends(require_role("industry", "institution", "admin"))):
    """Aggregated demand-vs-supply used by both the Industry Skill Radar and
    Institution Skill Intelligence views — one real computation, two UIs.
    """
    from app.models.models import Skill, StudentSkill

    skills = db.query(Skill).all()
    out = []
    for sk in skills:
        student_scores = db.query(StudentSkill).filter(StudentSkill.skill_id == sk.id).all()
        avg_supply = (
            sum(s.competency_score for s in student_scores) / len(student_scores) if student_scores else 0.0
        )
        gap = "Critical" if sk.industry_demand_score - avg_supply > 40 else (
            "Developing" if sk.industry_demand_score - avg_supply > 15 else "Strong"
        )
        out.append({
            "skill_name": sk.name,
            "industry_demand": sk.industry_demand_score,
            "academic_supply": round(avg_supply, 1),
            "gap_status": gap,
        })
    return sorted(out, key=lambda x: x["industry_demand"], reverse=True)
