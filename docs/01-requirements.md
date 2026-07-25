# ResumeIQ — Requirements Specification

> Phase 1 deliverable. Status: **draft for developer approval**.

---

## 1. Problem statement

Job seekers submit the same resume to many roles and receive no feedback when they are
rejected. The two failure modes are invisible to them:

1. **Relevance gap.** The resume does not contain the skills, tools, or qualifications the
   job description actually asks for — or contains them under different wording
   (`JS` vs `JavaScript`, `Postgres` vs `PostgreSQL`) that automated keyword screens miss.
2. **Evidence gap.** The resume lists responsibilities rather than outcomes. Bullets such as
   *"Responsible for maintaining the company website"* describe a duty; they do not tell a
   reader what changed, by how much, or with what technology.

Existing "ATS scanner" tools return a single opaque score with no explanation of how it was
derived, and frequently make claims they cannot support ("guaranteed to pass ATS"). A score
without a method is not feedback — it cannot be acted on, and it cannot be audited.

**ResumeIQ addresses this by making the analysis transparent.** It compares a PDF resume
against a pasted job description and returns a weighted score in which every category
publishes its weight, its points earned, the evidence behind those points, and the specific
limitation of that measurement. Nothing in the score is hidden, and the application states
plainly that its score is an internal estimate and not a replica of any particular employer's
applicant tracking system.

### What this project is not

- Not a guarantee of passing any employer's screening process.
- Not a replacement for a recruiter, career adviser, or hiring manager.
- Not a resume writer — the AI layer suggests rewording of statements the user already wrote;
  it never invents an employer, a qualification, a certification, or a metric.

---

## 2. Target users

| User | Context | Primary need |
|---|---|---|
| **Final-year student / recent graduate** | Applying to 20–50 entry-level roles, no professional feedback loop | Which of my listed skills actually match this role, and which sections of my resume are missing entirely |
| **Early-career developer (0–3 yrs) changing roles** | Has a working resume, wants to tailor it per application | Which required skills for *this* job are absent, and which of my bullets read as duties rather than results |
| **Career changer** | Transferable skills exist but are worded for a different industry | Whether the resume surfaces relevant experience in language the target role recognises |
| **Reviewer / interviewer (secondary)** | Evaluating this project as portfolio work | Can the author explain the architecture, the scoring model, and the security decisions |

The last row is a real user of this project. Every design decision below must be explainable
by the developer in an interview.

---

## 3. Scope

### 3.1 In scope (v1.0)

| # | Capability |
|---|---|
| S1 | Email + password registration and login with JWT-based session handling |
| S2 | PDF resume upload with extension, MIME, size, and content validation |
| S3 | Text extraction via PyMuPDF, with explicit handling of scanned/image-only PDFs |
| S4 | Detection of nine standard resume sections and reporting of missing ones |
| S5 | Job description parsing: skill extraction, required vs preferred split, experience and education requirements |
| S6 | Deterministic weighted match scoring with a published rubric (see `06-scoring-methodology.md`) |
| S7 | Resume statement analysis: weak verbs, passive voice, missing metrics, over-long bullets, repetition |
| S8 | AI-assisted rewording and improvement suggestions, with full deterministic fallback when the AI service is unavailable |
| S9 | Per-user analysis history: list, open, rename, delete — with enforced ownership |
| S10 | Dashboard with aggregate statistics, score trend chart, and common missing skills |
| S11 | Results page with full score breakdown and improvement priority list |
| S12 | Print-friendly / PDF report export |
| S13 | Profile and settings, including account deletion and data-retention control |
| S14 | Public landing page and privacy information page |

### 3.2 Explicitly out of scope (v1.0)

Recorded here so the README's *Known limitations* section is honest rather than
retro-fitted.

| Out of scope | Reason |
|---|---|
| DOCX / TXT / image resume upload | PDF is the dominant application format; each additional parser is a separate correctness and security surface |
| OCR of scanned resumes | Adds a heavy dependency (Tesseract) and a new failure mode; v1 detects and reports scanned PDFs clearly instead |
| Semantic/embedding-based skill matching | Non-deterministic and hard to explain; conflicts with the transparency goal. Listed as a future improvement |
| Multi-language resumes | Skill taxonomy and stopword lists are English-only |
| Social login (Google/GitHub OAuth) | Adds provider dependency without demonstrating anything the JWT flow does not |
| Team / recruiter accounts, billing, email verification flows | Not needed to demonstrate the core competency |
| Live job-board integration | Requires third-party API agreements |

