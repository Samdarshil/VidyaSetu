# VidyaSetu API

Real backend for VidyaSetu: FastAPI + SQLAlchemy + PostgreSQL, JWT auth,
role-based authorization, and an explainable skill-intelligence / matching
engine. Built to sit behind the existing static `index.html` frontend
without changing its visual identity.

> **Honesty note:** this was built and syntax-checked in an offline sandbox
> (no package registry or live database access), so it has **not** been
> run end-to-end yet. Do the steps below locally before trusting it in a
> demo — `pip install`, run the seed script, hit a couple of endpoints.
> The code is real (real password hashing, real JWT, real SQL relationships,
> real authorization checks) but "syntax-checked" isn't the same as
> "tested against a live Postgres."

## 1. Run locally (SQLite, zero setup)

```bash
cd vidyasetu-backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                # defaults to a local SQLite file
python -m app.seed                  # creates tables + demo data
uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000/docs for interactive Swagger docs — every
endpoint below is listed there with live "Try it out" buttons.

Demo accounts (password for all: `demo1234`):

| Role        | Email                     |
|-------------|---------------------------|
| Student     | aarav@student.demo        |
| Faculty     | kavita@faculty.demo       |
| Institution | admin@manipal.demo        |
| Industry    | hr@razorpay.demo          |
| Admin       | admin@vidyasetu.demo      |

## 2. What's real here

- **Auth**: bcrypt password hashing, JWT bearer tokens, `/auth/register`,
  `/auth/login`, `/auth/me`.
- **Authorization at the API, not just the UI**: every protected route uses
  `require_role(...)` (see `app/deps.py`). A student JWT gets a 403 on
  industry-only routes regardless of what the frontend hides.
- **Skill Intelligence**: `StudentSkill.competency_score` and
  `evidence_confidence` are *computed* from `SkillEvidence` rows
  (`app/engine.py:recompute_student_skill`) — not typed-in numbers. Add
  evidence via `POST /students/me/skills/evidence` and watch the score move.
- **Gap analysis & readiness**: computed from the student's real skills vs.
  a `CareerRole`'s required skills (`GET /students/me/gap-analysis`).
- **Career Impact Simulator**: `POST /students/me/simulate-skill` counts
  real active `Opportunity` rows the student would newly qualify for.
- **Opportunity matching**: `GET /opportunities` returns a transparent,
  weighted match score per opportunity with matched/missing skill lists —
  not a random or hardcoded percentage (`app/engine.py:match_opportunity`).
- **Institution intervention simulator**: `POST
  /institutions/me/intervention-simulator` models a training program's
  effect using a documented, tunable uplift formula — explainable, not a
  black box.
- **Applications persist real state**: apply → industry sees it → industry
  updates status → student gets a real `Notification` row.
- **Vidya AI assistant**: `POST /ai/ask` is rule-based and grounded only in
  your own database (see `app/engine.py:ai_explain_answer`) — every answer
  comes with `reasons` and a `source`, matching the brief's explainability
  requirement. See section 5 below for wiring in a real LLM instead.

## 2b. How the frontend is wired (the actual `index.html`)

The root `index.html` is your real, original file — landing page, role
picker, sidebar app shell, all five role dashboards, SVG charts, and the
Ask Vidya panel are untouched. On top of that:

- **Real login replaces the old instant "pick a card" flow** for Student,
  Faculty, Institution, and Industry. Choosing one of those roles opens a
  sign-in form prefilled with that role's seeded demo account — sign in
  for real, or hit "Skip — explore with static demo data" to fall back to
  the original mock experience instantly. **Admin still enters instantly
  with no login step** — the seed script does create an
  `admin@vidyasetu.demo` backend account, but no admin-specific endpoints
  or views were wired in this pass (see below), so there's nothing live
  for an admin login to fetch yet.
- **A small banner** at the top of the dashboard says plainly whether
  you're looking at 🟢 live backend data or 🟡 static demo data (shown
  automatically if the backend is unreachable — e.g. a sleeping Render
  free-tier instance — so the demo degrades gracefully instead of
  breaking).
- **Real data flows into the existing render functions unchanged**: skill
  scores, evidence, opportunities with real match percentages, the
  student's application tracker, institution heatmap, and industry
  candidate list are fetched and reshaped to match the original mock
  object shapes (`DATA`, `OPPORTUNITIES`, `CANDIDATES`, `COLLABS`) — so
  every existing template function (`skillRow`, `opportunityCard`,
  `heatmapTable`, etc.) works exactly as it did before, now fed by
  the database.
- **Applying to an opportunity really persists** when signed in for real
  (`submitApplication()` calls `POST /opportunities/apply`); in demo mode
  it stays the original decorative confirmation.
- **Ask Vidya calls the real `/ai/ask` endpoint** when signed in for real,
  and falls back to the original canned `AI_RESPONSES` dictionary
  otherwise or if the request fails.

### Still decorative / not wired to the backend
Being specific about what's still the original static prototype, not
because it's broken but because it wasn't in this pass's scope:
- **Admin dashboard** — no backend account or endpoints for admin in this
  build; stays fully mock.
- **Institution Intervention Simulator view** (`institutionSimulator()`)
  — the backend endpoint (`POST /institutions/me/intervention-simulator`)
  is real and working, but this specific view's skill/program chips
  aren't clickable yet, so the numbers shown stay the original static
  86→214 example rather than a live recomputation.
- Copy such as "Recent industry feedback" text, the skill evidence
  timeline list, and the landing page's illustrative stats are still
  static prose/numbers, as they were before — nothing here claims to be
  live data.

## 3. What's intentionally NOT built yet

Being upfront about scope: this covers phases 1–9 of the brief's suggested
sequence (auth, schema, skill intelligence, gaps, matching, applications).
Not yet implemented as real backend logic:

- Admin moderation/audit-log UI actions (the `AuditLog`/`VerificationRecord`
  tables exist; nothing writes to them yet).
- File uploads (project evidence links are currently plain URL strings).
- Rate limiting, refresh tokens (`access_token_expire_minutes` defaults to
  24h flat — fine for a demo, not for production).
- A real LLM behind `/ai/ask` (currently rule-based on purpose — see below).
- Automated tests. Test the flows in section 4 manually before your demo.

## 4. Manual test checklist before your demo

Run these once locally so you know it works before relying on it live:

1. `POST /auth/register` a new student → get a token.
2. `POST /students/me/skills/evidence` with `{"skill_name": "Docker",
   "evidence_type": "Practical Challenge", "score_contribution": 70}` →
   `GET /students/me/skills` and confirm Docker's score changed.
3. `PATCH /students/me/target-role?role_title=AI/ML Engineer` then
   `GET /students/me/gap-analysis`.
4. `GET /opportunities` as that student → confirm match percentages differ
   per opportunity and match your seeded skill levels roughly.
5. `POST /opportunities/apply` → log in as `hr@razorpay.demo` →
   `GET /applications/for-opportunity/{id}` → `PATCH
   /applications/{id}/status?new_status=Shortlisted` → log back in as the
   student → `GET /applications/me` shows the new status, and
   `GET /notifications/me` shows the notification.
6. Try any industry-only route with the student's token — confirm you get
   a 403, not a 200.

## 5. Deployment

### Database — Render PostgreSQL
1. Render dashboard → New → PostgreSQL. Copy the **Internal Database URL**.
2. Set it as `DATABASE_URL` in the web service's environment (step below).

### Backend — Render Web Service
1. Push this `vidyasetu-backend/` folder to your GitHub repo (a subfolder
   of the existing repo is fine — Render lets you set a root directory).
2. Render dashboard → New → Web Service → connect the repo.
   - Root directory: `vidyasetu-backend`
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. Environment variables: copy every key from `.env.example`, using your
   real `DATABASE_URL` and a freshly generated `JWT_SECRET_KEY`
   (`python -c "import secrets; print(secrets.token_hex(32))"`). Set
   `CORS_ORIGINS` to your actual Vercel URL.
4. After first deploy, run the seed script once via Render's Shell tab:
   `python -m app.seed`.

### Frontend — Vercel (unchanged)
The `index.html` at the repo root (one level up from this folder) already
has the API bridge inlined — no separate script file to add. Open it and
change the one line near the top of its `<script>` block:
```js
const API_BASE = "http://localhost:8000"; // <-- change to your Render backend URL
```
to your deployed Render URL, then push. Nothing else in `index.html`
needs to change to go live.

## 6. Swapping in a real LLM for Vidya

`app/routers/ai.py` builds a `context` dict from real database state and
passes it to `ai_explain_answer(role, question, context)` in
`app/engine.py`. To use a real LLM instead of the rule-based logic, replace
the body of that function with a call to your LLM provider, passing the
same `context` dict as grounding — the response contract
(`answer`, `reasons`, `source`) stays identical, so nothing else in the API
or frontend needs to change. Keep `source` honest: mark it clearly if a
response ever uses information beyond your own database.
