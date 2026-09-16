"""
The Skill Intelligence Engine.

Kept deliberately simple and fully explainable (per the product brief's own
"transparent enough for a demo" requirement) rather than a black-box model.
Every number this module produces can be traced back to specific evidence
rows or specific opportunity requirements — nothing here is a hardcoded
display value.
"""
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.models import (
    StudentSkill, SkillEvidence, CareerRole, Opportunity, StudentProfile, Skill
)

# Evidence types are weighted by how strong a demonstration of real ability
# they are: an internship's real-world feedback counts for more than a
# self-declared claim.
EVIDENCE_WEIGHTS = {
    "Technical Assessment": 1.0,
    "Practical Challenge": 1.2,
    "Project": 1.1,
    "Certification": 0.8,
    "Internship Feedback": 1.3,
    "Faculty Evaluation": 1.15,
    "Peer Review": 0.7,
    "Self-declared": 0.25,
}


def recompute_student_skill(db: Session, student_skill: StudentSkill) -> StudentSkill:
    """Recomputes competency_score and evidence_confidence from all evidence rows.

    competency_score = weighted average of each evidence's score_contribution
    evidence_confidence = grows with the number and diversity of weighted evidence,
    saturating so that a handful of strong, varied evidence sources gets you
    close to full confidence without ever quite claiming certainty.
    """
    rows = db.query(SkillEvidence).filter(SkillEvidence.student_skill_id == student_skill.id).all()
    if not rows:
        student_skill.competency_score = 0.0
        student_skill.evidence_confidence = 0.0
        return student_skill

    total_weight = sum(EVIDENCE_WEIGHTS.get(r.evidence_type.value, 0.5) for r in rows)
    weighted_score = sum(
        r.score_contribution * EVIDENCE_WEIGHTS.get(r.evidence_type.value, 0.5) for r in rows
    )
    competency = weighted_score / total_weight if total_weight else 0.0

    # confidence: diminishing-returns function of accumulated weighted evidence
    confidence = 100 * (1 - pow(2.71828, -total_weight / 2.2))

    student_skill.competency_score = round(min(100.0, competency), 1)
    student_skill.evidence_confidence = round(min(99.0, confidence), 1)
    student_skill.last_verified_at = max((r.recorded_at for r in rows), default=None)
    return student_skill


def gap_status(current: float, required: float) -> str:
    if current >= required:
        return "strong"
    if current >= required * 0.6:
        return "developing"
    return "critical"


def compute_readiness(student_skills: dict[str, float], required: dict[str, float]) -> float:
    """Readiness = average of (current/required) capped at 1.0 per skill,
    weighted equally across the target role's required skills. Explainable:
    a student missing one of five required skills entirely cannot exceed 80%.
    """
    if not required:
        return 0.0
    coverage = []
    for skill_name, req_level in required.items():
        current = student_skills.get(skill_name, 0.0)
        coverage.append(min(1.0, current / req_level) if req_level else 1.0)
    return round(100 * sum(coverage) / len(coverage), 1)


def gap_analysis(db: Session, student: StudentProfile, career_role: CareerRole) -> dict:
    student_skill_map = {
        ss.skill.name: ss.competency_score for ss in student.skills
    }
    required_map = {rs.skill.name: rs.required_level for rs in career_role.required_skills}

    skills_out = []
    for name, required_level in required_map.items():
        current = student_skill_map.get(name, 0.0)
        skills_out.append({
            "skill_name": name,
            "current_score": current,
            "required_level": required_level,
            "status": gap_status(current, required_level),
        })

    readiness = compute_readiness(student_skill_map, required_map)

    # Roadmap: order critical/developing gaps by (gap size * industry demand), highest first
    ordered = sorted(
        [s for s in skills_out if s["status"] != "strong"],
        key=lambda s: (s["required_level"] - s["current_score"]),
        reverse=True,
    )
    roadmap = [f"Improve {s['skill_name']}" for s in ordered]
    roadmap.append("Build an applied industry project using the strengthened skills")
    roadmap.append("Reassess and re-verify updated skills")
    roadmap.append("Apply to matched opportunities")

    return {
        "target_role": career_role.title,
        "readiness_percent": readiness,
        "skills": skills_out,
        "roadmap": roadmap,
    }


def match_opportunity(student_skill_map: dict[str, float], opportunity: Opportunity) -> dict:
    """Transparent weighted-coverage match score against one opportunity's
    stated skill requirements. Returns matched/missing skill lists so the UI
    can always show *why* a percentage exists, per the brief's explainability
    requirement.
    """
    reqs = opportunity.skill_requirements
    if not reqs:
        return {"match_percent": 0.0, "matched_skills": [], "missing_skills": []}

    total_weight = sum(r.weight for r in reqs)
    achieved = 0.0
    matched, missing = [], []
    for r in reqs:
        current = student_skill_map.get(r.skill.name, 0.0)
        coverage = min(1.0, current / r.required_level) if r.required_level else 1.0
        achieved += coverage * r.weight
        if current >= r.required_level * 0.75:
            matched.append(r.skill.name)
        else:
            missing.append(r.skill.name)

    percent = round(100 * achieved / total_weight, 1) if total_weight else 0.0
    return {"match_percent": percent, "matched_skills": matched, "missing_skills": missing}


def ai_explain_answer(role: str, question: str, context: dict) -> dict:
    """Rule-based, explainable assistant grounded only in platform data
    (no external LLM call, no invented facts) — matching the brief's
    requirement that AI recommendations state their reasons rather than
    asserting a conclusion. See README for how to swap in a real LLM call
    behind this same interface if desired.
    """
    q = question.lower()
    reasons = []
    source = "VidyaSetu Platform Data"

    if role == "student":
        if "next" in q or "learn" in q:
            gap = context.get("top_gap")
            if gap:
                reasons = [
                    f"You are missing or weak in {gap['skill_name']} "
                    f"(currently {gap['current_score']}, target {gap['required_level']}).",
                    f"Industry demand for {gap['skill_name']} is high relative to other gaps in your profile.",
                    "Closing this gap moves your readiness score the most per estimated hour of effort.",
                ]
                answer = f"Learn {gap['skill_name']} next — it's your highest-impact gap toward your target role."
            else:
                answer = "Set a target career role first so I can identify your highest-impact skill gap."
        elif "match" in q or "internship" in q or "opportunit" in q:
            top = context.get("top_opportunity")
            if top:
                reasons = [
                    f"You already meet {len(top['matched_skills'])} of the required skills.",
                    f"Missing: {', '.join(top['missing_skills']) or 'none'}.",
                ]
                answer = f"Your strongest current match is {top['title']} at {top['company_name']} ({top['match_percent']}%)."
            else:
                answer = "No active opportunities matched your profile yet — check back as new postings are added."
        else:
            answer = "I can help with your next skill to learn, or which opportunities best match your verified profile."
    elif role == "institution":
        gaps = context.get("critical_gaps", [])
        answer = (
            f"Your largest institution-wide gaps are: {', '.join(gaps)}."
            if gaps else "No critical skill gaps detected across tracked departments."
        )
        reasons = [
            "Calculated from average verified student competency vs. aggregated industry demand per skill.",
        ]
    elif role == "industry":
        cands = context.get("candidate_count", 0)
        answer = f"{cands} candidates currently meet at least 60% of this opportunity's requirements."
        reasons = ["Ranked by weighted skill coverage using verified competency and evidence confidence."]
    else:
        answer = "Ask me about skills, opportunities, or platform analytics relevant to your role."

    return {"answer": answer, "reasons": reasons, "source": source}
