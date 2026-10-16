# Testing and evidence

See [dated release readiness](10-release-readiness.md). Local success alone does not prove a public deployment works.

## Automated layers

Analyzer tests cover aliases/boundaries, headings, dates, sparse inputs, statement exclusions, quantification, exact rounding and rescaling. API tests cover registration/login/rotation/logout, password invalidation, profile changes, uploads, report CRUD, two-user isolation, opt-in retention, cascades and AI-off/provider-failure behavior. Release tests add UTF-8 password limits, atomic quotas, Origin/body/metadata limits, production config, PDF bounds, refresh concurrency and upload idempotency.

Frontend tests use accessible queries for components, sample isolation, password bytes and single-flight restoration. TypeScript, lint, formatting and production build are separate gates.

## Database distinction

Local tests without `TEST_DATABASE_URL` use SQLite and do not verify PostgreSQL row locks or migration semantics. CI supplies disposable PostgreSQL 16 `resumeiq_test`. The fixture accepts only a local service host and a database ending `_test`, creates a unique schema per test, upgrades real Alembic migrations and drops only that generated schema afterwards. Refresh concurrency uses independent connections. Migration up/down/up runs only in the disposable CI database, never Neon production.

## CI

The workflow runs the PostgreSQL-backed suite, migration reversal/reapplication, deterministic sample comparison, both Docker builds and actual Linux startup/health. Frontend types/lint/format/tests/build and pip/npm/history audits are enforced. No `|| true` audit escapes. CI first passed these gates on `7bedd2c`; final-head status is recorded in release readiness. A subsequent run failed the sample comparison while a parallel run passed. The check now prints a fictional-data diff, and response serialization now canonicalizes database collections with a reversal regression test. The old failure did not include a diff, so its exact cause cannot be proven retrospectively.

## Coverage

The 80% gate covers `app/analyzers`, `app/services`, `app/security`. Local result: 1,340 statements, 110 missed, **91.79%**, 266 passed and one PostgreSQL-only skipped on 15 October 2026. Routes, repositories, schemas, config and scripts are outside the denominator. The child PDF parser is exercised by integration tests but is not coverage-instrumented. Coverage is not a security score.

## Browser and public acceptance

Local production-build checks: sample viewing, 390-pixel responsive overflow check, fictional account registration, same-origin session restoration, real PDF upload, evidence expansion, JSON download and saved History. Real JPEGs are in `docs/screenshots`.

Executed public acceptance covers HTTPS frontend/backend connectivity, Secure/HttpOnly/Lax refresh forwarding and rotation, logout/reload, persistence across restart and fresh login, ownership isolation, deletion, no-store, trusted Origin, AI-off and direct read-only verification of Neon records. The complete PASS/FAIL/NOT RUN matrix is in release readiness. A backend restart is not evidence of a natural cold start.

Reproduce with README commands. `python -m scripts.export_sample --check` compares the static sample to engine output. The optional extractor benchmark uses the previously installed PyMuPDF only in a review environment; it is not a runtime/CI requirement.
