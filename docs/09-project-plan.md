> Historical planning/acceptance document. For implemented release behavior and measured verification, see [release readiness](10-release-readiness.md), [architecture](03-architecture.md) and [security](07-security-privacy.md). Unchecked planning items are not claims of completed validation.

# ResumeIQ — Project Plan

> Phase 1 deliverable: 30-day schedule, initial GitHub issues, git workflow, and the
> definition of "complete".

---

## 1. Thirty-day schedule

Assumes roughly **4 focused hours per day** alongside coursework. Days 7, 14, 21, and 28 are
deliberately lighter — they absorb slippage rather than adding scope.

| Day | Phase | Deliverable | Done when |
|---|---|---|---|
| 1–2 | **1. Planning** | The nine documents in `docs/` reviewed and adjusted | You can explain the scoring rubric without reading it |
| 3 | **2. Setup** | Install Git + Node; repo created; `.gitignore`, LICENSE, README skeleton, both `.env.example` files; backend and frontend scaffolds run | `uvicorn` serves `/health`; `npm run dev` serves the app |
| 4 | **2. Setup** | Tailwind design tokens; base components (Button, Input, Card, Badge, Alert, Skeleton); ESLint + Prettier + Ruff; CI workflow | CI green on an empty test suite |
| 5 | **3. Database** | Docker Compose Postgres; SQLAlchemy base; Alembic; migrations 0001–0002; `User` model | `alembic upgrade head` creates `users` |
| 6–7 | **4. Auth (backend)** | Hashing, JWT, register/login/me/refresh/logout, rate limiting, refresh-token table | All auth unit + integration tests pass |
| 8 | **4. Auth (frontend)** | Login and register pages, auth context, `ProtectedRoute`, axios interceptors | Full login → dashboard → refresh → logout cycle works |
| 9–10 | **5. Upload** | Upload validation, PyMuPDF extraction, normalisation, error codes; upload UI | All ten extractor tests pass; every error path shows a three-part message |
| 11–12 | **6. Sections** | Section detector, statement analyzer, achievement detection | Nine sections detected on three different résumé layouts |
| 13–14 | **7. Job descriptions** | Skills taxonomy JSON, skill extractor, JD parser, requirement split | Alias and word-boundary tests pass |
| 15–17 | **8. Scoring** | All eight categories, rescaling, evidence, limitations | The worked example reproduces to 69 |
| 18–19 | **9. Persistence** | Migrations 0004–0006, repositories, ownership enforcement, history endpoints | Cross-user access returns 404 on GET, PATCH, DELETE |
| 20–21 | **10. Dashboard** | App layout, sidebar/drawer, stats cards, trend chart, history table, all four states | Responsive at all four breakpoints |
| 22–23 | **10. Results page** | Score breakdown, skills, sections, statements, priority list | Every score is traceable in the UI |
| 24–25 | **11. AI** | Claude client, prompt design, schema validation, timeout, quota, rule-based fallback | Analysis succeeds with `AI_API_KEY` unset |
| 26 | **12. Export & settings** | Print stylesheet, JSON/PDF export, profile page, password change, account deletion | Print view is clean and keeps the disclaimer |
| 27 | **13. Hardening** | Security checklist, accessibility pass, Lighthouse, coverage gate | Zero critical axe violations; checklist fully ticked |
| 28 | **14. Deploy** | Dockerfiles, Compose, Render + Vercel + managed Postgres, migration release command | Live URL works end-to-end from a phone |
| 29 | **15. Documentation** | Full README, architecture + ERD diagrams, screenshots, API docs, demo account | A stranger can run it locally from the README alone |
| 30 | **15. Audit** | Secret scan, dead-code removal, final commit-history review, release tag | Every box in §5 ticked |

**If time runs short, cut in this order:** PDF export (keep print) → the trend chart (keep
the stats cards) → the interview-preparation AI section → the certifications/achievements
detectors. **Never cut:** ownership enforcement, upload validation, the AI fallback, or the
README.

---

## 2. First GitHub issues

Create these before writing code. Milestones: `Phase 2 — Foundation`, `Phase 3–4 — Auth`,
`Phase 5–8 — Analysis Engine`, `Phase 9–10 — Application`, `Phase 11–15 — Polish & Release`.
Labels: `backend`, `frontend`, `database`, `security`, `documentation`, `testing`,
`accessibility`, `infrastructure`, `phase-N`.

