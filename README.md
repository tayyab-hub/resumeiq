# ResumeIQ — AI Resume Analyzer and Job Matching Platform

A full-stack web application that compares a PDF resume against a job description and returns a
**transparent, auditable** match score. Every point is traceable: each category publishes its
weight, the evidence behind it, and what it cannot measure.

<!-- Replace with real badges once the repository is pushed and CI has run. -->
![Tests](https://img.shields.io/badge/tests-207%20passing-success)
![Coverage](https://img.shields.io/badge/coverage-93%25-success)
![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue)
![TypeScript](https://img.shields.io/badge/typescript-strict-blue)
![Licence](https://img.shields.io/badge/licence-MIT-lightgrey)

---

## Table of contents

1. [Project summary](#1-project-summary) · 2. [Problem statement](#2-problem-statement) ·
3. [Target users](#3-target-users) · 4. [Key features](#4-key-features) ·
5. [Screenshots](#5-screenshots) · 6. [Technology stack](#6-technology-stack) ·
7. [System architecture](#7-system-architecture) · 8. [Database structure](#8-database-structure) ·
9. [Matching methodology](#9-matching-methodology) · 10. [Installation](#10-installation) ·
11. [Environment variables](#11-environment-variables) · 12. [Testing](#12-testing) ·
13. [Security](#13-security) · 14. [Privacy](#14-privacy) ·
15. [Deployment](#15-deployment) · 16. [Known limitations](#16-known-limitations) ·
17. [Future improvements](#17-future-improvements) · 18. [AI usage statement](#18-ai-usage-statement) ·
19. [Author](#19-author) · 20. [Licence](#20-licence)

---

## 1. Project summary

ResumeIQ takes a PDF resume and a pasted job description, and produces a breakdown of how well the
two align: which required skills are evidenced, which are missing, which resume sections are
absent, which bullet points read as duties rather than results, and how each of those contributes
to a score out of 100.

The distinguishing feature is **transparency**. The scoring rubric is published in
[`docs/06-scoring-methodology.md`](docs/06-scoring-methodology.md), implemented as a pure function
in [`backend/app/analyzers/scorer.py`](backend/app/analyzers/scorer.py), and rendered in the UI in
full — weight, points earned, evidence, recommendation, and limitation for all eight categories. A
user can reconstruct the total by hand from what is on the screen.

The second is **not keeping data**. The uploaded PDF is read in memory and discarded; there is no
column anywhere in the schema capable of storing a file. Extracted resume text is not stored unless
the user explicitly opts in per analysis, and that rule is enforced by a database `CHECK`
constraint rather than only by application code.

---

## 2. Problem statement

Job seekers submit the same resume to many roles and receive no feedback when rejected. Two failure
modes are invisible to them:

1. **Relevance gap.** The resume does not contain the skills the posting asks for — or contains
   them under different wording (`JS` vs `JavaScript`, `Postgres` vs `PostgreSQL`) that keyword
   screens miss.
2. **Evidence gap.** Bullets describe responsibilities rather than outcomes. *"Responsible for
   maintaining the company website"* states a duty; it does not say what changed, by how much, or
   with what technology.

Existing "ATS scanner" tools return a single opaque number with no explanation, and frequently make
claims they cannot support. **A score without a method is not feedback** — it cannot be acted on,
and it cannot be audited.

ResumeIQ addresses this by publishing the method.

---

## 3. Target users

| User | Need |
|---|---|
| Final-year student / recent graduate | Which listed skills actually match this role, and which resume sections are missing entirely |
| Early-career developer tailoring per application | Which required skills for *this* job are absent, and which bullets read as duties rather than results |
| Career changer | Whether the resume surfaces relevant experience in language the target role recognises |

---

## 4. Key features

**Analysis**
- PDF upload with layered validation: extension, MIME type, magic bytes, size, and content
- Text extraction with normalisation (whitespace, bullet glyphs, hyphenated line breaks)
- Nine-section detection (contact, summary, skills, experience, education, projects,
  certifications, achievements, languages), reporting the heading that triggered each match
- Job description parsing into required vs preferred skills, experience, and education requirements
- Skill matching with alias resolution and word-boundary safety (`R` does not match "Requirements";
  `Go` does not match "Google")
- Statement analysis: generic phrasing, passive voice, missing action verbs, absent metrics,
  over-long bullets, repeated phrasing
- Eight-category weighted score, each with published weight, evidence, recommendation, and stated
  limitation

**AI (optional)**
- Personalised rewording, summary suggestions, skill guidance, and interview points
- Instructed and tested never to fabricate an employer, qualification, or figure
- Output schema-validated before storage; malformed output is discarded
- **The application is fully functional with no AI provider configured** — a failure degrades the
  richness of advice, never the existence of a result

**Accounts and history**
- Registration, login, silent token refresh, logout, account deletion
- Saved history with rename and delete
- Dashboard with aggregate statistics, score trend, and most common missing skills
- Ownership enforced in the repository layer; cross-user access returns 404, not 403

**Interface**
- Twelve pages, each with loading, empty, error, and populated states
- Responsive from 360 px to 1440 px, sidebar collapsing to an accessible drawer
- Print stylesheet that strips navigation and retains the disclaimer

---

## 5. Screenshots

> **To be captured before publishing.** Take these from the demo account (§10.4), which contains
> only fictional data. Save to `docs/screenshots/` and check that no real personal information
> appears in any image.

| View | File | What to capture |
|---|---|---|
| Landing page | `docs/screenshots/landing.png` | Hero plus the published scoring table |
| Dashboard | `docs/screenshots/dashboard.png` | Stat cards, score trend, common gaps |
| New analysis | `docs/screenshots/new-analysis.png` | Upload area and job description form |
| Results — score | `docs/screenshots/results-score.png` | Gauge and summary panel |
| Results — breakdown | `docs/screenshots/results-breakdown.png` | An expanded category showing evidence and limitation |
| History | `docs/screenshots/history.png` | Table with rename and delete |

---

## 6. Technology stack

| Layer | Choice | Why this, over the alternative |
|---|---|---|
| API | FastAPI + Pydantic v2 | The validation model is the same object that generates the OpenAPI docs, so the contract cannot drift from the code |
| ORM | SQLAlchemy 2.0 (typed) | Parameterised queries throughout; `Mapped[]` annotations give real type safety |
| Migrations | Alembic | Schema changes are reviewable artefacts in git, not manual DDL |
| Database | PostgreSQL 16 | Real foreign keys, `ON DELETE CASCADE`, JSONB, and check constraints |
| PDF | PyMuPDF | Best text-extraction accuracy of the pure-Python options on multi-column layouts |
| Passwords | `bcrypt` directly | passlib imports the stdlib `crypt` module, **removed in Python 3.13** |
| Tokens | PyJWT (HS256) | Stateless access tokens; refresh tokens stored hashed so they can be revoked |
| Frontend | React 18 + TypeScript (strict) + Vite | `strict` catches API contract drift at build time |
| Styling | Tailwind CSS | Design tokens live in one config file, which makes a consistent system enforceable |
| Server state | TanStack Query | Caching and invalidation without hand-rolled effects |
| Forms | React Hook Form + Zod | One schema drives validation, types, and messages |
| Charts | Recharts | Composable, accessible defaults, code-split out of the initial bundle |
| AI | Anthropic Claude API (`claude-opus-5`) | Strong instruction-following for the never-fabricate constraint; structured-output support. Model ID is an environment variable |

---

## 7. System architecture

```
┌──────────────┐   HTTPS + Bearer token    ┌──────────────────┐
│  React SPA   │   + httpOnly refresh      │  FastAPI         │
│  (Vercel)    │ ────────────────────────► │  (Render/Docker) │
└──────────────┘                           └────────┬─────────┘
                                                    │ SQLAlchemy
                                                    ▼
                                           ┌──────────────────┐
                                           │  PostgreSQL      │
                                           └──────────────────┘
                                                    ┊
                                    (optional, 20s timeout, non-fatal)
                                                    ▼
                                           ┌──────────────────┐
                                           │  Claude API      │
                                           └──────────────────┘
```

The dashed edge is the point of the design: the AI provider is the only external dependency, and
the system is fully functional without it.

### Backend layering

| Layer | Responsibility | Must not |
|---|---|---|
| `api/` | Routing, status codes, dependency injection | Contain business logic or touch the ORM session |
| `services/` | Orchestration — sequence analyzers, assemble, persist, enrich | Know about HTTP |
| `analyzers/` | **Pure functions.** Text in, structured data out | Perform I/O, touch the database, read the clock, or use randomness |
| `repositories/` | All database queries; `owner_id` is a required parameter | Contain scoring or parsing logic |
| `security/` | Hashing, JWT, `get_current_user`, rate limiting | — |

**Why `analyzers/` is separate from `services/`:** the analyzers are the intellectual core and the
part most worth testing. Keeping them pure means every scoring rule is unit-testable with a plain
string — no fixtures, no database, no mocks. That is why 93% coverage was achievable, and it is the
layer to walk an interviewer through.

**Why `repositories/` exists:** ownership enforcement lives in one place. With the `owner_id` filter
inside the query function rather than in each route, a forgotten check in a new endpoint is
impossible rather than merely unlikely.

### Request flow for an analysis

1. Validate upload (extension → MIME → magic bytes → size) and job description length
2. Extract text with PyMuPDF, in memory; normalise
3. Run the pure analyzers: sections, skills, statements, experience, education
4. Parse the job description into a requirements profile
5. `compute_score(resume, job)` → deterministic breakdown
6. **Persist** — the result exists before anything external is called
7. Attempt AI enrichment under a timeout; any failure sets `ai_status: "unavailable"` and returns
   `201` regardless

Full detail, including sequence diagrams: [`docs/03-architecture.md`](docs/03-architecture.md).

---

## 8. Database structure

Eight tables. `users` → `analyses` → six child tables, every relationship `ON DELETE CASCADE`.

```
users ──┬── refresh_tokens          (token stored as SHA-256, never raw)
        └── analyses ──┬── job_descriptions      (1:1)
                       ├── score_categories      (8 rows, one per category)
                       ├── skill_matches         (one per job requirement)
                       ├── resume_sections       (9 rows, absence recorded explicitly)
                       ├── statement_findings    (bounded to 30)
                       └── recommendations       (labelled rule | ai)
```

Design decisions worth defending in an interview:

- **UUID primary keys.** Sequential integers make record counts and other users' rows guessable.
  Combined with 404-not-403, an attacker cannot even confirm that an ID exists.
- **The privacy constraint is in the schema:**
  `CHECK (store_resume_text OR resume_text IS NULL)`. A future code path cannot quietly violate it.
- **There is no `resumes` table and no file column.** That is the point.
- **`overall_score` is denormalised** onto `analyses` so the history list and dashboard need no
  aggregate join. Written once, in the same transaction as its categories, never mutated.
- **Absence is stored explicitly** — nine section rows always, including `detected = false` — so
  "analysed and missing" stays distinguishable from "never analysed".

Full ERD and column specifications: [`docs/04-database-design.md`](docs/04-database-design.md).

---

## 9. Matching methodology

Eight categories totalling exactly 100 points. The weights are constants in one dictionary, with a
module-level assertion that they sum to 100 — an inconsistent rubric cannot be shipped.

| Category | Weight | Measures |
|---|---:|---|
| Required skill coverage | 30 | Matched (1.0) + partially matched (0.5) ÷ total required |
| Relevant experience | 15 | Duration against the stated requirement (8) + required skills evidenced *inside* the experience section (7) |
| Preferred skill coverage | 10 | Same formula as required |
| Education alignment | 10 | Ordinal comparison: none < certificate < diploma < bachelor < master < doctorate |
| Keyword coverage | 10 | Non-skill vocabulary overlap, **full marks at 60%** |
| Resume completeness | 10 | Sections weighted by how much a reader relies on them |
| Measurable achievements | 10 | Banded count of quantified outcomes |
| Statement quality | 5 | Deductions for weakening patterns |

Three choices deserve explanation:

- **Keyword coverage caps at 60%.** Requiring total overlap would reward stuffing the resume with
  the posting's vocabulary — precisely the behaviour this tool should not encourage.
- **Unparseable data scores neutral, never zero.** A resume with no readable dates has a formatting
  problem, not necessarily an experience problem, so it earns 4/8 and a formatting recommendation.
- **Categories rescale when not applicable.** A posting with no preferred skills sets that category
  to 0/0 and rescales the rest to 100. An employer who lists no preferences must not cost the
  candidate ten points.

Worked example, formulas, and every limitation:
[`docs/06-scoring-methodology.md`](docs/06-scoring-methodology.md). The worked example is
reproduced by a test, so if the code changes, the documentation fails.

---

## 10. Installation

### Prerequisites

- Python 3.11+ · Node.js 20+ · Docker Desktop (optional but easiest) · Git

### 10.1 Docker (recommended)

```bash
git clone https://github.com/tayyab-hub/resumeiq.git
cd resumeiq
cp backend/.env.example backend/.env      # works as-is for local development
docker compose up --build
```

- Frontend → <http://localhost:5173>
- API docs → <http://localhost:8000/docs>

Migrations run automatically before the API starts.

### 10.2 Backend without Docker

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # then set JWT_SECRET and DATABASE_URL

alembic upgrade head
uvicorn app.main:app --reload
```

> **Generate a real secret:**
> `python -c "import secrets; print(secrets.token_urlsafe(48))"`
> The application refuses to start in production with the example value.

### 10.3 Frontend without Docker

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

### 10.4 Demonstration account

```bash
cd backend
python -m scripts.seed_demo
```

Creates `demo@resumeiq.example` / `demo account 2026` with three analyses scoring 76, 62, and 50 —
a close match, a partial match, and a weak one, which is what makes the tool's discrimination
visible in a demo.

**All seeded data is fictional.** The resume describes an invented person at invented companies. No
real resume, email address, or employer appears anywhere in this repository.

---

## 11. Environment variables

### Backend (`backend/.env`)

| Variable | Required | Default | Notes |
|---|---|---|---|
| `ENVIRONMENT` | no | `development` | `development` \| `production` \| `test` |
| `DEBUG` | no | `true` | Must be `false` in production; startup asserts this |
| `DATABASE_URL` | **yes** | — | `postgresql+psycopg://user:pass@host:5432/db` |
| `JWT_SECRET` | **yes** | — | ≥ 32 characters; startup fails on the example value in production |
| `ACCESS_TOKEN_TTL_MINUTES` | no | `30` | |
| `REFRESH_TOKEN_TTL_DAYS` | no | `7` | |
| `BCRYPT_ROUNDS` | no | `12` | Do not lower in production |
| `CORS_ORIGINS` | **yes** | localhost | Comma-separated exact origins. Never `*` |
| `MAX_UPLOAD_BYTES` | no | `5242880` | 5 MB |
| `AI_API_KEY` | no | *(empty)* | **Leave empty to run without AI** — everything still works |
| `AI_MODEL` | no | `claude-opus-5` | Swappable without a code change |
| `AI_TIMEOUT_SECONDS` | no | `20` | |

### Frontend (`frontend/.env.local`)

| Variable | Required | Notes |
|---|---|---|
| `VITE_API_BASE_URL` | **yes** | Include the `/api/v1` suffix |

> ⚠️ **Every `VITE_*` variable is compiled into the browser bundle and is public.** Never put a
> secret in one.

---

## 12. Testing

```bash
# Backend — 207 tests
cd backend
pytest                                              # all
pytest --cov=app --cov-report=term-missing          # with coverage
pytest tests/unit -q                                # analyzers only, no database needed

# Frontend
cd frontend
npm test
npm run typecheck && npm run lint
```

### Current state

| Suite | Result |
|---|---|
| Backend tests | **207 passing** |
| Backend coverage | **93%** overall — `analyzers/` 95–99%, `security/` 95–96%, `services/` 91–95% |
| Lint (`ruff`) | Clean |
| Migrations | `upgrade → downgrade → upgrade` verified |

`services/ai_service.py` sits at 45% because the live-provider branch needs a real API key. Every
fallback path is covered.

### Tests worth reading

These encode the guarantees the project actually makes:

- `TestOwnershipEnforcement` — cross-user `GET`/`PATCH`/`DELETE` all return 404, the target survives
  the attempt, and list endpoints are scoped. *The most important tests in the project.*
- `test_analysis_completes_with_no_ai_key_configured` — the AI-independence guarantee
- `test_suggestions_never_invent_a_number` — the anti-fabrication guarantee, asserted directly
- `test_unhandled_failures_leak_nothing` — a forced 500 returns no path, trace, or class name
- `test_logs_contain_no_resume_content` — captures logs during a full analysis and asserts no
  resume text or email address appears
- `test_arithmetic_matches_the_published_example` — keeps the scoring documentation honest
- `test_rejects_an_executable_renamed_as_pdf` — the magic-byte check
- `test_unsigned_alg_none_token_is_rejected` — the classic JWT attack

Test data policy: all fixtures are fictional and labelled. No real person's resume, email address,
or proprietary job posting appears in the repository.

Strategy and the manual checklist: [`docs/08-testing-strategy.md`](docs/08-testing-strategy.md).

---

## 13. Security

| Risk | Control |
|---|---|
| Weak password storage | bcrypt, cost 12. `password_hash` appears in no response schema anywhere |
| Broken access control (IDOR) | `owner_id` is a **required parameter** of every analysis query; non-owned returns **404**, not 403 |
| Unsafe upload | Extension → MIME → **magic bytes** → size, streamed and aborted early. Filenames sanitised; nothing written to disk |
| SQL injection | SQLAlchemy with bound parameters throughout; no string-interpolated SQL |
| XSS | React escapes by default; `dangerouslySetInnerHTML` banned by an ESLint rule, not by discipline |
| Token theft | Access token in **memory only** (never `localStorage`); refresh token in an `httpOnly; Secure; SameSite=None` cookie, stored server-side as SHA-256 |
| Brute force | 5 failures / 15 min per email **and** per IP; unknown-email and wrong-password responses are identical, including timing |
| Information disclosure | One global handler; unhandled errors return a generic body plus a request ID. Traces stay server-side |
| CORS misconfiguration | Explicit origin allowlist with credentials; never `*` |
| Prompt injection | Resume content passed as delimited data; AI has **no tools and no database access**, so the worst outcome is a bad suggestion |

Timing equalisation is worth noting: the unknown-email login path runs a bcrypt comparison against
a dummy hash, so response time does not reveal whether an account exists.

Full threat model and the security checklist:
[`docs/07-security-privacy.md`](docs/07-security-privacy.md).

---

## 14. Privacy

| Data | Stored? | Rationale |
|---|---|---|
| The PDF file | **Never** | Read in memory, discarded. No table or column could hold it |
| Full resume text | **Not by default** | Per-analysis opt-in, enforced by a DB `CHECK` constraint |
| Flagged statements | Yes, ≤ 30, ≤ 600 chars | The results page must show the user their own bullets |
| Skill evidence snippets | Yes, ≤ 240 chars | A match the user cannot verify is not credible |
| Job description | Yes, in full | Employer content, not the user's personal data |
| Scores, sections, recommendations | Yes | Derived data — the product |

**What the AI provider receives:** matched and missing skill names, the text of already-flagged
statements, which sections are absent, and the job title. It does **not** receive the PDF, the full
resume text, or the user's name, email, phone, or address. The prompt is assembled from analysis
output, not from the document.

**Logging:** no resume content, job description content, or PII at any level, in any environment —
asserted by a test.

---

## 15. Deployment

### Backend → Render

1. New Web Service from the repository, root directory `backend`, environment **Docker**
2. Add a managed PostgreSQL instance and copy its internal URL to `DATABASE_URL`
3. Set `ENVIRONMENT=production`, `DEBUG=false`, a real `JWT_SECRET`, `CORS_ORIGINS` (your Vercel
   URL), and optionally `AI_API_KEY`
4. **Pre-deploy command:** `alembic upgrade head`

> Migrations run as a release command, never at application start — two starting workers would race
> each other applying the same migration.

### Frontend → Vercel

1. Import the repository, root directory `frontend`, framework **Vite**
2. Set `VITE_API_BASE_URL` to `https://<your-api>.onrender.com/api/v1`
3. Deploy, then add the resulting Vercel URL to the backend's `CORS_ORIGINS` and redeploy the API

### Post-deployment checklist

- [ ] `/api/v1/health` returns `{"status":"ok","database":"ok"}`
- [ ] `/docs` returns **404** in production
- [ ] Register, log in, run an analysis, refresh the page — session survives
- [ ] Refresh cookie shows `HttpOnly`, `Secure`, `SameSite=None` in DevTools
- [ ] A request from a disallowed origin receives no allow header
- [ ] Seed the demo account

> **Free-tier cold starts.** Render free instances sleep when idle; the first request after that
> can take ~30 seconds. The frontend surfaces this in its network-error message rather than
> presenting it as a failure.

---

## 16. Known limitations

Published because a tool that lists only its strengths is not telling you enough to judge its
output.

**Analysis**
- Skill matching is **lexical**, against ~300 curated terms and their aliases. Unusual wording or a
  technology outside that list is missed — which understates a score rather than inflating it.
- Required/preferred classification is **cue-based**. Postings without conventional headings fall
  back to "all required"; the result discloses when this happened.
- **No OCR.** Scanned resumes are detected and explained clearly, not processed.
- English only. Employment-date parsing covers common formats; unusual ones may be misread.
- Achievement detection is pattern-based, so "halved the processing time" is missed.

**Product**
- The score does not predict shortlisting or hiring, and does not replicate any specific
  employer's ATS. No commercial ATS publishes its logic, so any tool claiming to would be guessing.
- It cannot verify that anything on a resume is true.
- Not a replacement for a recruiter or careers adviser.

**Engineering**
- Analysis is synchronous; a very large PDF on a cold free-tier instance may approach the platform
  timeout. A job queue is the documented scaling path.
- **Rate-limit counters are in-process**, so limits are per-worker. A multi-instance deployment
  would need Redis.
- Email addresses are not verified; there is no MFA.
- No third-party penetration test or compliance certification.
- PyMuPDF is AGPL-licensed — see [LICENSE](LICENSE). It is isolated behind a single function so it
  can be swapped for a permissive alternative.

---

## 17. Future improvements

| Improvement | Why it was deferred |
|---|---|
| Embedding-based semantic skill matching | Would match more, but could not explain *why* a skill was considered present — directly in tension with the transparency goal. Would need to sit **alongside** the lexical score, not replace it |
| OCR for scanned resumes | A heavy dependency and a new failure mode; v1 detects and explains instead |
| DOCX support | Each parser is a separate correctness and security surface |
| Background job queue | Not justified at this volume; the documented path if analysis time grows |
| Redis-backed rate limiting | Required only once there is more than one instance |
| Resume version comparison | Show score movement between two revisions of the same resume |
| Email verification and MFA | Neither demonstrates anything the current auth flow does not |
| Taxonomy contribution flow | Let users propose missing skills, directly addressing the main accuracy limitation |

---

## 18. AI usage statement

AI tools were used for technical guidance, debugging support, and code review. The project
architecture, implementation decisions, testing, and final verification were completed by the
developer.

No AI-generated percentage is claimed, because any such figure would be invented.

Separately — and distinctly — the *application itself* integrates the Claude API as an optional
feature for generating resume-improvement suggestions. That integration is described in §4 and
[`docs/03-architecture.md`](docs/03-architecture.md), and the application runs in full without it.

---

## 19. Author

**Muhammad Tayyab** — built as a portfolio project for a Diploma in Computer Science.

The planning documents in [`docs/`](docs/) were written before implementation and record the
reasoning behind each decision — requirements, user stories, architecture, database design, API
contract, scoring methodology, security plan, testing strategy, and project plan.

- GitHub: [@tayyab-hub](https://github.com/tayyab-hub)
- Email: tayyabofficial0978@gmail.com

---

## 20. Licence

MIT — see [LICENSE](LICENSE).

Note that PyMuPDF, used for PDF text extraction, is AGPL v3. If that is a problem for your use
case, replace `backend/app/analyzers/pdf_extractor.py`; it is isolated behind one function for
exactly this reason.