### 3.3 Assumptions

- Resumes are text-based PDFs in English, typically 1–3 pages.
- Job descriptions are pasted as plain text, 200–8,000 characters.
- A single user's usage is low-volume (tens of analyses), so the deterministic analysis can
  run synchronously inside the request rather than in a background worker.
- The AI provider may be unavailable, rate-limited, or unconfigured at any time. The
  application must remain fully functional without it.

---

## 4. Functional requirements

Each requirement has a stable ID used by user stories, tests, and GitHub issues.

### FR-A — Authentication and accounts

| ID | Requirement |
|---|---|
| FR-A1 | A visitor can register with email, password, and full name. Email is unique, stored case-normalised. |
| FR-A2 | Passwords must be ≥ 10 characters and contain at least one letter and one digit; the same rule is enforced on client (Zod) and server (Pydantic). Server validation is authoritative. |
| FR-A3 | Passwords are stored only as a bcrypt hash (cost factor ≥ 12). The plaintext never reaches the database, the logs, or any error response. |
| FR-A4 | A registered user can log in and receive a short-lived JWT access token plus a refresh token. |
| FR-A5 | `GET /api/v1/auth/me` returns the authenticated user's profile; it returns 401 for missing, malformed, expired, or invalid-signature tokens. |
| FR-A6 | Logout invalidates the refresh token server-side and clears it client-side. |
| FR-A7 | Login attempts are rate limited per email and per IP; after repeated failures the endpoint responds with 429 and a retry hint. Failed login responses never reveal whether the email exists. |
| FR-A8 | A user can permanently delete their account, which cascades to all of their analyses. |

### FR-B — Resume upload and extraction

| ID | Requirement |
|---|---|
| FR-B1 | Only `.pdf` files are accepted. The extension, the declared MIME type, and the file's magic bytes (`%PDF-`) must all agree. |
| FR-B2 | Maximum upload size is 5 MB, enforced by streaming and aborting rather than by reading the whole body first. |
| FR-B3 | The original filename is never used to construct a filesystem path; it is sanitised and used only as a display label. |
| FR-B4 | Empty, corrupted, or encrypted PDFs are rejected with a specific, actionable error. |
| FR-B5 | A PDF from which fewer than 200 meaningful characters are extracted is reported as "likely a scanned image" with guidance, not as a generic failure. |
| FR-B6 | The uploaded file is processed in memory or in a temporary file that is deleted in a `finally` block. No PDF is persisted. |
| FR-B7 | Extracted text is normalised: collapsed whitespace, normalised bullet glyphs, de-hyphenated line breaks, preserved paragraph boundaries. |
| FR-B8 | No error response, log line, or stack trace exposes an internal filesystem path. |

### FR-C — Resume content analysis

| ID | Requirement |
|---|---|
| FR-C1 | The analyser detects these sections: contact, summary, skills, experience, education, projects, certifications, achievements, languages. |
| FR-C2 | Each section result reports `detected: bool`, the matched heading, and the character span, so the UI can explain *why* it was detected. |
| FR-C3 | Contact detection is heuristic (email regex, phone regex, URL regex), not heading-based. |
| FR-C4 | Skills are extracted from the whole document, not only from a "Skills" heading. |
| FR-C5 | Bullet-level statement analysis flags: missing action verb, passive voice, no measurable result, length > 35 words, generic phrasing ("responsible for", "worked on", "helped with"), and phrases repeated ≥ 3 times. |
| FR-C6 | Measurable achievements are detected by pattern (percentages, currency, counts with units, time reductions) and reported with the bullet they came from. |

### FR-D — Job description analysis

