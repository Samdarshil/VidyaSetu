# VidyaSetu

**VidyaSetu is an evidence-driven academia–industry skill intelligence
platform for skill mapping, verification, internship discovery, and
placement readiness.**

Built for Smart India Hackathon 2026. Institutions and companies referenced
throughout are illustrative demo data, not real partnerships.

---

## Problem

A student's resume says "Python — Advanced." An institution's placement
office doesn't really know how ready its students are for the roles
industry is hiring for. Industry can't tell which colleges reliably
produce candidates with the specific skills a role needs. Three
stakeholders, three different pictures of the same reality — because
none of them are working from evidence, just claims.

## Solution

VidyaSetu replaces self-reported skill claims with an evidence pipeline:

```
Evidence (assessments, projects, GitHub, faculty evaluation)
        ↓
Skill Intelligence (competency + evidence confidence, computed, not typed in)
        ↓
Verification (claimed vs. evidence-backed, shown side by side)
        ↓
Gap Analysis (current profile vs. a target role's real requirements)
        ↓
Opportunity Matching (explainable — shows why a percentage exists)
        ↓
Action (assessment, project, application, institutional intervention)
```

## Who it serves

| Role | What they get |
|---|---|
| **Student** | A verified skill profile, gap analysis against a target role, a career-impact simulator, matched opportunities with explainable scores, and an application tracker. |
| **Faculty** | A view into their own institution's students' real skills, collaboration matching against their research interests, and industry consultancy/research opportunities. |
| **Institution** | A department × skill competency heatmap built from real student data, critical-gap detection, and an intervention simulator that models a training program's projected impact. |
| **Industry** | Candidate discovery ranked by real, explainable skill match, and a skill-demand radar comparing demand against verified academic supply. |

## What makes it technically meaningful

- **Competency scores are computed, not typed in.** Every skill's score
  and confidence are derived from weighted evidence rows
  (`app/engine.py:recompute_student_skill`) — add a real assessment
  result or a GitHub repo, and the number actually moves.
- **Matching is explainable.** Every match percentage comes with the
  matched and missing skills that produced it
  (`app/engine.py:match_opportunity`) — never a bare number.
- **Authorization is enforced at the API, not the UI.** A student's JWT
  gets a real `403` on an industry-only endpoint, regardless of what the
  frontend hides (`app/deps.py:require_role`).
- **Assessments are genuinely scored server-side.** The answer key never
  reaches the browser; a submitted result becomes real database evidence
  that recomputes the student's actual skill.
- **GitHub evidence is honest about what it proves.** Public-repo
  language detection becomes evidence a skill was *used*, explicitly
  weighted lower than a graded assessment — see
  [`docs/github-integration.md`](docs/github-integration.md).

## How the prototype works

```
Student
 ↓
Evidence
 ├── GitHub (public repos, client-side fetch, no OAuth secret needed)
 ├── Assessments (server-scored, real questions)
 ├── Projects / certifications
 └── Faculty evaluation
 ↓
SkillEvidence rows
 ↓
Competency Engine (app/engine.py)
 ↓
Skill Profile (competency + evidence confidence, explainable)
 ↓
Gap Analysis (vs. a target CareerRole)
 ↓
Opportunity Matching (vs. real Opportunity requirements)
 ↓
Career Action (assessment, application, institutional intervention)
```

## Architecture

See [`docs/architecture.md`](docs/architecture.md) for the full breakdown
with diagrams. In short:

**Frontend** — one self-contained `index.html` (no build step, no
framework) with a small `VS` API-bridge object handling every network
call, and a `DATA_SOURCE` flag that shows a plain 🟢 live / 🟡 demo
banner so nothing is ever silently faked as real.

**Backend** — FastAPI, organized as one router per resource area, with
all skill-intelligence and matching math isolated in `app/engine.py` so
it's shared correctly across routers and independently testable.

**Database** — PostgreSQL in production, SQLite as a zero-setup local
fallback, via SQLAlchemy.

**Auth** — JWT bearer tokens, bcrypt password hashing, role-based
authorization enforced server-side.

**AI layer** — a rule-based, explainable assistant ("Ask Vidya") grounded
only in the caller's real platform data — no external LLM call, so it
cannot invent a skill, score, or opportunity that doesn't exist in the
database.

**External integration** — GitHub's public REST API, called client-side,
for public-repository evidence import. See
[`docs/github-integration.md`](docs/github-integration.md).

## Technology stack

| Layer | Technology |
|---|---|
| Frontend | HTML, CSS, vanilla JavaScript (no framework, no build step) |
| Backend | Python 3, FastAPI, Uvicorn |
| ORM | SQLAlchemy |
| Validation | Pydantic / pydantic-settings |
| Auth | python-jose (JWT), passlib + bcrypt (password hashing) |
| Database | PostgreSQL (production), SQLite (local dev fallback) |
| Hosting | Vercel (frontend), Render (backend + PostgreSQL) — see individual READMEs for other providers |

