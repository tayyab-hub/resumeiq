# Release readiness — 15 October 2026

**PARTIALLY COMPLETED — hosted workflow verification in progress.** Do not treat prepared configurations as a completed deployment.

## Source and CI

- Baseline/main: `b1581348b43e529e78df52d41e8a6cc78be93aa0`.
- Feature branch: `codex/resumeiq-portfolio-release`.
- [PR #1](https://github.com/tayyab-hub/resumeiq/pull/1), unmerged.
- [CI at 7bedd2c](https://github.com/tayyab-hub/resumeiq/actions/runs/38687935917): all four jobs green.
- PostgreSQL 16 / Python 3.12: **265 passed**, including concurrent refresh redemption, migrations up/down/up and deterministic sample verification.
- Local Python 3.13 / SQLite: **264 passed, one PostgreSQL-only skipped**, no failures.
- Selected backend coverage: **91.79%**, 1,340 statements/110 missed; analyzer/service/security modules only. Child parser exercised but not coverage-instrumented.
- Frontend: **52 passed**, types/lint/format/production build passed locally and CI.
- Both production images built; Linux startup/migration/health smoke passed in CI.
- Python audit: no known vulnerabilities. npm all-dependency and production audits: zero findings. History/tracked pattern scan passed after inspecting a documentation-placeholder false positive; scanner limitations are documented.

## Executed local browser checks

Production build with same-origin API proxy: fictional account registration; refresh restores session; sample readable; real fictional PDF upload returns score 76; evidence expands; JSON export downloads; History shows the saved record. Sample at 390 × 844 has no horizontal document overflow. Real captures: landing-desktop.jpg, sample-desktop.jpg, sample-mobile.jpg and analysis-desktop.jpg. Local screens are not live-hosting proof.

## Provider checks so far

Vercel account is Hobby. Render Hobby has no card on file, $0 current/projected charges, 3.93/750 shared free instance hours, 4 MB/5 GB bandwidth and 0/500 build minutes. Its existing single service belongs to SCAMGUARD; it was not modified. No ResumeIQ Render service existed before setup.

Neon existing project `resumeiq-prod`, production branch, AWS Singapore, Free plan, PostgreSQL 18: read-only query returned database `neondb`, role `neondb_owner`, and zero application tables. Project usage was zero. Private connection values are not recorded here.

Public frontend/backend URLs, migrations on Neon, secure cookie forwarding, live CRUD/persistence, quota behavior and final cost recheck are still pending. AI remains explicitly off. No payment method, paid instance, disk, domain, trial or AI call was added.

## Changes and residual limits

See the [security findings](07-security-privacy.md), [architecture](03-architecture.md) and [PDF benchmark](12-pdf-migration.md). Key fixes include password byte limits, atomic sessions/quotas, password invalidation, correct cookie deletion, request/PDF bounds, idempotent upload, strict AI output validation, sparse-evidence scoring and a genuine sample.

Remaining product limits: no OCR/DOCX, English lexical heuristics, no hiring prediction, process-local quotas reset on restart, shared proxy-peer quotas, no email verification/recovery/MFA, temporary upload spooling, retained evidence snippets, and provider backup retention. Logout cannot revoke a copied access JWT before expiry.

## Developer actions

Final merge approval is required. Any provider action that remains blocked will be recorded here after independent engineering and verification finish; routine engineering is not delegated to the developer.
