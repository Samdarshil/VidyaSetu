import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, Enum, JSON
)
from sqlalchemy.orm import relationship

from app.database import Base


def gen_id() -> str:
    return str(uuid.uuid4())


class RoleEnum(str, enum.Enum):
    student = "student"
    faculty = "faculty"
    institution = "institution"
    industry = "industry"
    admin = "admin"


class ApplicationStatus(str, enum.Enum):
    applied = "Applied"
    under_review = "Under Review"
    shortlisted = "Shortlisted"
    interview = "Interview"
    selected = "Selected"
    rejected = "Rejected"
    withdrawn = "Withdrawn"


class OpportunityType(str, enum.Enum):
    job = "Job"
    internship = "Internship"
    project = "Industry Project"
    research = "Research"
    mentorship = "Mentorship"
    training = "Training Program"


class CollaborationStatus(str, enum.Enum):
    draft = "Draft"
    requested = "Requested"
    under_review = "Under Review"
    accepted = "Accepted"
    active = "Active"
    completed = "Completed"
    declined = "Declined"


class EvidenceType(str, enum.Enum):
    assessment = "Technical Assessment"
    practical_challenge = "Practical Challenge"
    project = "Project"
    certification = "Certification"
    internship_feedback = "Internship Feedback"
    faculty_evaluation = "Faculty Evaluation"
    peer_review = "Peer Review"
    self_declared = "Self-declared"


# ---------------------------------------------------------------- Identity

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=gen_id)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(RoleEnum), nullable=False)
    full_name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    student_profile = relationship("StudentProfile", back_populates="user", uselist=False)
    faculty_profile = relationship("FacultyProfile", back_populates="user", uselist=False)
    notifications = relationship("Notification", back_populates="user")


class Institution(Base):
    __tablename__ = "institutions"
    id = Column(String, primary_key=True, default=gen_id)
    name = Column(String, nullable=False)
    city = Column(String)
    state = Column(String)
    institution_type = Column(String)  # e.g. IIT, State University, Private
    created_at = Column(DateTime, default=datetime.utcnow)

    departments = relationship("Department", back_populates="institution")
    students = relationship("StudentProfile", back_populates="institution")


class Department(Base):
    __tablename__ = "departments"
    id = Column(String, primary_key=True, default=gen_id)
    name = Column(String, nullable=False)
    institution_id = Column(String, ForeignKey("institutions.id"), nullable=False)

    institution = relationship("Institution", back_populates="departments")
    students = relationship("StudentProfile", back_populates="department")


class Company(Base):
    __tablename__ = "companies"
    id = Column(String, primary_key=True, default=gen_id)
    name = Column(String, nullable=False)
    industry_domain = Column(String)
    city = Column(String)
    user_id = Column(String, ForeignKey("users.id"))  # owning industry account

    opportunities = relationship("Opportunity", back_populates="company")


# ---------------------------------------------------------------- Profiles

class StudentProfile(Base):
    __tablename__ = "student_profiles"
    id = Column(String, primary_key=True, default=gen_id)
    user_id = Column(String, ForeignKey("users.id"), unique=True, nullable=False)
    institution_id = Column(String, ForeignKey("institutions.id"))
    department_id = Column(String, ForeignKey("departments.id"))
    program = Column(String)          # e.g. B.Tech CSE
    year_of_study = Column(Integer)
    cgpa = Column(Float)
    target_career_role_id = Column(String, ForeignKey("career_roles.id"))

    user = relationship("User", back_populates="student_profile")
    institution = relationship("Institution", back_populates="students")
    department = relationship("Department", back_populates="students")
    target_role = relationship("CareerRole")
    skills = relationship("StudentSkill", back_populates="student")
    applications = relationship("Application", back_populates="student")
    projects = relationship("Project", back_populates="student")
    certifications = relationship("Certification", back_populates="student")


class FacultyProfile(Base):
    __tablename__ = "faculty_profiles"
    id = Column(String, primary_key=True, default=gen_id)
    user_id = Column(String, ForeignKey("users.id"), unique=True, nullable=False)
    institution_id = Column(String, ForeignKey("institutions.id"))
    department_id = Column(String, ForeignKey("departments.id"))
    research_interests = Column(Text)     # comma-separated for prototype simplicity
    available_for_consultancy = Column(Boolean, default=True)

    user = relationship("User", back_populates="faculty_profile")


