import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_role
from app.engine import recompute_student_skill
from app.models.models import (
    User, StudentProfile, Assessment, AssessmentResult, SkillEvidence,
)
from app.schemas.schemas import (
    AssessmentSummary, AssessmentDetail, AssessmentQuestionOut,
    AssessmentSubmitRequest, AssessmentResultOut,
)

router = APIRouter(prefix="/assessments", tags=["assessments"])


@router.get("", response_model=list[AssessmentSummary])
def list_assessments(db: Session = Depends(get_db), user: User = Depends(require_role("student"))):
    rows = db.query(Assessment).all()
    return [
        AssessmentSummary(
            id=a.id, title=a.title, skill_name=a.skill.name,
            assessment_type=a.assessment_type, question_count=len(a.questions or []),
        )
        for a in rows
    ]


@router.get("/{assessment_id}", response_model=AssessmentDetail)
def get_assessment(assessment_id: str, db: Session = Depends(get_db), user: User = Depends(require_role("student"))):
    a = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not a:
        raise HTTPException(404, "Assessment not found.")
    # correct_index is deliberately stripped here — a student taking the
    # assessment must never receive the answer key in the response payload.
    questions = [
        AssessmentQuestionOut(id=q["id"], text=q["text"], options=q["options"])
        for q in (a.questions or [])
    ]
    return AssessmentDetail(id=a.id, title=a.title, skill_name=a.skill.name, questions=questions)


@router.post("/{assessment_id}/submit", response_model=AssessmentResultOut)
def submit_assessment(
    assessment_id: str,
    payload: AssessmentSubmitRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("student")),
):
    """Scores the submission server-side (the answer key never left the
    server), persists a real AssessmentResult, records a real SkillEvidence
    row from it, and recomputes the student's skill from the full evidence
    trail — this is the P0 requirement that a result must actually change
    backend state, not just a number painted on the frontend.
    """
    a = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not a:
        raise HTTPException(404, "Assessment not found.")
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()
    if not profile:
        raise HTTPException(404, "Student profile not found.")

    questions = a.questions or []
    if not questions:
        raise HTTPException(400, "This assessment has no questions configured.")

    correct = 0
    stage_results = {}
    for q in questions:
        given = payload.answers.get(q["id"])
        is_correct = given is not None and given == q["correct_index"]
        stage_results[q["id"]] = {"given": given, "correct": is_correct}
        if is_correct:
            correct += 1

    score = round(100 * correct / len(questions), 1)

    result = AssessmentResult(
        assessment_id=a.id, student_id=profile.id, score=score, stage_results=stage_results,
    )
    db.add(result)

    # Find or create the StudentSkill row for this assessment's skill.
    from app.models.models import StudentSkill
    student_skill = db.query(StudentSkill).filter(
        StudentSkill.student_id == profile.id, StudentSkill.skill_id == a.skill_id
    ).first()
    if not student_skill:
        student_skill = StudentSkill(student_id=profile.id, skill_id=a.skill_id)
        db.add(student_skill)
        db.flush()

    db.add(SkillEvidence(
        student_skill_id=student_skill.id,
        evidence_type="Technical Assessment",
        score_contribution=score,
        source_note=f"{a.title} — {correct}/{len(questions)} correct",
    ))
    db.flush()
    recompute_student_skill(db, student_skill)
    db.commit()
    db.refresh(student_skill)

    return AssessmentResultOut(
        score=score, correct_count=correct, total_count=len(questions),
        skill_name=a.skill.name,
        updated_competency_score=student_skill.competency_score,
        updated_evidence_confidence=student_skill.evidence_confidence,
    )