No React, no Node.js backend, no Docker, no message queue. Kept
deliberately simple so it's realistic to run, explain, and debug under
hackathon time pressure, rather than an npm-dependency-heavy stack that
would be harder to deploy and reason about confidently.

## Repository structure

```
VidyaSetu/
├── README.md                  ← you are here
├── LICENSE
├── .gitignore
├── index.html                 ← the entire frontend (single file, see docs/architecture.md)
│
├── vidyasetu-backend/
│   ├── app/
│   │   ├── main.py             ← FastAPI app, router registration, CORS
│   │   ├── config.py           ← environment-variable settings
│   │   ├── database.py         ← SQLAlchemy engine/session
│   │   ├── security.py         ← password hashing, JWT
│   │   ├── deps.py             ← auth dependencies (get_current_user, require_role)
│   │   ├── engine.py           ← skill intelligence, matching, gap analysis, AI logic
│   │   ├── seed.py             ← demo data population
│   │   ├── models/models.py    ← SQLAlchemy models (full relational schema)
│   │   ├── schemas/schemas.py  ← Pydantic request/response schemas
│   │   └── routers/            ← one file per resource area (auth, skills, opportunities, ...)
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md               ← backend-specific run/deploy instructions
│
├── docs/
│   ├── architecture.md
│   ├── api.md
│   ├── demo-flow.md
│   └── github-integration.md
│
└── tests/
    └── test_engine.py          ← unit tests for the pure skill-intelligence functions
```

The frontend is intentionally a single file rather than split into
`frontend/js/`, `frontend/css/`, etc. — see the "Why a single-file
frontend" section of `docs/architecture.md` for the reasoning. This
structure reflects the actual, current project rather than an aspirational
one with empty placeholder folders.

## Assessment engine

- Questions are stored as JSON on the `Assessment` model
  (`app/models/models.py`), each with `id`, `text`, `options`, and a
  `correct_index` that is **stripped before ever being sent to a
  student** (`GET /assessments/{id}` only returns `id/text/options`).
- Scoring happens entirely server-side in
  `POST /assessments/{id}/submit` — the client sends selected option
  indices, the server compares them against the real answer key.
- The result is persisted as an `AssessmentResult` row **and** a
  `SkillEvidence` row, then `recompute_student_skill()` is called — a
  submitted assessment genuinely changes the student's stored competency
  and evidence confidence.

## GitHub integration

Public-repository analysis, no OAuth, no secrets. Full explanation,
including exactly what this evidence does and doesn't prove, and the
future OAuth upgrade path: [`docs/github-integration.md`](docs/github-integration.md).

## Skill Intelligence

A skill's `competency_score` is a weighted average across all its
`SkillEvidence` rows, where each evidence type carries a different weight
(`EVIDENCE_WEIGHTS` in `app/engine.py`) — an internship's real feedback
counts for more than a self-declared claim, for instance. `evidence_confidence`
grows with the amount and diversity of weighted evidence via a saturating
function, so a handful of strong, varied sources gets close to full
confidence without a single data point ever claiming certainty.

## Opportunity Matching

Each `Opportunity` declares its own weighted `OpportunitySkillRequirement`
rows. A candidate's match percentage is the weighted average of
`min(1, current_competency / required_level)` across those requirements
(`app/engine.py:match_opportunity`) — and the same function returns the
matched and missing skill lists that produced that number, so the UI
never shows an unexplained percentage.

## Ask Vidya

Rule-based and grounded only in data actually queried from VidyaSetu's
own database for the asking user — see `app/engine.py:ai_explain_answer`.
It does not call an external LLM in this build, and it cannot fabricate a
skill, score, company, or opportunity: if the underlying context is
empty (e.g. no target role set yet), it says so rather than inventing an
answer. `docs/api.md` documents the exact response contract if you want
to swap in a real LLM behind the same endpoint later.

## Security

- Passwords are hashed with bcrypt (`passlib`) — never stored in plain text.
- Sessions are stateless JWTs, signed with `JWT_SECRET_KEY` (must be set
  to a real random value in production — see `.env.example`).
- Authorization is enforced in `app/deps.py`, at the API layer, on every
  protected route — not just hidden in the frontend.
- CORS is restricted to the origins listed in `CORS_ORIGINS`.
- No secrets are hardcoded anywhere in this repository — everything
  sensitive is an environment variable, and `.gitignore` excludes `.env`,
  `*.db`, and `__pycache__`. See "Security check" below for what was
  actually scanned.
- GitHub integration never requests, stores, or transmits a GitHub
  token or password — see `docs/github-integration.md`.

## Running locally

### Backend
```bash
cd vidyasetu-backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                # defaults to a local SQLite file — no Postgres needed to try this
python -m app.seed                  # creates tables + demo data
uvicorn app.main:app --reload --port 8000
```
Visit `http://localhost:8000/docs` for interactive API docs.