| ID | Requirement |
|---|---|
| FR-D1 | The user pastes a job description (200–8,000 chars) and optionally a job title and company. |
| FR-D2 | Skills are extracted by matching against a curated taxonomy with alias normalisation (`js`→`javascript`, `postgres`→`postgresql`, `k8s`→`kubernetes`). |
| FR-D3 | Requirements are classified as **required** or **preferred** using section-cue detection ("must have", "requirements", "minimum qualifications" vs "nice to have", "preferred", "bonus"). When no cue is found, all extracted skills default to **required** and the analysis discloses this. |
| FR-D4 | Years-of-experience requirements are extracted (e.g. "3+ years", "at least 5 years"). |
| FR-D5 | Education requirements are extracted and mapped to a level ordinal (none < certificate < diploma < bachelor < master < doctorate). |
| FR-D6 | Stopwords and boilerplate ("equal opportunity employer", "competitive salary") are removed before keyword coverage is computed. |

### FR-E — Matching and scoring

| ID | Requirement |
|---|---|
| FR-E1 | The overall score is the weighted sum of eight published categories totalling 100 points. |
| FR-E2 | Every category returns: name, weight, points earned, points possible, a plain-English explanation, evidence, recommendations, and a stated limitation. |
| FR-E3 | Skills are classified as matched, partially matched (alias/substring/related), or missing. Partial matches earn partial credit at a fixed, documented ratio. |
| FR-E4 | The scoring function is pure and deterministic: identical input produces an identical score, with no reliance on the AI service, on wall-clock time, or on randomness. |
| FR-E5 | Every response containing a score also carries a machine-readable disclaimer that the score is an internal estimate. |

### FR-F — AI recommendations

| ID | Requirement |
|---|---|
| FR-F1 | The AI layer produces: prioritised improvement suggestions, rewrites of specific weak statements, a professional-summary suggestion, guidance on missing skills, and interview preparation points. |
| FR-F2 | The system prompt forbids inventing employers, job titles, dates, certifications, or numbers. Rewrites must use only facts present in the supplied statement. |
| FR-F3 | If the AI provider is unconfigured, errors, or times out, the endpoint returns HTTP 200 with the deterministic analysis plus `ai_status: "unavailable"` and a reason code. The analysis must never fail because of the AI provider. |
| FR-F4 | AI calls run under an explicit timeout and a per-user daily quota. |
| FR-F5 | AI output is validated against a Pydantic schema before it is stored or returned; malformed output is treated as an AI failure and falls back. |

### FR-G — Storage, history, and ownership

| ID | Requirement |
|---|---|
| FR-G1 | A completed analysis is persisted with its score breakdown, matched/missing skills, section results, statement findings, and recommendations. |
| FR-G2 | **Raw resume text is not stored by default.** Only the specific bullet strings flagged as weak are stored (bounded), because the results page must show them back to the user. Storing full resume text is an explicit per-analysis opt-in. |
| FR-G3 | Every analysis-scoped endpoint filters by `owner_id == current_user.id`. A request for another user's analysis returns **404**, not 403, so IDs are not enumerable. |
| FR-G4 | A user can rename and delete their own analyses. Deletion is hard deletion and cascades to all child rows. |
| FR-G5 | The history list is paginated and sorted by creation date descending. |

### FR-H — Interface

| ID | Requirement |
|---|---|
| FR-H1 | Twelve pages ship: landing, login, register, dashboard, new analysis, results, history, analysis detail, profile/settings, privacy, 404, error. |
| FR-H2 | Every asynchronous view implements four states: loading (skeleton), empty, error, and populated. |
| FR-H3 | The dashboard shows: analyses count, average score, score trend chart, most frequent missing skills, recent analyses table, and quick actions. |
| FR-H4 | The results page can be printed or exported without navigation chrome. |
| FR-H5 | The UI is usable at 360 px, 768 px, 1024 px, and 1440 px widths. |

---

## 5. Non-functional requirements