# ---------------------------------------------------------------- Skills

class SkillCategory(Base):
    __tablename__ = "skill_categories"
    id = Column(String, primary_key=True, default=gen_id)
    name = Column(String, unique=True, nullable=False)


class Skill(Base):
    __tablename__ = "skills"
    id = Column(String, primary_key=True, default=gen_id)
    name = Column(String, unique=True, nullable=False)
    category_id = Column(String, ForeignKey("skill_categories.id"))
    industry_demand_score = Column(Float, default=50.0)  # 0-100, updated from aggregated opportunity requirements


class SkillEvidence(Base):
    """One piece of evidence backing a StudentSkill score."""
    __tablename__ = "skill_evidence"
    id = Column(String, primary_key=True, default=gen_id)
    student_skill_id = Column(String, ForeignKey("student_skills.id"), nullable=False)
    evidence_type = Column(Enum(EvidenceType), nullable=False)
    weight = Column(Float, default=1.0)          # relative strength of this evidence
    score_contribution = Column(Float, default=0.0)  # 0-100 contribution from this evidence
    source_note = Column(String)                  # e.g. "Docker Practical Challenge, Sep 20"
    recorded_at = Column(DateTime, default=datetime.utcnow)

    student_skill = relationship("StudentSkill", back_populates="evidence")


class StudentSkill(Base):
    __tablename__ = "student_skills"
    id = Column(String, primary_key=True, default=gen_id)
    student_id = Column(String, ForeignKey("student_profiles.id"), nullable=False)
    skill_id = Column(String, ForeignKey("skills.id"), nullable=False)

    self_declared_level = Column(String)     # e.g. "Advanced" - what the user claims
    competency_score = Column(Float, default=0.0)     # 0-100, derived from evidence
    evidence_confidence = Column(Float, default=0.0)  # 0-100, derived from evidence quantity/quality
    last_verified_at = Column(DateTime, nullable=True)

    student = relationship("StudentProfile", back_populates="skills")
    skill = relationship("Skill")
    evidence = relationship("SkillEvidence", back_populates="student_skill")


class Assessment(Base):
    __tablename__ = "assessments"
    id = Column(String, primary_key=True, default=gen_id)
    skill_id = Column(String, ForeignKey("skills.id"), nullable=False)
    title = Column(String, nullable=False)
    assessment_type = Column(String)   # "Practical Challenge", "MCQ + Practical", etc.
    stages = Column(JSON, default=list)  # ["Submit", "Explain", "Modify", "Debug", "Edge case"]


class AssessmentResult(Base):
    __tablename__ = "assessment_results"
    id = Column(String, primary_key=True, default=gen_id)
    assessment_id = Column(String, ForeignKey("assessments.id"), nullable=False)
    student_id = Column(String, ForeignKey("student_profiles.id"), nullable=False)
    score = Column(Float)
    stage_results = Column(JSON, default=dict)
    completed_at = Column(DateTime, default=datetime.utcnow)


