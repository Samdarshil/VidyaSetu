from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.engine import ai_explain_answer, match_opportunity
from app.models.models import User, StudentProfile, Opportunity, Institution, StudentSkill, Skill
from app.schemas.schemas import AIQueryRequest, AIQueryResponse

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/ask", response_model=AIQueryResponse)
def ask(payload: AIQueryRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Vidya, the platform assistant. Deliberately grounded only in
    VidyaSetu's own database — see app/engine.py:ai_explain_answer for the
    reasoning, and the README for how to plug in a real LLM behind this same
    endpoint without changing the frontend contract.
    """
    context = {}

    if user.role.value == "student":
        profile = db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()
        if profile:
            skill_map = {ss.skill.name: ss.competency_score for ss in profile.skills}
            if profile.target_role:
                required = {rs.skill.name: rs.required_level for rs in profile.target_role.required_skills}
                gaps = sorted(
                    [
                        {"skill_name": n, "current_score": skill_map.get(n, 0.0), "required_level": r}
                        for n, r in required.items() if skill_map.get(n, 0.0) < r
                    ],
                    key=lambda g: g["required_level"] - g["current_score"], reverse=True,
                )
                context["top_gap"] = gaps[0] if gaps else None

            opps = db.query(Opportunity).filter(Opportunity.is_active == True).all()  # noqa: E712
            scored = []
            for o in opps:
                m = match_opportunity(skill_map, o)
                scored.append({"title": o.title, "company_name": o.company.name, **m})
            scored.sort(key=lambda x: x["match_percent"], reverse=True)
            context["top_opportunity"] = scored[0] if scored else None

    elif user.role.value == "institution":
        inst = db.query(Institution).filter(Institution.name == user.full_name).first()
        if inst:
            students = [s for s in db.query(StudentProfile).filter(StudentProfile.institution_id == inst.id)]
            skills = db.query(Skill).all()
            gaps = []
            for sk in skills:
                scores = [ss.competency_score for s in students for ss in s.skills if ss.skill_id == sk.id]
                avg = sum(scores) / len(scores) if scores else 0.0
                if sk.industry_demand_score - avg > 40:
                    gaps.append(sk.name)
            context["critical_gaps"] = gaps

    elif user.role.value == "industry":
        context["candidate_count"] = db.query(StudentProfile).count()

    return ai_explain_answer(user.role.value, payload.question, context)