| # | Title | Labels | Acceptance criteria |
|---|---|---|---|
| 1 | Install and verify toolchain (Git, Node LTS, Docker Desktop) | `infrastructure` | `git --version`, `node --version`, `docker --version` all succeed |
| 2 | Initialise repository with `.gitignore`, MIT LICENSE, README skeleton | `documentation` | `.env` is ignored **before** any secret exists; README has all 20 headings as stubs |
| 3 | Scaffold FastAPI backend with `/health` | `backend` | `/health` returns `{"status":"ok"}`; project structure matches `03-architecture.md` §10 |
| 4 | Scaffold React + TypeScript + Vite + Tailwind frontend | `frontend` | `npm run dev` serves; `tsc --noEmit` clean with `strict: true` |
| 5 | Define design tokens (colour, type scale, spacing, radius, shadow) | `frontend` | Tokens in `tailwind.config.ts`; all body-text pairs ≥ 4.5:1 contrast |
| 6 | Build base UI component library | `frontend` | Button, Input, Card, Badge, Alert, Skeleton, Modal — each with focus states and a Vitest test |
| 7 | Add CI workflow (lint, typecheck, test, audit) | `infrastructure`, `testing` | Green on an empty suite; runs on every push and PR |
| 8 | Postgres via Docker Compose + SQLAlchemy + Alembic | `database` | `docker compose up db` then `alembic upgrade head` succeeds |
| 9 | `User` model and migration | `database` | `CITEXT` unique email; UUID PK; timestamps |
| 10 | Password hashing module | `backend`, `security` | bcrypt cost ≥ 12; unit tests for hash ≠ plaintext, verify, salt uniqueness |
| 11 | JWT issue/verify + `get_current_user` dependency | `backend`, `security` | Expired, malformed, wrong-secret, and `alg:none` tokens all rejected |
| 12 | Register and login endpoints | `backend` | Matches `05-api-contract.md` §3; identical response for unknown email and wrong password |
| 13 | Refresh tokens (hashed at rest) + logout revocation | `backend`, `security` | Replaying a revoked token returns 401 |
| 14 | Login rate limiting | `backend`, `security` | 5 failures / 15 min → 429 with `Retry-After` |
| 15 | Auth pages, context, and `ProtectedRoute` | `frontend` | Token never touches `localStorage`; no login flash on refresh |
| 16 | Upload validation (extension, MIME, magic bytes, size, filename) | `backend`, `security` | All six rejection tests in `08-testing-strategy.md` §2 pass |
| 17 | PDF text extraction and normalisation | `backend` | Scanned, corrupt, encrypted, and empty PDFs each return their own error code; no temp-file residue |
| 18 | **Ownership enforcement in the analysis repository** | `backend`, `security` | `owner_id` is a required parameter; cross-user access returns 404 on GET, PATCH, DELETE |
| 19 | Skills taxonomy JSON (~300 skills + aliases) | `backend` | Committed, documented, alias resolution unit-tested |
| 20 | Implement `compute_score` per the published rubric | `backend` | All fifteen scorer tests pass, including the worked example |
| 21 | AI service with schema validation, timeout, quota, and fallback | `backend` | Analysis returns 201 with `ai_status: "unavailable"` when `AI_API_KEY` is unset |
| 22 | Privacy page and landing-page limitations section | `documentation`, `frontend` | States what is stored, what the AI receives, and how to delete data |

Issues 18 and 21 are the two that most often go wrong in projects like this. Both are written
first so they cannot be "added later".

---

## 3. Git workflow

Branch per feature: `feat/jwt-authentication`, `fix/pdf-extraction-encoding`,
`docs/readme-architecture`, `test/scorer-edge-cases`, `chore/ci-workflow`.

Conventional commits, imperative mood, explaining *why* where it is not obvious:

```
feat(auth): hash refresh tokens before storing

Storing the raw refresh token means a database dump yields usable sessions.
Persist SHA-256 of the token and compare hashes on refresh.

Closes #13
```

Pull request for every feature branch, even solo. The PR body records: what changed, why this
approach, how it was tested, and any security consideration. Squash-merge to `main` so the
history reads as one commit per feature. Reviewers of the portfolio read this history — it is
part of the deliverable.

**Rules:** never commit `.env` · never commit a real résumé or personal data · never commit
generated `node_modules`, `__pycache__`, or `.pytest_cache` · never force-push `main`.

