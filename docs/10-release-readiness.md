# Release readiness — 15 October 2026

**COMPLETED AND VERIFIED for the public portfolio demo**, subject to the limitations and unexecuted checks below. The feature branch is deployed; this does not authorize merging main or promise production-grade availability.

## GitHub and automated gates

- Baseline/main: `b1581348b43e529e78df52d41e8a6cc78be93aa0`, unchanged.
- Branch: `codex/resumeiq-portfolio-release`; [PR #1](https://github.com/tayyab-hub/resumeiq/pull/1), unmerged.
- Application revision: `e19b05ed7f4f8457c88b4f49cc7f0f9b559f4bc2`. Later documentation/screenshot commits do not alter the deployed application code.
- [Application CI](https://github.com/tayyab-hub/resumeiq/actions/runs/38692504076) and [independent push CI](https://github.com/tayyab-hub/resumeiq/actions/runs/38692499745): all four jobs passed.
- PostgreSQL 16 / Python 3.12: **267 passed**, no failures, in 52.54 seconds. Real migrations, API persistence/ownership/deletion and concurrent refresh redemption. Migration up/down/up ran only on disposable CI databases.
- Local Python 3.13 / SQLite: **266 passed, one PostgreSQL-only skipped**, no failures, in 52.04 seconds.
- Selected coverage: **91.79%**, 1,340 statements / 110 missed. Scope: `app/analyzers`, `app/services`, `app/security`, not the entire app. The PDF child is exercised but not coverage-instrumented.
- Frontend: **52 passed**; TypeScript, ESLint, formatting and production build passed locally and CI.
- Both production Docker images built; actual Linux startup/migration/health smoke passed in CI.
- Python, all-dependency npm and production npm audits: no known findings. Tracked/history secret-pattern scan passed. [Advisory/version evidence](13-dependency-audit.md) records the baseline's 17 npm packages and 18 Python advisory entries, exposure and upgrades.

Executed commands: backend `ruff check`, `ruff format --check`, `pytest --cov=app/analyzers --cov=app/services --cov=app/security --cov-report=term-missing --cov-fail-under=80`, `python -m scripts.export_sample --check`, `pip-audit`; frontend `npm run typecheck`, `npm run lint`, `npm run format:check`, `npm test`, `npm run build`, both npm audit modes; repository `python scripts/scan_secrets.py --history`. Docker and Alembic commands are in `.github/workflows/ci.yml`.

## Actual deployment and RM0

| Component | Verified deployment |
|---|---|
| Frontend | https://resumeiq-lemon-eight.vercel.app — Vercel Hobby, Node 22, Vite, root frontend, npm ci, npm run build, dist |
| Backend | https://resumeiq-api-zqip.onrender.com — Render Free, Docker, Singapore, 0.1 CPU / 512 MB, one worker, manual deployment |
| Database | Existing Neon resumeiq-prod, production branch, AWS Singapore, PostgreSQL 18, neondb, recurring Free with no expiration |
| Fixed monthly cost | **RM0** under inspected account conditions; no paid compute/disk/domain, card, upgrade or AI request added |
| AI | Explicitly disabled; no provider key/model configured |

Render Hobby billing before provisioning: no card on file, $0 current/projected, 3.93/750 shared hours, 4 MB/5 GB bandwidth, 0/500 pipeline minutes. Post-deployment: still no card and $0 current/projected, 4.27/750 hours. Usage is a dated snapshot and can lag. The existing SCAMGUARD service was not changed; no ResumeIQ service existed before this one. Vercel was verified Hobby. Neon showed a zero-use dedicated Free project before migration.

[Render Free rules](https://render.com/docs/free) specify 750 shared monthly workspace hours, idle sleep after 15 minutes, wake delay, and suspension/build disabling rather than overage billing without a payment method. Two continuously active services cannot both fit within 750 hours/month. No keep-alives were added. [Vercel Hobby](https://vercel.com/docs/plans/hobby) is personal/non-commercial; [Neon Free](https://neon.com/pricing) has finite compute/storage/transfer limits. Reassess billing and terms before future changes; no availability guarantee is made.

A read-only Neon preflight confirmed zero application tables before bootstrap. Startup applied migration 0004. Independent SQL confirmed nine application tables, three fictional users, two reports and zero stored full-text resumes. A fresh login retrieved a report after backend replacement. After application-level test-account deletion, a separate SQL query confirmed **zero rows in all nine tables**, including child findings and refresh sessions. No reset, downgrade or destructive cloud SQL was used. The one-time bootstrap setting is disabled after initial migration; subsequent startup upgrades remain fail-fast and lock-protected.

## Public acceptance matrix

| Check | Result | Executed evidence |
|---|---|---|
| HTTPS landing and SPA paths | PASS | Public landing/sample; protected report deep-link reload and navigation |
| Direct/proxied health and database | PASS | HTTP 200, status/database ok, Cache-Control no-store |
| Registration/login | PASS | Fictional browser account and two API accounts |
| Browser session restoration | PASS | Reload restored dashboard and saved report through the proxy |
| Refresh cookie | PASS | Host-only, Secure, HttpOnly, SameSite=Lax, Path=/api/v1/auth |
| Rotation/replay/CSRF | PASS | Refresh rotates; old token 401; foreign and absent Origin 403 |
| Logout | PASS | 204 clears matching cookie; refresh 401; browser sign-out/reload/sign-in |
| PDF/job parsing/score | PASS | Real fictional PDF in browser/API; score 76, seven matched required skills, four measurable statements |
| Evidence and skill gaps | PASS | Expanded category and visible excerpts; matched/related/not-detected groups |
| AI-disabled fallback | PASS | Rule-only result and provider-not-configured explanation |
| Duplicate submission | PASS | Same idempotency key returned 200 and original report ID |
| History/persistence | PASS | Browser History, report reload and independent Neon query |
| Backend restart persistence | PASS | Fresh login retrieved the same report after successful Render deployment |
| Cross-user isolation | PASS | Other account's read and rename requests returned 404 |
| Profile/password change | PASS | Profile update; old access/refresh invalidated; new password login |
| Analysis/account deletion | PASS | 204; old access rejected; browser returned to sign-in; all nine Neon tables empty |
| Malformed/oversized PDFs | PASS | Rejected malformed PDF and payload over 5 MB |
| Invalid/empty input | PASS | API short description rejected; browser focused useful description validation |
| Anonymous sample | PASS | Available after test accounts were deleted; Sign in/Create account navigation; no mutation controls |
| Desktop/tablet/mobile | PASS | Actual captures; 768×1024 and 390×844 viewports without horizontal document overflow |
| Login throttling | PASS | Live 429 TOO_MANY_ATTEMPTS and Retry-After after shared-peer quota exhaustion |
| Final date/ordering fixes | PASS | Current-date experience; report survived final rollout; canonical finding order |
| Private cache/headers | PASS | Live auth/results no-store; frontend security headers configured and application rendered |
| Browser errors | PASS with recovery | A tab spanning a deployment lost an old lazy chunk; Reload restored form/session; no persistent error |
| Natural idle cold-start recovery | NOT RUN | Backend replacement tested; controlled uninterrupted 15-minute idle/wake cycle not completed |
| JSON export | PASS locally; hosted download NOT RUN | Local browser download completed; public button/render checked, download not repeated |
| Paid AI | NOT RUN intentionally | No billable calls; malformed/timeout/failure cases tested with mocks |
| Load/external penetration test | NOT RUN | No SLA or comprehensive security certification claimed |

The live helper recorded 37 passing API assertions across creation, restart and cleanup, in addition to the browser/SQL checks above. An initial cleanup request omitted the required confirmation=DELETE field and was rejected; the corrected request passed. Repeated logins also reached the intended rate limit. These were not counted as successful requests.

## Investigated failures and remaining limits

One earlier CI run at 45b6e9f failed sample equality while its parallel run passed. Twenty repeated exports and eight hash-seed runs did not reproduce it locally. Diagnostics now print a fictional-data diff. An independent ordering defect was confirmed and fixed: unordered database relationships could change the response. Canonical serialization and a reversal regression now cover this. Both final application CI runs pass. The original failure had no diff, so its exact cause is not claimed proven.

The initial Vercel main-branch import was intentionally build-blocked and never published. Branch tracking was changed before the successful release build. Automatic approval review rejected an empty-project shortcut; the explicit named repository import succeeded instead.

Limits: no OCR/DOCX, English lexical heuristics, no hiring prediction, process-local quotas reset on restart, shared proxy-peer throttling can deny legitimate visitors, no email verification/recovery/MFA, temporary upload spooling, retained excerpts and provider backup retention. A copied access JWT may survive logout until its 30-minute expiry. Neon displayed a six-hour restore window. Parser vulnerabilities and unknown advisories remain possible. [Security review](07-security-privacy.md)

## Portfolio and developer action

Open the [public sample](https://resumeiq-lemon-eight.vercel.app/sample), expand a score row, compare related/not-detected skills and read limitations. For the full workflow, register a disposable account and use docs/samples/fictional-resume.pdf with fictional-job.txt. [Eleven genuine screenshots](screenshots/README.md) cover landing, form, dashboard, results, evidence, gaps, history and responsive views.

Only final merge approval remains a developer decision. The PR remains unmerged; no sign-in or routine engineering work is delegated back.