| ID | Category | Requirement | How it is verified |
|---|---|---|---|
| NFR-1 | Performance | Deterministic analysis of a 2-page resume + 3,000-char JD completes in < 2 s server-side (p95), excluding the AI call | Timed pytest benchmark |
| NFR-2 | Performance | AI enrichment runs under a 20 s timeout and never blocks the deterministic result | Unit test with a mocked slow client |
| NFR-3 | Performance | First Contentful Paint < 2.0 s on the landing page over a simulated 4G connection | Lighthouse run, recorded in Phase 13 |
| NFR-4 | Security | No secret, key, or credential is committed. `.env` is git-ignored; `.env.example` documents every variable with placeholder values | `git log -p` grep + pre-commit hook |
| NFR-5 | Security | All database access is via SQLAlchemy parameterised queries; no f-string SQL anywhere | Code review + grep in the security checklist |
| NFR-6 | Security | CORS allows only the explicit deployed frontend origin and localhost dev origins — never `*` when credentials are enabled | Integration test asserting a rejected origin |
| NFR-7 | Security | 4xx/5xx responses return a stable error code and a safe message; stack traces and internal paths are never sent to the client | Integration test on a deliberately failing route |
| NFR-8 | Privacy | Resume content, extracted text, and PII never appear in application logs at any level | Log-capture assertion in tests |
| NFR-9 | Reliability | Application starts and serves the full deterministic feature set with `AI_API_KEY` unset | Integration test with the variable cleared |
| NFR-10 | Accessibility | Zero critical axe-core violations on all twelve pages; all interactive elements reachable and operable by keyboard; visible focus ring throughout | axe + manual keyboard pass in Phase 13 |
| NFR-11 | Accessibility | Text/background contrast ≥ 4.5:1 for body text, ≥ 3:1 for large text and UI boundaries | Contrast audit of the design tokens |
| NFR-12 | Maintainability | Backend ≥ 80 % line coverage on `analyzers/`, `services/`, and `security/`; every public function typed and docstring'd | `pytest --cov` gate |
| NFR-13 | Maintainability | Frontend passes `tsc --noEmit`, ESLint, and Prettier with zero warnings; `strict: true` in `tsconfig` | CI job |
| NFR-14 | Portability | `docker compose up` brings up API + database + frontend from a clean clone with no manual steps beyond copying `.env.example` | Verified in Phase 14 on a fresh clone |
| NFR-15 | Observability | Structured JSON logs with a request ID on every request; errors logged with the code and request ID but no user content | Manual review + log assertion |
| NFR-16 | Documentation | Every scoring category, every error code, and every environment variable is documented before Phase 15 closes | Phase 15 audit checklist |

---

## 6. Constraints

- **Solo developer, 30 calendar days**, alongside coursework. The schedule in
  `09-project-plan.md` assumes ~4 focused hours per day.
- **Free hosting tiers.** Render/Railway free instances sleep when idle; the README must
  state that the first request after idle takes ~30 s. Managed Postgres free tiers cap
  storage — another reason not to store resume text.
- **AI budget.** AI calls cost real money. Per-user daily quota, and a demonstration account
  with pre-generated (clearly labelled) sample analyses so the project can be demoed without
  live spend.
- **Local environment gaps (2026-07-25):** Python 3.13.3 is installed. **Git and Node.js are
  not.** Both must be installed before Phase 2 begins.

---

## 7. Open decisions for developer confirmation

These are the choices that change downstream work. Recommended answers are given; confirm or
override before Phase 2.

| # | Decision | Recommendation | Rationale |
|---|---|---|---|
| D1 | Token storage strategy | Short-lived access token (30 min) held in React memory + refresh token in an `httpOnly; Secure; SameSite=None` cookie | `localStorage` tokens are readable by any XSS payload. The memory+cookie split is the defensible answer in an interview and is not much more code |
| D2 | AI provider | Anthropic Claude API (`claude-opus-5`), model ID read from an environment variable | Strong structured-output support; the model is swappable without a code change |
| D3 | Resume text retention | Not stored by default; per-analysis opt-in checkbox | Data minimisation is the strongest privacy story and directly supports the privacy page |
| D4 | Skill taxonomy source | Hand-curated JSON (~300 skills + aliases) committed to the repo | Deterministic, auditable, no runtime dependency. Its incompleteness becomes a stated limitation |
| D5 | Job-description required/preferred split | Cue-based section detection with a documented fallback to "all required" | Honest about the heuristic rather than pretending to certainty |
| D6 | Backend hosting | Render (Docker deploy) + Render managed Postgres | Single provider for API and DB simplifies networking and the deployment guide |
