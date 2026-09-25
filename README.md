<div align="center">

# 🎓🌉🏭 VidyaSetu

### Bridging Academia & Industry — Evidence-Driven Skill Intelligence

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-4169E1?logo=postgresql&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-SIH%202026%20Prototype-orange)

**VidyaSetu replaces self-reported skill claims with real, evidence-backed skill intelligence — connecting students, faculty, institutions, and industry around what students can actually demonstrate, not just what they claim.**

Built for Smart India Hackathon 2026. Institutions and companies referenced throughout are illustrative demo data, not real partnerships.

[Problem](#-the-problem) · [Solution](#-the-solution) · [Features](#-what-makes-it-technically-meaningful) · [Quick Start](#-quick-start) · [Architecture](#%EF%B8%8F-architecture) · [API Docs](#-api) · [Demo](#-sih-demonstration-flow) · [Limitations](#%EF%B8%8F-known-limitations)

</div>

---

## 🧩 The Problem

A student's resume says *"Python — Advanced."* An institution's placement office doesn't really know how ready its students are for the roles industry is hiring for. Industry can't tell which colleges reliably produce candidates with the specific skills a role needs.

Three stakeholders. Three different pictures of the same reality — because none of them are working from **evidence**, just **claims**.

## 💡 The Solution

VidyaSetu replaces self-reported skill claims with a real evidence pipeline:

```
📂 Evidence  (assessments, projects, GitHub, faculty evaluation)
        ↓
🧠 Skill Intelligence  (competency + confidence — computed, not typed in)
        ↓
✅ Verification  (claimed vs. evidence-backed, shown side by side)
        ↓
🎯 Gap Analysis  (current profile vs. a target role's real requirements)
        ↓
🔍 Opportunity Matching  (explainable — shows *why* a percentage exists)
        ↓
🚀 Action  (assessment, project, application, institutional intervention)
```

## 👥 Who It Serves

| Role | What they get |
|---|---|
| 🎓 **Student** | A verified skill profile, gap analysis against a target role, a career-impact simulator, matched opportunities with explainable scores, and an application tracker. |
| 🧑‍🏫 **Faculty** | A real view into their own institution's students' skills, collaboration matching against research interests, and industry consultancy/research opportunities. |
| 🏛️ **Institution** | A department × skill competency heatmap built from real student data, critical-gap detection, and an intervention simulator that models a training program's projected impact. |
| 🏭 **Industry** | Candidate discovery ranked by real, explainable skill match, and a skill-demand radar comparing demand against verified academic supply. |

---

## ⚡ What Makes It Technically Meaningful

- 🧮 **Competency scores are computed, not typed in.** Every skill's score and confidence are derived from weighted evidence rows (`app/engine.py:recompute_student_skill`) — add a real assessment result or a GitHub repo, and the number actually moves.
- 🔎 **Matching is explainable.** Every match percentage comes with the matched and missing skills that produced it (`app/engine.py:match_opportunity`) — never a bare number.
- 🔐 **Authorization is enforced at the API, not the UI.** A student's JWT gets a real `403` on an industry-only endpoint, regardless of what the frontend hides (`app/deps.py:require_role`).
- 📝 **Assessments are genuinely scored server-side.** The answer key never reaches the browser; a submitted result becomes real database evidence that recomputes the student's actual skill.
- 🐙 **GitHub evidence is honest about what it proves.** Public-repo language detection becomes evidence a skill was *used*, explicitly weighted lower than a graded assessment — see [`docs/github-integration.md`](docs/github-integration.md).

---

## 🚀 Quick Start

```bash
# 1. Backend
cd vidyasetu-backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python -m app.seed                  # creates tables + demo data
uvicorn app.main:app --reload --port 8000

# 2. Frontend (new terminal, from repo root)
python -m http.server 5500
```

Open `http://localhost:5500`, sign in with any seeded demo account (password `demo1234` — see [Demo Accounts](#-demo-accounts)), and explore. Full setup details in [Running Locally](#%EF%B8%8F-running-locally) below.

---

## 🔄 How the Prototype Works

```
                         Student
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
   🐙 GitHub           📝 Assessments      📁 Projects /
   (public repos,      (server-scored,      certifications
    no OAuth needed)    real questions)
        │                   │                   │
        └───────────────────┼───────────────────┘
                            ▼
                   SkillEvidence rows
                            │
                            ▼
                🧠 Competency Engine (app/engine.py)
                            │
                            ▼
             Skill Profile (competency + confidence)
                            │
                            ▼
              🎯 Gap Analysis  (vs. a target CareerRole)
                            │
                            ▼
           🔍 Opportunity Matching  (vs. real requirements)
                            │
                            ▼
     🚀 Career Action (assessment · application · institutional intervention)
```

---

## 🏗️ Architecture

Full breakdown with diagrams: [`docs/architecture.md`](docs/architecture.md).

| Layer | What it is |
|---|---|
| 🖥️ **Frontend** | One self-contained `index.html` — no build step, no framework. A small `VS` API-bridge object handles every network call, and a `DATA_SOURCE` flag shows a plain 🟢 live / 🟡 demo banner so nothing is ever silently faked as real. |
| ⚙️ **Backend** | FastAPI, one router per resource area. All skill-intelligence and matching math lives in `app/engine.py` so it's shared correctly and independently testable. |
| 🗄️ **Database** | PostgreSQL in production, SQLite as a zero-setup local fallback, via SQLAlchemy. |
| 🔑 **Auth** | JWT bearer tokens, bcrypt password hashing, role-based authorization enforced server-side. |
| 🤖 **AI layer** | A rule-based, explainable assistant (**Ask Vidya**) grounded only in the caller's real platform data — no external LLM call, so it cannot invent a skill, score, or opportunity. |
| 🐙 **External integration** | GitHub's public REST API, called client-side, for public-repository evidence import. |

## 🧰 Technology Stack

| Layer | Technology |
|---|---|
| Frontend | HTML, CSS, vanilla JavaScript — no framework, no build step |
| Backend | Python 3, FastAPI, Uvicorn |
| ORM | SQLAlchemy |
| Validation | Pydantic / pydantic-settings |
| Auth | python-jose (JWT), passlib + bcrypt |
| Database | PostgreSQL (prod), SQLite (local dev fallback) |
| Hosting | Vercel (frontend) · Render (backend + PostgreSQL) |

> No React, no Node.js backend, no Docker, no message queue — kept deliberately simple so it's realistic to run, explain, and debug under hackathon time pressure.

## 📁 Repository Structure

```
VidyaSetu/
├── 📄 README.md                  ← you are here
├── 📄 LICENSE
├── 📄 .gitignore
├── 🖥️ index.html                 ← the entire frontend (single file — see docs/architecture.md)
│
├── ⚙️ vidyasetu-backend/
│   ├── app/
│   │   ├── main.py               ← FastAPI app, router registration, CORS
│   │   ├── config.py             ← environment-variable settings
│   │   ├── database.py           ← SQLAlchemy engine/session
│   │   ├── security.py           ← password hashing, JWT
│   │   ├── deps.py               ← auth dependencies (get_current_user, require_role)
│   │   ├── engine.py             ← skill intelligence, matching, gap analysis, AI logic
│   │   ├── seed.py               ← demo data population
│   │   ├── models/models.py      ← SQLAlchemy models (full relational schema)
│   │   ├── schemas/schemas.py    ← Pydantic request/response schemas
│   │   └── routers/              ← one file per resource area
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md                 ← backend-specific run/deploy instructions
│
├── 📚 docs/
│   ├── architecture.md
│   ├── api.md
│   ├── demo-flow.md
│   └── github-integration.md
│
└── 🧪 tests/
    └── test_engine.py            ← unit tests for the skill-intelligence engine
```

<details>
<summary>💬 Why is the frontend one big file instead of split up?</summary>

<br>

It's intentional, not an oversight — see "Why a single-file frontend" in [`docs/architecture.md`](docs/architecture.md). Short version: no build step, trivial to deploy anywhere, trivial to review, and a framework's benefits don't yet outweigh the tooling overhead at this scale. The `VS` bridge object already isolates every network call behind named functions, so splitting it up later is a mechanical refactor, not a rewrite.

</details>

---

## 📝 Assessment Engine

- Questions are stored as JSON on the `Assessment` model, each with `id`, `text`, `options`, and a `correct_index` that is **stripped before ever being sent to a student**.
- Scoring happens **entirely server-side** — the client sends selected option indices, the server compares them against the real answer key.
- The result is persisted as an `AssessmentResult` **and** a `SkillEvidence` row, then the competency engine recomputes the student's real score. A submitted assessment genuinely changes stored state.

## 🐙 GitHub Integration

**Public-repository analysis. No OAuth. No secrets.**

Full explanation of exactly what this evidence does and doesn't prove, plus the future OAuth upgrade path: [`docs/github-integration.md`](docs/github-integration.md).

## 🧠 Skill Intelligence

A skill's competency score is a **weighted average** across all its evidence rows — an internship's real feedback counts for more than a self-declared claim. Evidence confidence grows with the amount and diversity of evidence via a saturating function, so a handful of strong, varied sources gets close to full confidence without ever claiming certainty.

## 🔍 Opportunity Matching

Each opportunity declares weighted skill requirements. A candidate's match percentage is the weighted average of `min(1, current_competency / required_level)` across those requirements — and the **same calculation** returns the matched/missing skill lists that explain the number. No unexplained percentages, anywhere.

## 🤖 Ask Vidya

Rule-based, grounded only in the asking user's real platform data. No external LLM call, so it **cannot fabricate** a skill, score, company, or opportunity — if the underlying context is empty, it says so rather than inventing an answer.

---

## 🔒 Security

- ✅ Passwords hashed with bcrypt — never stored in plain text
- ✅ Stateless JWTs, signed with a configurable secret
- ✅ Authorization enforced server-side on every protected route
- ✅ CORS restricted to explicitly configured origins
- ✅ No secrets hardcoded anywhere — `.gitignore` excludes `.env`, `*.db`, `__pycache__`
- ✅ GitHub integration never requests, stores, or transmits a token or password

## 🖥️ Running Locally

### Backend
```bash
cd vidyasetu-backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                # defaults to local SQLite — no Postgres needed to try this
python -m app.seed                  # creates tables + demo data
uvicorn app.main:app --reload --port 8000
```
Interactive API docs: `http://localhost:8000/docs`

### Frontend
No build step — it's one HTML file.
```bash
python -m http.server 5500   # from the repo root
```
Then update this line near the top of `index.html`'s `<script>` block to point at your backend:
```js
const API_BASE = "http://localhost:8000"; // change to your deployed backend URL
```
Without this, the site still works via **"Skip — explore with static demo data."**

## 🔑 Environment Variables

See [`vidyasetu-backend/.env.example`](vidyasetu-backend/.env.example) for the full list with inline explanations. None are committed with real values anywhere in this repository.

## 👤 Demo Accounts

Password for every seeded account: **`demo1234`**

| Role | Email |
|---|---|
| 🎓 Student | `aarav@student.demo` |
| 🧑‍🏫 Faculty | `kavita@faculty.demo` |
| 🏛️ Institution | `admin@manipal.demo` |
| 🏭 Industry | `hr@razorpay.demo` |
| ⚙️ Admin | `admin@vidyasetu.demo` *(seeded, but no admin-specific endpoints exist yet)* |

Each is prefilled automatically when you pick that role on the sign-in screen.

## 📡 API

Full reference — method, path, purpose, auth requirement, request body, response shape — for every route: [`docs/api.md`](docs/api.md).

## 🧪 Testing

| Check | Status |
|---|---|
| Backend syntax (`py_compile`) | ✅ Passing |
| Frontend syntax (`node --check`) | ✅ Passing |
| Engine unit tests (`tests/test_engine.py`) | ✅ Passing |
| Live browser / live Postgres / deployed instance | ⚠️ **Not run** — see below |

```bash
pip install pytest
cd vidyasetu-backend && pytest ../tests/test_engine.py -v
```

> **Honesty note:** this project was built and verified in an offline sandbox with no network access. The checks above were genuinely run; nothing has been exercised against a live browser, a live database, or a deployed instance. Do a manual pass through [`docs/demo-flow.md`](docs/demo-flow.md) yourself before presenting this live.

## 🎬 SIH Demonstration Flow

Full step-by-step script: [`docs/demo-flow.md`](docs/demo-flow.md)

```
Landing → Student → Login → Dashboard → Connect GitHub → Skill Profile
   → Take Assessment → Score & Evidence Update → Skill Gap → Opportunity
   → Why This Match? → Ask Vidya → Apply → Industry → Institution → Faculty
```

---

## ⚠️ Known Limitations

Stated plainly, not hidden:

- 🚫 **Admin dashboard is fully mock** — no admin-specific endpoints or authorization logic were built.
- 🐙 **GitHub is public-repo-only, no OAuth** — explained in full in `docs/github-integration.md`.
- 📊 **Prototype-scale data** — enough to demonstrate every feature convincingly, not production-scale.
- 🧪 **No automated integration or end-to-end tests** — only the pure-logic unit tests exist.
- 🔄 **No migration framework** — schema changes require dropping and reseeding.
- ⏳ **JWTs don't expire until 24h by default, no refresh-token flow.**
- 🚦 **No rate limiting.**
- 🎭 A few UI elements are intentionally static rather than wired to a backend action that doesn't exist yet — nothing claims to be live that isn't; see `vidyasetu-backend/README.md` for the current specific list.

<details>
<summary>🔮 Future Scope</summary>

<br>

- Real GitHub OAuth (architecture already documented for a clean swap-in)
- Deeper repository analysis (commit history, code-quality signals) once OAuth is in place
- Broader evidence sources: LinkedIn Learning / Coursera completions, hackathon records, verified internship certificates
- Production-scale analytics with proper time-series tracking
- Deeper institution integrations (SSO, roster import)
- Recruiter workflows: saved searches, structured shortlisting, interview scheduling
- A real LLM behind Ask Vidya, grounded via the same context structure this build already constructs
- Privacy/security hardening: rate limiting, refresh tokens, audit logging (schema already exists, unused)

</details>

---

<div align="center">

Built for **Smart India Hackathon 2026** · Licensed under [MIT](LICENSE)

</div>
