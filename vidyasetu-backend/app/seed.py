"""
Seeds the database with realistic demo data — the same institutions,
companies, and numbers the existing static frontend already displays, so
switching the frontend from hardcoded DATA to real API calls doesn't change
what the demo looks like.

Run with:  python -m app.seed
Safe to re-run: it clears and recreates all tables first.
"""
from datetime import datetime, timedelta

from app.database import Base, engine, SessionLocal
from app.models import models as m
from app.security import hash_password
from app.engine import recompute_student_skill

DEMO_PASSWORD = "demo1234"  # every seeded account uses this password


def run():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # ---------------- Institutions & departments ----------------
    manipal = m.Institution(name="Manipal University Jaipur", city="Jaipur", state="Rajasthan", institution_type="Private University")
    bits = m.Institution(name="BITS Pilani", city="Pilani", state="Rajasthan", institution_type="Deemed University")
    iit_jaipur = m.Institution(name="IIT Jaipur", city="Jaipur", state="Rajasthan", institution_type="IIT")
    amity = m.Institution(name="Amity University", city="Jaipur", state="Rajasthan", institution_type="Private University")
    db.add_all([manipal, bits, iit_jaipur, amity])
    db.flush()

    cse_manipal = m.Department(name="Computer Science", institution_id=manipal.id)
    aids_manipal = m.Department(name="AI & Data Science", institution_id=manipal.id)
    ece_manipal = m.Department(name="Electronics", institution_id=manipal.id)
    mech_manipal = m.Department(name="Mechanical", institution_id=manipal.id)
    cse_bits = m.Department(name="Computer Science", institution_id=bits.id)
    db.add_all([cse_manipal, aids_manipal, ece_manipal, mech_manipal, cse_bits])
    db.flush()

    # ---------------- Companies ----------------
    razorpay_user = m.User(email="hr@razorpay.demo", hashed_password=hash_password(DEMO_PASSWORD),
                            role=m.RoleEnum.industry, full_name="Razorpay Talent Team")
    zoho_user = m.User(email="hr@zoho.demo", hashed_password=hash_password(DEMO_PASSWORD),
                        role=m.RoleEnum.industry, full_name="Zoho Corporation Talent Team")
    tcs_user = m.User(email="hr@tcs.demo", hashed_password=hash_password(DEMO_PASSWORD),
                       role=m.RoleEnum.industry, full_name="TCS Talent Team")
    db.add_all([razorpay_user, zoho_user, tcs_user])
    db.flush()

    razorpay = m.Company(name="Razorpay", industry_domain="Fintech", city="Bengaluru", user_id=razorpay_user.id)
    zoho = m.Company(name="Zoho Corporation", industry_domain="SaaS", city="Chennai", user_id=zoho_user.id)
    tcs = m.Company(name="TCS", industry_domain="IT Services", city="Mumbai", user_id=tcs_user.id)
    infosys = m.Company(name="Infosys", industry_domain="IT Services", city="Bengaluru")
    wipro = m.Company(name="Wipro", industry_domain="IT Services", city="Bengaluru")
    db.add_all([razorpay, zoho, tcs, infosys, wipro])
    db.flush()

    # ---------------- Skills (with industry demand scores) ----------------
    def skill(name, demand):
        s = m.Skill(name=name, industry_demand_score=demand)
        db.add(s)
        return s

    python = skill("Python", 92)
    ml = skill("Machine Learning", 88)
    sql = skill("SQL", 80)
    docker = skill("Docker", 78)
    mlops = skill("MLOps", 90)
    react = skill("React", 65)
    ds = skill("Data Structures", 75)
    aws = skill("AWS", 82)
    kubernetes = skill("Kubernetes", 70)
    typescript = skill("TypeScript", 60)
    powerbi = skill("Power BI", 55)
    statistics = skill("Statistics", 60)
    db.flush()

    # ---------------- Career roles ----------------
    ai_ml_role = m.CareerRole(title="AI/ML Engineer")
    fullstack_role = m.CareerRole(title="Full-Stack Developer")
    cloud_role = m.CareerRole(title="Cloud Engineer")
    db.add_all([ai_ml_role, fullstack_role, cloud_role])
    db.flush()

    def req(role, skill_obj, level):
        db.add(m.CareerRoleSkill(career_role_id=role.id, skill_id=skill_obj.id, required_level=level))

    req(ai_ml_role, python, 90); req(ai_ml_role, ml, 85); req(ai_ml_role, sql, 70)
    req(ai_ml_role, docker, 75); req(ai_ml_role, mlops, 80)
    req(fullstack_role, react, 70); req(fullstack_role, ds, 88); req(fullstack_role, sql, 65); req(fullstack_role, docker, 60)
    req(cloud_role, python, 70); req(cloud_role, docker, 80); req(cloud_role, aws, 85); req(cloud_role, kubernetes, 75)
    db.flush()

    # ---------------- Student: Aarav Sharma ----------------
    aarav_user = m.User(email="aarav@student.demo", hashed_password=hash_password(DEMO_PASSWORD),
                         role=m.RoleEnum.student, full_name="Aarav Sharma")
    db.add(aarav_user)
    db.flush()
    aarav = m.StudentProfile(
        user_id=aarav_user.id, institution_id=manipal.id, department_id=cse_manipal.id,
        program="B.Tech CSE", year_of_study=3, cgpa=8.4, target_career_role_id=ai_ml_role.id,
    )
    db.add(aarav)
    db.flush()

    def give_skill(student, skill_obj, evidences):
        """evidences: list of (type, score_contribution, note)"""
        ss = m.StudentSkill(student_id=student.id, skill_id=skill_obj.id)
        db.add(ss)
        db.flush()
        for etype, score, note in evidences:
            db.add(m.SkillEvidence(student_skill_id=ss.id, evidence_type=etype, score_contribution=score, source_note=note))
        db.flush()
        recompute_student_skill(db, ss)
        return ss

    give_skill(aarav, python, [
        ("Technical Assessment", 86, "Python Fundamentals Assessment"),
        ("Practical Challenge", 84, "Debugging & Edge Case Challenge"),
        ("Project", 82, "Crop Yield Prediction (scikit-learn)"),
        ("Internship Feedback", 85, "Infosys assessment panel, Aug"),
    ])
    give_skill(aarav, ml, [
        ("Technical Assessment", 60, "ML Fundamentals Assessment"),
        ("Project", 63, "Crop Yield Prediction project"),
    ])
    give_skill(aarav, sql, [
        ("Practical Challenge", 74, "Advanced Queries Challenge"),
        ("Certification", 68, "SQL Certification, Coursera"),
    ])
    give_skill(aarav, docker, [
        ("Self-declared", 34, "Self-reported on profile setup"),
    ])
    give_skill(aarav, mlops, [
        ("Self-declared", 18, "Self-reported on profile setup"),
    ])
    give_skill(aarav, ds, [
        ("Technical Assessment", 90, "Data Structures Assessment"),
        ("Practical Challenge", 88, "Algorithms Challenge"),
        ("Project", 85, "Pathfinding visualizer"),
    ])
    give_skill(aarav, react, [
        ("Project", 72, "Portfolio site"),
        ("Certification", 66, "React certification"),
    ])
    db.commit()

    # ---------------- Faculty: Dr. Kavita Sharma ----------------
    kavita_user = m.User(email="kavita@faculty.demo", hashed_password=hash_password(DEMO_PASSWORD),
                          role=m.RoleEnum.faculty, full_name="Dr. Kavita Sharma")
    db.add(kavita_user)
    db.flush()
    db.add(m.FacultyProfile(
        user_id=kavita_user.id, institution_id=bits.id, department_id=cse_bits.id,
        research_interests="Medical AI,Deep Learning,Computer Vision", available_for_consultancy=True,
    ))

    # ---------------- Institution account: Manipal University Jaipur ----------------
    manipal_user = m.User(email="admin@manipal.demo", hashed_password=hash_password(DEMO_PASSWORD),
                           role=m.RoleEnum.institution, full_name="Manipal University Jaipur")
    db.add(manipal_user)

    # ---------------- Admin ----------------
    admin_user = m.User(email="admin@vidyasetu.demo", hashed_password=hash_password(DEMO_PASSWORD),
                         role=m.RoleEnum.admin, full_name="Platform Admin")
    db.add(admin_user)
    db.commit()

    # ---------------- A few more students, spread across departments, for heatmaps ----------------
    import random
    random.seed(42)
    names = ["Priya Menon", "Rohan Verma", "Sneha Reddy", "Kabir Mehta", "Ishita Rao", "Vivaan Gupta"]
    depts = [cse_manipal, aids_manipal, ece_manipal, mech_manipal]
    for i, name in enumerate(names):
        email = name.lower().replace(" ", ".") + "@student.demo"
        u = m.User(email=email, hashed_password=hash_password(DEMO_PASSWORD), role=m.RoleEnum.student, full_name=name)
        db.add(u)
        db.flush()
        dept = depts[i % len(depts)]
        sp = m.StudentProfile(user_id=u.id, institution_id=manipal.id, department_id=dept.id,
                               program="B.Tech", year_of_study=random.choice([2, 3, 4]),
                               cgpa=round(random.uniform(6.5, 9.2), 1))
        db.add(sp)
        db.flush()
        for sk in [python, ml, sql, docker, mlops]:
            base = random.randint(15, 85)
            give_skill(sp, sk, [("Technical Assessment", base, "Seeded demo assessment")])
    db.commit()

    # ---------------- Opportunities ----------------
    def make_opp(company, title, otype, loc, mode, comp, reqs):
        o = m.Opportunity(company_id=company.id, title=title, opportunity_type=otype,
                           location=loc, work_mode=mode, compensation=comp)
        db.add(o)
        db.flush()
        for sk, level, weight in reqs:
            db.add(m.OpportunitySkillRequirement(opportunity_id=o.id, skill_id=sk.id, required_level=level, weight=weight))
        return o

    make_opp(zoho, "AI/ML Engineering Intern", m.OpportunityType.internship, "Chennai, TN", "Hybrid", "₹35,000/mo",
              [(python, 75, 1.2), (ml, 60, 1.2), (sql, 60, 0.8), (docker, 50, 1.0)])
    make_opp(razorpay, "Backend Developer (Node.js)", m.OpportunityType.job, "Bengaluru, KA", "On-site", "₹9-14 LPA",
              [(sql, 65, 1.0), (ds, 70, 1.0), (docker, 55, 0.8), (kubernetes, 40, 0.6)])
    make_opp(tcs, "Data Analyst — Winter Program", m.OpportunityType.internship, "Remote", "Remote", "₹20,000/mo",
              [(python, 60, 1.0), (sql, 65, 1.2), (powerbi, 40, 0.8), (statistics, 50, 0.8)])
    make_opp(infosys, "Cloud Infrastructure Project", m.OpportunityType.project, "Pune, MH", "Hybrid", "Certificate + Stipend",
              [(python, 50, 0.8), (aws, 55, 1.2), (docker, 60, 1.2), (mlops, 40, 1.0)])
    make_opp(wipro, "Frontend Engineer Trainee", m.OpportunityType.job, "Jaipur, RJ", "On-site", "₹6-8 LPA",
              [(react, 65, 1.2), (ds, 70, 1.0), (typescript, 40, 0.8)])
    db.commit()

    # ---------------- Collaboration requests ----------------
    db.add_all([
        m.CollaborationRequest(title="Computer Vision Project — 20 student positions", description="Looking for 20 students for a Computer Vision project.",
                                from_type="Industry", from_id=razorpay.id, to_type="Institution",
                                status=m.CollaborationStatus.requested),
        m.CollaborationRequest(title="47 students with verified AI skills available", description="Our AI department has 47 students with verified relevant skills.",
                                from_type="Institution", from_id=manipal.id, to_type="Industry",
                                status=m.CollaborationStatus.active, participants_count=47),
        m.CollaborationRequest(title="Research collaboration in Medical AI", description="Available for research collaboration in Medical AI.",
                                from_type="Faculty", from_id=kavita_user.id, to_type="Industry",
                                status=m.CollaborationStatus.under_review, participants_count=2),
        m.CollaborationRequest(title="40-hour MLOps industry training cohort", description="Proposed MLOps industry training for Manipal students.",
                                from_type="Industry", from_id=infosys.id, to_type="Institution",
                                status=m.CollaborationStatus.accepted, participants_count=86),
    ])
    db.commit()
    db.close()
    print("Seed complete. Demo login password for every account:", DEMO_PASSWORD)
    print("Try: aarav@student.demo / kavita@faculty.demo / admin@manipal.demo / hr@razorpay.demo / admin@vidyasetu.demo")


if __name__ == "__main__":
    run()
