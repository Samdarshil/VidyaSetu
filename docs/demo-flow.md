# Demo Flow

A script for presenting VidyaSetu to judges/evaluators. Every step below
maps to a real, working action — none of it is narrated over a static
screen.

Password for every seeded account: `demo1234`.

## The core story (~5–7 minutes)

1. **Open the site.** Landing page explains the positioning: evidence-driven
   skill intelligence, not another job board or LMS.
2. **"Explore VidyaSetu" → choose Student.** Sign in as `aarav@student.demo`
   (prefilled). Point out the 🟢/🟡 banner — it tells the room honestly
   whether you're on live backend data or the static fallback.
3. **Dashboard.** "Good morning, Aarav" — career readiness, verified skill
   count, the "highest-impact next move" card (Docker), and matched
   opportunities, all computed, not typed in.
4. **Skill Profile → Connect GitHub.** Enter any real public GitHub
   username (yours works). Show the repo list coming back with detected
   languages, and that this becomes real Project evidence for skills
   VidyaSetu tracks — explain plainly that this reads public repos only,
   no OAuth, no token.
5. **Still on Skill Profile.** Click into a skill — show competency,
   evidence confidence, and the underlying evidence list (assessment,
   project, GitHub, etc.) that produced the number.
6. **Available Assessments → take one** (Docker Fundamentals is a good
   choice since it's the flagged gap). Answer the questions, submit.
7. **Show the real score and the updated skill.** Then navigate back to
   Skill Profile — Docker's competency and confidence have genuinely
   changed, because the assessment result is real evidence in the
   database now, not a repainted number.
8. **Skill Gap Analysis.** Pick "AI / ML Engineer" as the target role.
   Point out the roadmap step for a skill with a seeded assessment is
   clickable — clicking it reopens that same real assessment flow.
9. **Career Impact Simulator.** "What happens if I learn Docker?" — show
   the opportunity and readiness projection.
10. **Opportunities.** Open one, show the match percentage with matched
    and missing skills explained, not just a bare number. Apply — this
    creates a real `Application` row.
11. **Ask Vidya.** Ask "What should I learn next?" — the answer names the
    same gap and cites real reasons, grounded in the student's actual
    profile.
12. **Switch role → Industry** (`hr@razorpay.demo`). Open Talent Search,
    pick a candidate, click "Why this match?" — show the same kind of
    explainable breakdown from the other side of the marketplace.
13. **Switch role → Institution** (`admin@manipal.demo`). Open Skill
    Intelligence (the department × skill heatmap, real data), then
    Intervention Simulator — pick a skill and program length, run it, and
    show the projected readiness change is computed live.
14. **Close on Faculty** (`kavita@faculty.demo`) if time allows — Students
    page, open a real student's evidence-backed profile, and the
    Collaboration view showing a real request with a working
    accept/decline action.

## If something doesn't load

The 🟡 demo-data banner and the "Skip — explore with static demo data"
option on sign-in exist for exactly this situation (e.g. a Render
free-tier backend that's gone to sleep and needs ~30 seconds to wake on
the first request). Mention this openly rather than let a slow first
request look like a bug — it's a known, explained tradeoff of free-tier
hosting, not a defect in the product.

## What to avoid in the demo

- Don't open the Admin dashboard as if it's a live feature — it's
  explicitly mock in this build (see the root README's Known
  Limitations). If asked, say so plainly rather than clicking through it
  as though it does something.
- Don't claim the GitHub import "proves" the student's skill level — the
  UI's own language is "supports competency evidence," and the demo
  narration should match that.
