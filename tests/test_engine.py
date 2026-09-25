"""
Unit tests for app/engine.py — specifically the pure functions that don't
require a database session or network access, so they can run in any
environment with just `pip install pytest` and the backend's own
requirements.

Run with:  cd vidyasetu-backend && pytest ../tests/test_engine.py -v

NOTE ON SCOPE: recompute_student_skill() and gap_analysis() are not
covered here because they require a live SQLAlchemy session and ORM
objects backed by a real database — testing them meaningfully needs an
integration test with a test database, which is listed as future work
in the main README's Testing section rather than faked here.
"""
import sys
import os
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "vidyasetu-backend"))

from app.engine import compute_readiness, gap_status, match_opportunity, ai_explain_answer  # noqa: E402


def test_gap_status_strong():
    assert gap_status(current=90, required=80) == "strong"


def test_gap_status_developing():
    assert gap_status(current=55, required=80) == "developing"  # 55 >= 80*0.6=48


def test_gap_status_critical():
    assert gap_status(current=20, required=80) == "critical"  # 20 < 48


def test_compute_readiness_full_coverage():
    current = {"Python": 90, "SQL": 85}
    required = {"Python": 80, "SQL": 70}
    # Both skills exceed requirement, so each contributes 1.0 -> 100% readiness
    assert compute_readiness(current, required) == 100.0


def test_compute_readiness_partial_coverage():
    current = {"Python": 40}
    required = {"Python": 80}
    # 40/80 = 0.5 coverage on the only required skill
    assert compute_readiness(current, required) == 50.0


def test_compute_readiness_missing_skill_caps_score():
    # A student missing one of two required skills entirely cannot exceed
    # 50% readiness, even with a perfect score on the other — this is the
    # "can't exceed 80% missing one of five skills" property from the
    # engine's own docstring, checked here with two skills for simplicity.
    current = {"Python": 100}
    required = {"Python": 80, "Docker": 80}
    assert compute_readiness(current, required) == 50.0


def _mock_requirement(skill_name, required_level, weight=1.0):
    return SimpleNamespace(
        skill=SimpleNamespace(name=skill_name),
        required_level=required_level,
        weight=weight,
    )


def test_match_opportunity_full_match():
    student_skills = {"Python": 90, "SQL": 85}
    opportunity = SimpleNamespace(skill_requirements=[
        _mock_requirement("Python", 80),
        _mock_requirement("SQL", 70),
    ])
    result = match_opportunity(student_skills, opportunity)
    assert result["match_percent"] == 100.0
    assert set(result["matched_skills"]) == {"Python", "SQL"}
    assert result["missing_skills"] == []


def test_match_opportunity_partial_match_reports_missing_skill():
    student_skills = {"Python": 90, "Docker": 20}
    opportunity = SimpleNamespace(skill_requirements=[
        _mock_requirement("Python", 80, weight=1.0),
        _mock_requirement("Docker", 75, weight=1.0),
    ])
    result = match_opportunity(student_skills, opportunity)
    assert "Python" in result["matched_skills"]
    assert "Docker" in result["missing_skills"]
    assert 0 < result["match_percent"] < 100


def test_match_opportunity_no_requirements_returns_zero():
    result = match_opportunity({"Python": 90}, SimpleNamespace(skill_requirements=[]))
    assert result["match_percent"] == 0.0


def test_ai_explain_answer_student_learn_next_grounds_in_context():
    context = {"top_gap": {"skill_name": "Docker", "current_score": 30, "required_level": 80}}
    result = ai_explain_answer("student", "what should I learn next?", context)
    assert "Docker" in result["answer"]
    assert len(result["reasons"]) > 0
    assert result["source"] == "VidyaSetu Platform Data"


def test_ai_explain_answer_never_invents_a_gap_with_empty_context():
    result = ai_explain_answer("student", "what should I learn next?", {})
    # With no target role / gap data available, the assistant must say so
    # rather than inventing a skill to recommend.
    assert "target career role" in result["answer"].lower()