class Project(Base):
    __tablename__ = "projects"
    id = Column(String, primary_key=True, default=gen_id)
    student_id = Column(String, ForeignKey("student_profiles.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    skills_used = Column(String)  # comma-separated skill names, prototype simplicity
    evidence_url = Column(String)

    student = relationship("StudentProfile", back_populates="projects")


class Certification(Base):
    __tablename__ = "certifications"
    id = Column(String, primary_key=True, default=gen_id)
    student_id = Column(String, ForeignKey("student_profiles.id"), nullable=False)
    title = Column(String, nullable=False)
    issuer = Column(String)
    issued_at = Column(DateTime)

    student = relationship("StudentProfile", back_populates="certifications")


# ---------------------------------------------------------------- Career roles

class CareerRole(Base):
    __tablename__ = "career_roles"
    id = Column(String, primary_key=True, default=gen_id)
    title = Column(String, unique=True, nullable=False)   # "AI/ML Engineer"

    required_skills = relationship("CareerRoleSkill", back_populates="career_role")


class CareerRoleSkill(Base):
    __tablename__ = "career_role_skills"
    id = Column(String, primary_key=True, default=gen_id)
    career_role_id = Column(String, ForeignKey("career_roles.id"), nullable=False)
    skill_id = Column(String, ForeignKey("skills.id"), nullable=False)
    required_level = Column(Float, default=70.0)   # 0-100 target competency

    career_role = relationship("CareerRole", back_populates="required_skills")
    skill = relationship("Skill")


# ---------------------------------------------------------------- Opportunities

class Opportunity(Base):
    __tablename__ = "opportunities"
    id = Column(String, primary_key=True, default=gen_id)
    company_id = Column(String, ForeignKey("companies.id"), nullable=False)
    title = Column(String, nullable=False)
    opportunity_type = Column(Enum(OpportunityType), nullable=False)
    location = Column(String)
    work_mode = Column(String)   # Remote / Hybrid / On-site
    compensation = Column(String)  # kept as display string ("₹35,000/mo") for prototype
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="opportunities")
    skill_requirements = relationship("OpportunitySkillRequirement", back_populates="opportunity")
    applications = relationship("Application", back_populates="opportunity")


class OpportunitySkillRequirement(Base):
    __tablename__ = "opportunity_skill_requirements"
    id = Column(String, primary_key=True, default=gen_id)
    opportunity_id = Column(String, ForeignKey("opportunities.id"), nullable=False)
    skill_id = Column(String, ForeignKey("skills.id"), nullable=False)
    required_level = Column(Float, default=60.0)
    weight = Column(Float, default=1.0)   # importance of this skill to the match score

    opportunity = relationship("Opportunity", back_populates="skill_requirements")
    skill = relationship("Skill")


class Application(Base):
    __tablename__ = "applications"
    id = Column(String, primary_key=True, default=gen_id)
    student_id = Column(String, ForeignKey("student_profiles.id"), nullable=False)
    opportunity_id = Column(String, ForeignKey("opportunities.id"), nullable=False)
    status = Column(Enum(ApplicationStatus), default=ApplicationStatus.applied)
    match_score_at_apply = Column(Float)
    applied_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    student = relationship("StudentProfile", back_populates="applications")
    opportunity = relationship("Opportunity", back_populates="applications")


# ---------------------------------------------------------------- Collaboration

class CollaborationRequest(Base):
    __tablename__ = "collaboration_requests"
    id = Column(String, primary_key=True, default=gen_id)
    title = Column(String, nullable=False)
    description = Column(Text)
    from_type = Column(String)   # "Industry", "Institution", "Faculty"
    from_id = Column(String)     # id of company / institution / faculty_profile
    to_type = Column(String)
    to_id = Column(String, nullable=True)
    status = Column(Enum(CollaborationStatus), default=CollaborationStatus.draft)
    participants_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class TrainingProgram(Base):
    __tablename__ = "training_programs"
    id = Column(String, primary_key=True, default=gen_id)
    institution_id = Column(String, ForeignKey("institutions.id"))
    skill_id = Column(String, ForeignKey("skills.id"))
    title = Column(String, nullable=False)
    duration_hours = Column(Integer)
    students_ready_before = Column(Integer, default=0)
    students_ready_projected = Column(Integer, default=0)
    status = Column(String, default="Proposed")


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(String, primary_key=True, default=gen_id)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    message = Column(String, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="notifications")


class VerificationRecord(Base):
    __tablename__ = "verification_records"
    id = Column(String, primary_key=True, default=gen_id)
    entity_type = Column(String)  # "StudentSkill", "Institution", "Company"
    entity_id = Column(String)
    verified_by = Column(String)  # user id of verifier (faculty/industry/admin)
    verified_at = Column(DateTime, default=datetime.utcnow)
    note = Column(String)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(String, primary_key=True, default=gen_id)
    actor_user_id = Column(String, ForeignKey("users.id"))
    action = Column(String, nullable=False)
    entity_type = Column(String)
    entity_id = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
