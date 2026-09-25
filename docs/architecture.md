# Architecture

## System overview

```
                         ┌──────────────────────┐
                         │   Browser (Student,   │
                         │ Faculty, Institution,  │
                         │   Industry, Admin)     │
                         └───────────┬────────────┘
                                     │ HTTPS (fetch)
                                     ▼
                         ┌──────────────────────┐
                         │   index.html          │
                         │   (single-file        │
                         │    frontend, no       │
                         │    build step)        │
                         └───────────┬────────────┘
                                     │ JSON over REST
                                     │ (Bearer JWT)
                                     ▼
                         ┌──────────────────────┐
                         │     FastAPI app       │
                         │  (vidyasetu-backend)  │
                         └───────────┬────────────┘
                                     │ SQLAlchemy ORM
                                     ▼
                         ┌──────────────────────┐
                         │     PostgreSQL        │
                         │  (SQLite for local    │
                         │   dev fallback)        │
                         └──────────────────────┘
```

## Evidence → skill → opportunity pipeline

This is the core product loop, and it maps directly onto real code —
nothing in this diagram is aspirational:

```
                 ┌───────────────┐
                 │    Student     │
                 └───────┬───────┘
                         │
          ┌──────────────┼───────────────┐
          ▼              ▼               ▼
   GitHub (public)   Assessment      Project /
   repos, via         (server-       Certification
   GitHub's public    scored)         evidence
   API, client-side        │               │
          │              │               │
          └──────────────┼───────────────┘
                         ▼
              SkillEvidence rows
           (app/models/models.py)
                         │
                         ▼
         recompute_student_skill()
            (app/engine.py)
                         │
          ┌──────────────┴──────────────┐
          ▼                             ▼
   competency_score               evidence_confidence
   (weighted avg of               (saturating function
    evidence contributions)        of accumulated
                                    weighted evidence)
                         │
                         ▼
              ┌──────────┴──────────┐
              ▼                     ▼
         gap_analysis()      match_opportunity()
      (vs. a CareerRole's   (vs. an Opportunity's
       required_skills)      skill_requirements)
              │                     │
              ▼                     ▼
        Readiness %          Match % + matched/
        + roadmap             missing skill lists
```

## Layers, and what each owns

| Layer | Location | Responsibility |
|---|---|---|
| Presentation | `index.html` | Renders all five role dashboards from either live API data or the original static demo objects (`DATA`, `OPPORTUNITIES`, etc.), depending on `DATA_SOURCE.mode`. |
| API routing | `app/routers/*.py` | One file per resource area (auth, skills, opportunities, applications, industry, institutions, faculty, collaboration, notifications, ai, assessments). Each route declares its own role requirement via `require_role(...)`. |
| Domain logic | `app/engine.py` | The skill-intelligence, gap-analysis, matching, and rule-based AI logic. Deliberately kept separate from routers so it's independently testable (see `tests/test_engine.py`) and so no router duplicates this math. |
| Data access | `app/models/models.py`, `app/database.py` | SQLAlchemy models and the engine/session setup. One `Base.metadata.create_all()` call in `main.py` creates the schema — no migration framework, appropriate for a prototype of this scale. |
| Auth | `app/security.py`, `app/deps.py` | Password hashing (bcrypt via passlib), JWT issuance/verification, and the `get_current_user` / `require_role` dependencies every protected route uses. Authorization is enforced here, at the API layer — never only by the frontend hiding a button. |
| Config | `app/config.py` | Environment-variable-driven settings (`DATABASE_URL`, `JWT_SECRET_KEY`, `CORS_ORIGINS`, etc.) via `pydantic-settings`. |
| Seed data | `app/seed.py` | Drops and recreates all tables, then populates realistic Indian demo data (institutions, companies, skills, career roles, students, opportunities, assessments, collaborations) so the same schema can back both a live demo and further development. |

## Why a single-file frontend

The frontend is intentionally one `index.html` with inline CSS and
JavaScript — no build step, no bundler, no framework. This was a
deliberate choice carried through every pass of this project rather than
an oversight: it's trivial to deploy (any static host works), trivial to
diff and review, and for a UI this size (five dashboards, one shared
design system) a framework's benefits don't yet outweigh the added
tooling surface. If the project grows past this scale, the natural next
step is extracting the render functions into ES modules without changing
the underlying API contract — the `VS` bridge object at the top of
`index.html`'s `<script>` block already isolates every network call
behind a small set of named functions for exactly this reason.

## Authentication & authorization flow

```
POST /auth/register or /auth/login
        │
        ▼
 bcrypt password check  →  JWT issued (subject = user id, claim = role)
        │
        ▼
 Browser stores token in localStorage, attaches as
 `Authorization: Bearer <token>` on every subsequent request
        │
        ▼
 get_current_user() resolves the token to a real User row on every request
        │
        ▼
 require_role("industry", "admin") rejects with 403 if the
 authenticated user's role isn't in the allowed set —
 this check happens on the SERVER, so a student's token can never
 successfully call an industry-only endpoint, regardless of what
 the frontend shows or hides.
```

## What's explicitly out of scope in this architecture

- No message queue, caching layer, or background job runner — none of
  the current features need one at this scale.
- No migration framework (Alembic, etc.) — `create_all()` plus a
  from-scratch seed script is simpler and sufficient while the schema is
  still actively changing.
- No admin-specific service layer — the admin role exists in the schema
  (see `seed.py`) but has no dedicated endpoints yet; see the root
  README's "Known Limitations" section.
