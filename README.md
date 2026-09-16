# VidyaSetu — push contents

This is the whole repo, ready to replace what's currently in
`github.com/Samdarshil/VidyaSetu`.

## What's in here

- **`index.html`** — replaces your existing root file. Same visual
  identity, same landing page, same five role dashboards. On top of that,
  Student/Faculty/Institution/Industry now have a real sign-in step
  wired to the backend below, with a "Skip — explore with static demo
  data" fallback so the demo never breaks if the backend isn't deployed
  yet or is asleep. See `vidyasetu-backend/README.md` section 2b for the
  exact list of what's live vs. still-static.
- **`vidyasetu-backend/`** — new folder, additive. Real FastAPI +
  SQLAlchemy backend: JWT auth, role-based authorization enforced at the
  API (not just hidden buttons), an evidence-based skill-intelligence and
  opportunity-matching engine, and a seed script with the same
  institutions/companies your frontend already references.

## Before you push

1. Open `vidyasetu-backend/README.md` — start with section 1 (run it
   locally) and section 4 (manual test checklist). This was built and
   syntax-checked offline; it has not been run against a live database.
   Confirm it actually works before you rely on it in front of judges.
2. Once you've deployed the backend (section 5 of that README covers
   Render), change one line near the top of `index.html`'s `<script>`
   block:
   ```js
   const API_BASE = "http://localhost:8000"; // <-- change to your Render backend URL
   ```
3. Push both `index.html` and `vidyasetu-backend/` to your repo.

## Demo accounts (password for all: `demo1234`)

| Role        | Email                |
|-------------|-----------------------|
| Student     | aarav@student.demo    |
| Faculty     | kavita@faculty.demo   |
| Institution | admin@manipal.demo    |
| Industry    | hr@razorpay.demo      |

Each is prefilled automatically when you pick that role on the sign-in
screen — you don't need to type them.