### Frontend
No build step — it's one HTML file. Two ways to run it:
- Open `index.html` directly in a browser, or
- Serve it (recommended, avoids `file://` quirks): `python -m http.server 5500` from the repo root, then visit `http://localhost:5500`.

Before it can log in for real, open `index.html` and find this line near
the top of its `<script>` block:
```js
const API_BASE = "http://localhost:8000"; // change to your deployed backend URL
```
Point it at wherever your backend is running. Without this, the site
still works via "Skip — explore with static demo data."

## Environment variables

See `vidyasetu-backend/.env.example` for the full list with inline
explanations (`DATABASE_URL`, `JWT_SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES`,
`CORS_ORIGINS`). None of these are committed with real values anywhere in
this repository.

## Demo accounts

Password for every seeded account: `demo1234`

| Role | Email |
|---|---|
| Student | `aarav@student.demo` |
| Faculty | `kavita@faculty.demo` |
| Institution | `admin@manipal.demo` |
| Industry | `hr@razorpay.demo` |
| Admin | `admin@vidyasetu.demo` (seeded, but no admin-specific endpoints exist yet — see Known Limitations) |

Each is prefilled automatically when you pick that role on the frontend's
sign-in screen.

## API

Full reference with method, path, purpose, auth requirement, request
body, and response shape for every route: [`docs/api.md`](docs/api.md).

## Testing

- **Backend:** `python -m py_compile app/*.py app/models/*.py
  app/schemas/*.py app/routers/*.py` from `vidyasetu-backend/` — confirms
  every file is syntactically valid Python.
- **Frontend:** the inline `<script>` block has been extracted and
  checked with `node --check` — confirms valid JavaScript syntax.
- **Unit tests:** `tests/test_engine.py` covers the pure functions in the
  skill-intelligence engine (`compute_readiness`, `gap_status`,
  `match_opportunity`, `ai_explain_answer`) with real assertions against
  real logic — no database needed. Run with:
  ```bash
  pip install pytest
  cd vidyasetu-backend && pytest ../tests/test_engine.py -v
  ```
- **What has NOT been run:** this project was built and verified in an
  offline sandbox with no network access — so nothing here has been
  exercised against a live browser, a live PostgreSQL database, or a
  deployed instance. The syntax checks and unit tests above were run;
  full endpoint-by-endpoint and UI-click-by-click testing was not, and is
  called out explicitly rather than implied. Do a manual pass through
  `docs/demo-flow.md` yourself before presenting this live.

## SIH Demonstration Flow

Full step-by-step script: [`docs/demo-flow.md`](docs/demo-flow.md).

## Known Limitations

Stated plainly, not hidden:

- **Admin dashboard is fully mock.** An admin account exists in the seed
  data, but no admin-specific endpoints or authorization logic were
  built — admin screens show static data with no live actions.
- **GitHub integration is public-repo-only, no OAuth.** Explained in
  full, including why, in `docs/github-integration.md`.
- **This is prototype-scale data.** The seed script creates a handful of
  students, companies, and opportunities — enough to demonstrate every
  feature convincingly, not a production-scale dataset.
- **No automated integration or end-to-end tests.** Only the pure-logic
  unit tests described above exist; there is no test database or browser
  automation in this repository yet.
- **No migration framework.** Schema changes currently require dropping
  and reseeding (`python -m app.seed`, which calls `drop_all` first) —
  fine for active prototype development, not for a system with real user
  data to preserve.
- **JWTs don't expire until `ACCESS_TOKEN_EXPIRE_MINUTES` (default 24h)
  and there's no refresh-token flow** — acceptable for a demo, not for
  production.
- **No rate limiting.**
- A few UI elements are intentionally static/decorative rather than
  wired to a backend action that doesn't exist yet (the admin dashboard
  entirely, and some illustrative dashboard copy) — nothing claims to be
  live that isn't; see `vidyasetu-backend/README.md` for the specific,
  current list, since this list changes as more of the product gets wired.

## Future Scope

- Real GitHub OAuth (architecture already documented for a clean swap-in).
- Deeper repository analysis (commit history, code-quality signals) once
  OAuth is in place.
- Broader evidence sources: LinkedIn Learning / Coursera completions,
  hackathon participation records, verified internship completion
  certificates.
- Production-scale analytics (proper time-series tracking of readiness
  and demand trends, not point-in-time snapshots).
- Deeper institution integrations (SSO, roster import).
- Recruiter workflows: saved searches, structured shortlisting, interview
  scheduling.
- A real LLM behind Ask Vidya, grounded via the same `context` dict this
  build already constructs — see `docs/api.md`'s notes on the `/ai/ask`
  contract.
- Privacy/security hardening for real user data: rate limiting, refresh
  tokens, audit logging (the `AuditLog`/`VerificationRecord` tables
  already exist in the schema, unused).