---

## 4. Risk register

| Risk | Likelihood | Impact | Response |
|---|---|---|---|
| Scoring work overruns days 15–17 | High | Schedule slip | Implement categories in weight order; a partially populated rubric still runs, and the missing categories are visibly zero-weighted |
| PDF extraction quality varies by layout | High | Poor results | Collect five genuinely different fictional résumé layouts on day 9 and test against all five from the start |
| Free-tier cold starts look like bugs in the demo | Medium | Poor first impression | Document the ~30 s wake in the README; show a "waking the server" message after 5 s |
| AI cost or quota exhausted mid-demo | Medium | Demo failure | Per-user daily quota; demo account seeded with pre-generated, labelled sample analyses |
| Scope creep (OAuth, DOCX, OCR) | Medium | Nothing finishes | §3.2 of `01-requirements.md` is the contract. New ideas become "Future improvements" README entries, not work |
| Accessibility left to day 27 and found broken | Medium | Rework | Build focus states into the base components on day 4, not retrofitted on day 27 |
| Node/Git not installed blocks day 3 | Certain today | One lost day | Issue #1 — install before day 3 |

---

## 5. Definition of "project complete"

The project is complete when **every** box below is ticked. Not most.

### Functionality
- [ ] Register, login, refresh, logout, and account deletion all work end-to-end
- [ ] PDF upload rejects non-PDF, oversized, empty, corrupt, encrypted, and scanned files, each with its own three-part message
- [ ] Nine sections detected and reported, with the matched heading shown
- [ ] Job descriptions parsed into required/preferred skills, experience, and education
- [ ] All eight score categories computed, each with weight, points, explanation, evidence, recommendation, and limitation
- [ ] Weak statements flagged with suggestions that invent nothing
- [ ] AI recommendations work when configured; the analysis is complete when they are not
- [ ] History: list, open, rename, delete
- [ ] Dashboard: stats, trend chart, common missing skills, empty/loading/error states
- [ ] Results page prints cleanly and exports
- [ ] All twelve pages implemented, including 404 and error pages

### Quality
- [ ] Backend coverage ≥ 80 % on `analyzers/`, `services/`, `security/`
- [ ] All backend and frontend tests pass in CI
- [ ] `tsc --noEmit`, ESLint, Prettier, and Ruff clean
- [ ] Manual testing checklist completed and recorded
- [ ] No dead code, no commented-out blocks, no `TODO` markers, no `console.log`
- [ ] No placeholder text, no lorem ipsum, no non-functional buttons

### Security and privacy
- [ ] Every item in the `07-security-privacy.md` §6 checklist ticked
- [ ] `git log -p` contains no secret, ever
- [ ] Cross-user access returns 404, proven by an automated test
- [ ] No PDF is persisted; no résumé text stored without opt-in
- [ ] Logs contain no résumé content and no PII
- [ ] Privacy page live and accurate

### Accessibility
- [ ] Zero critical axe violations on all twelve pages
- [ ] Complete keyboard-only pass with visible focus throughout
- [ ] Contrast ratios verified
- [ ] Screen-reader spot check completed
- [ ] `prefers-reduced-motion` respected

### Deployment
- [ ] Frontend live on Vercel, backend live on Render, managed Postgres attached
- [ ] Migrations run as a deploy release command
- [ ] `docker compose up` reproduces the whole stack from a clean clone
- [ ] Demo account works with clearly labelled fictional data
- [ ] Cold-start behaviour documented

### Documentation
- [ ] README complete against all 20 headings
- [ ] Screenshots of landing, dashboard, and results (no real personal data)
- [ ] Architecture diagram and ERD exported and embedded
- [ ] API documented; installation, testing, and deployment instructions verified on a clean clone
- [ ] Known limitations listed honestly
- [ ] Future improvements listed
- [ ] AI usage statement present and honest — no invented percentage
- [ ] No unsupported claims anywhere: no "guaranteed to pass ATS", no "100 % accurate", no "replaces recruiters"

### The one that matters most
- [ ] **You can explain, without notes:** why the layers are split as they are, why each
      scoring weight is what it is, how ownership is enforced and why 404 rather than 403,
      why the PDF is never stored, how the AI fallback works, and what this project cannot do.

If you cannot do the last box, the project is not finished regardless of how many others are
ticked. It is the one an interviewer will actually test.
