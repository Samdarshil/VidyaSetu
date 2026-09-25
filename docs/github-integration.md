# GitHub Integration

## Current mode: public repository analysis, no OAuth

VidyaSetu currently analyzes a student's **public** GitHub repositories.
**No GitHub credentials, tokens, or account access are required or
requested.**

### How it works

```
Student enters a GitHub username
            │
            ▼
Browser calls GitHub's own public API directly:
https://api.github.com/users/<username>/repos
            │
            ▼
Non-fork repos' name + primary language are collected
(this happens entirely client-side — VidyaSetu's backend
 never talks to GitHub directly in this mode)
            │
            ▼
That list is sent to POST /students/me/github-import
            │
            ▼
Each repo's language is matched against a small, explicit
map (LANGUAGE_TO_SKILL in app/routers/skills.py) to a skill
VidyaSetu already tracks — unmapped languages are skipped,
never guessed at
            │
            ▼
A SkillEvidence row is recorded per matched repo, type "Project",
with a fixed, modest score_contribution (55) — deliberately lower
than a graded assessment's typical contribution
            │
            ▼
recompute_student_skill() folds this into the skill's real
competency_score and evidence_confidence
```

### Why this approach, and not OAuth, right now

Real GitHub OAuth requires registering a GitHub OAuth App, which
generates a **Client ID and Client Secret** — a credential pair only the
GitHub account owner can create, tied to their own GitHub account and
callback URLs. That's not something that can be generated on someone
else's behalf, and it isn't needed to demonstrate the actual point of
this feature (evidence from real project work informing a skill score).
Public-repo analysis achieves the same demonstration honestly, with zero
secrets to manage or leak.

### What this evidence does and doesn't claim

- **Does claim:** "a public repository exists using this language,
  supporting evidence that this skill has been used in a real project."
- **Does not claim:** that the student wrote high-quality code, that the
  repository proves mastery, or that the student is an expert. This is
  why the contribution score (55) is fixed and modest rather than scaled
  by repo stars, size, or any other proxy that could be gamed or
  misread as a quality signal.

### Current limitations

- **Public repositories only.** Private repos are invisible to this flow
  by design — seeing them would require OAuth.
- **Language detection is GitHub's own "primary language" field**, which
  is a byte-count heuristic, not a real analysis of what the code
  actually does. A Python project with a large generated-assets folder
  in another language could be mis-tagged. This is a known, accepted
  limitation of using GitHub's own metadata rather than building a
  custom code analyzer.
- **The student must type their own username** — there's no "sign in
  with GitHub" identity step, so nothing here verifies the username
  actually belongs to the person entering it. This is a demo-appropriate
  trust model, not a production-appropriate one.
- **No commit history, contributor graph, or code-quality analysis** —
  only repo existence and declared language.

## Future: real OAuth

The upgrade path, when ready:

```
Register a GitHub OAuth App (github.com/settings/developers)
            │
            ▼
Student clicks "Sign in with GitHub" → redirected to GitHub's
authorization page → GitHub redirects back with a temporary code
            │
            ▼
Backend exchanges that code + the app's Client Secret (stored only
as a backend environment variable, never in frontend code) for an
access token
            │
            ▼
Backend calls the GitHub API on the student's behalf, using that
token, to see private repos (with the student's explicit consent
during the OAuth authorization step) and richer metadata
            │
            ▼
Same evidence pipeline as today, from here on: language detection →
skill mapping → SkillEvidence → recompute_student_skill()
```

The import code is intentionally structured so this swap only touches
*how the repo list is obtained* — the evidence-recording and
competency-recomputation logic in `POST /students/me/github-import`
would not need to change.
