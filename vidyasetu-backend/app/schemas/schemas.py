from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


# ---------- Auth ----------
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str  # student | faculty | institution | industry | admin
    institution_name: Optional[str] = None   # used for student/faculty/institution roles
    company_name: Optional[str] = None       # used for industry role


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: str
    full_name: str


class CurrentUserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str

    class Config:
        from_attributes = True


# ---------- Skills ----------
class EvidenceOut(BaseModel):
    evidence_type: str
    score_contribution: float
    source_note: Optional[str] = None
    recorded_at: datetime

    class Config:
        from_attributes = True


class StudentSkillOut(BaseModel):
    skill_name: str
    self_declared_level: Optional[str]
    competency_score: float
    evidence_confidence: float
    last_verified_at: Optional[datetime]
    industry_demand_score: float
    evidence: list[EvidenceOut] = []


class AddEvidenceRequest(BaseModel):
    skill_name: str
    evidence_type: str          # one of EvidenceType values
    score_contribution: float   # 0-100, how strong this evidence is on its own
    source_note: Optional[str] = None


# ---------- Career / Gap analysis ----------
class GapSkill(BaseModel):
    skill_name: str
    current_score: float
    required_level: float
    status: str  # strong | developing | critical


class GapAnalysisResponse(BaseModel):
    target_role: str
    readiness_percent: float
    skills: list[GapSkill]
    roadmap: list[str]


class SimulateSkillRequest(BaseModel):
    skill_name: str


class SimulateSkillResponse(BaseModel):
    skill_name: str
    opportunities_before: int
    opportunities_after: int
    readiness_before: float
    readiness_after: float
    estimated_effort_hours: int
    industry_demand: str


# ---------- Opportunities ----------
class SkillRequirementIn(BaseModel):
    skill_name: str
    required_level: float = 60.0
    weight: float = 1.0


class OpportunityCreate(BaseModel):
    title: str
    opportunity_type: str
    location: Optional[str] = None
    work_mode: Optional[str] = None
    compensation: Optional[str] = None
    description: Optional[str] = None
    skill_requirements: list[SkillRequirementIn] = []


class OpportunityMatchOut(BaseModel):
    id: str
    title: str
    company_name: str
    opportunity_type: str
    location: Optional[str]
    work_mode: Optional[str]
    compensation: Optional[str]
    match_percent: float
    matched_skills: list[str]
    missing_skills: list[str]


class ApplyRequest(BaseModel):
    opportunity_id: str


class ApplicationOut(BaseModel):
    id: str
    opportunity_title: str
    company_name: str
    status: str
    match_score_at_apply: Optional[float]
    applied_at: datetime


class ApplicationStatusUpdate(BaseModel):
    status: str


# ---------- Industry / candidate discovery ----------
class CandidateOut(BaseModel):
    student_id: str
    name: str
    institution_name: Optional[str]
    target_role: Optional[str]
    match_percent: float
    top_skills: list[str]
    gap_skills: list[str]
    avg_evidence_confidence: float


# ---------- Institution analytics ----------
class DepartmentSkillCoverage(BaseModel):
    department_name: str
    skill_name: str
    avg_competency: float


class InstitutionAnalyticsResponse(BaseModel):
    institution_name: str
    student_count: int
    avg_readiness: float
    heatmap: list[DepartmentSkillCoverage]
    critical_gaps: list[str]


class InterventionSimRequest(BaseModel):
    skill_name: str
    duration_hours: int = 40


class InterventionSimResponse(BaseModel):
    skill_name: str
    students_ready_before: int
    students_ready_projected: int
    opportunities_unlocked_estimate: int
    readiness_improvement_percent: float


# ---------- Collaboration ----------
class CollaborationCreate(BaseModel):
    title: str
    description: Optional[str] = None
    from_type: str
    to_type: str
    to_id: Optional[str] = None


class CollaborationOut(BaseModel):
    id: str
    title: str
    from_type: str
    to_type: str
    status: str
    participants_count: int
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Assessments ----------
class AssessmentSummary(BaseModel):
    id: str
    title: str
    skill_name: str
    assessment_type: Optional[str]
    question_count: int


class AssessmentQuestionOut(BaseModel):
    id: str
    text: str
    options: list[str]
    # No correct_index here — never sent to the student taking it.


class AssessmentDetail(BaseModel):
    id: str
    title: str
    skill_name: str
    questions: list[AssessmentQuestionOut]


class AssessmentSubmitRequest(BaseModel):
    answers: dict[str, int]  # question_id -> selected option index


class AssessmentResultOut(BaseModel):
    score: float
    correct_count: int
    total_count: int
    skill_name: str
    updated_competency_score: float
    updated_evidence_confidence: float


# ---------- GitHub evidence import ----------
class GitHubRepoIn(BaseModel):
    name: str
    primary_language: Optional[str] = None
    description: Optional[str] = None


class GitHubImportRequest(BaseModel):
    github_username: str
    repos: list[GitHubRepoIn]  # fetched client-side from GitHub's public API, then sent here to record as evidence


class GitHubImportResponse(BaseModel):
    github_username: str
    repos_processed: int
    skills_updated: list[str]


# ---------- AI Assistant ----------
class AIQueryRequest(BaseModel):
    question: str


class AIQueryResponse(BaseModel):
    answer: str
    reasons: list[str]
    source: str  # "VidyaSetu Platform Data" — always disclosed, no external calls by default
