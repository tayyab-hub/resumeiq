# Release readiness

## Main-branch release transition — 16 October 2026

The owner authorized merging PR #1 after fresh checks and moving the existing Vercel and Render resources to `main`. Pre-merge inspection confirmed the approved head `6468038465a50817c03d67a81f78263d2dfbb93b`, unchanged base `b1581348b43e529e78df52d41e8a6cc78be93aa0`, and both green head CI runs. The README badge and Render template now target `main`; this does not itself change provider tracking or prove a merge. Actual merge/deployment and live acceptance evidence will be recorded after completion.

## Historical verification — 15 October 2026

The following is the preserved pre-merge verification snapshot; branch, deployment and approval wording in it describes that date.

**READY TO MERGE for the personal portfolio demonstration**, subject to the owner's explicit merge approval. Core live workflows, authorization, persistence, migrations and required CI jobs pass. No known release-blocking defect remains. The direct browser password-form check is blocked by the browser tool's handoff rule; its real API behavior and automated React form integration pass. Authenticated restoration after an actual natural sleep was not separately reproduced; natural cold start and genuine access-token expiry recovery passed independently. These evidence limits are explicit below. This is not a production availability or security certification.

## Revision and automated gates

- Main remains `b1581348b43e529e78df52d41e8a6cc78be93aa0`.
- Final application fix: `30e9eafe20c4754bfa7fbecd617c76cbccfb5b95`.
- [PR #1](https://github.com/tayyab-hub/resumeiq/pull/1) is open, ready for review and unmerged.
- [Application CI](https://github.com/tayyab-hub/resumeiq/actions/runs/38743740803) and [independent push CI](https://github.com/tayyab-hub/resumeiq/actions/runs/38743732476): PASS, all four required jobs.

| Gate | Status | Current evidence |
|---|---|---|
| Backend lint/format | PASS | Ruff; 71 files already formatted |
| Local backend suite | PASS | 266 passed, one PostgreSQL-only skip, 49.12 seconds |
| PostgreSQL integration | PASS | 267 passed in 51.62 seconds, PostgreSQL 16 / Python 3.12 in CI |
| Coverage threshold | PASS | 91.79%, 1,340 statements / 110 missed; analyzers, services and security only |
| Frontend tests | PASS | 62 tests, including ten new session/privacy regressions |
| Frontend type/lint/format/build | PASS | Local and CI; production Vercel deployment Ready |
| Production containers | PASS | Both Docker images built; Linux startup/migration/health smoke in CI |
| Migrations | PASS | Disposable CI up/down/up; live Neon revision 0004 with nine application tables |
| Dependency audits | PASS | Fresh installed Python, all npm and runtime npm audits: zero known findings |
| Secret-pattern scan | PASS | Tracked/history scan; not a guarantee against every possible secret format |
| Genuine public sample | PASS | Export matches the deterministic engine; complete read-only browser report |

Commands: backend `ruff check`, `ruff format --check`, `pytest --cov=app/analyzers --cov=app/services --cov=app/security --cov-report=term-missing --cov-fail-under=80`, `python -m scripts.export_sample --check`, `pip-audit`; frontend `npm run typecheck`, `npm run lint`, `npm run format:check`, `npm test`, `npm run build`, both npm audit modes; `python scripts/scan_secrets.py --history`. The PDF child is exercised but not coverage-instrumented. Docker and real PostgreSQL checks run in GitHub Actions, not the local Windows host.

## Confirmed defects corrected in this pass

1. **Private browser cache survived account changes.** Shared query keys retained the previous account's results after logout/login. A failing regression reproduced this, including a late in-flight query. Session termination and new sign-in now clear queries and cancel outstanding query work. Backend ownership checks were already correct.
2. **Revoked sessions left a signed-in shell.** Only expired-token renewal failures cleared auth UI. `TOKEN_INVALID` and `TOKEN_MISSING` now end the session, while wrong password-confirmation errors preserve it. Expiry renewal still retries only once.
3. **Password-change UI contradicted revocation.** The backend invalidates every session, including the current one. The form now clears the current session and returns to sign-in with that accurate explanation. A component integration test covers the successful form path.
4. **Mobile History caused document overflow.** An absolutely positioned screen-reader label escaped the table's scrolling container. Making that container positioned confines the label and preserves the existing table. Live document widths after deployment: 390/390, 768/768 and 1280/1280; the table scrolls inside its container.

5. **Late refresh responses crossed session boundaries.** Regressions reproduced an old refresh success replacing a new login and an old failure clearing it. A session generation now guards refresh completion and protected-request retries/errors; ending a session aborts its pending refresh. Old protected requests are not replayed under the next account. Ten session regression tests cover these fixes, including concurrent expiry renewal.

No dependency, scoring, database schema or backend behavior changed in this final pass.

## Actual hosted acceptance

| Check | Status | Executed evidence |
|---|---|---|
| Landing/sample and HTTPS routing | PASS | Public website and fictional sample; authenticated report deep link/reload |
| Direct/proxied health | PASS | Both return 200, database ok and no-store |
| Fictional registration | PASS | Actual browser registration plus two separate live API accounts |
| Browser reload/persistence | PASS | Session-restoration loading state then the same saved 76-point report |
| Browser login/logout/re-login | PASS | Final 30e9eaf deployment: changed-password login, two saved reports, sign out, reload still signed out, re-login restores both reports |
| Natural access-token expiry | PASS | Retained token from 13:07:41 UTC; Dashboard at 13:41:00 produced two TOKEN_EXPIRED/401 requests, one refresh/200 at 13:41:01, then both requests/200. Same report displayed, no manual token or TTL changes |
| Refresh rotation/replay | PASS | Actual proxy API rotates cookie; replay of old refresh token returns 401 |
| Secure cookie and Origin | PASS | Host-only, HttpOnly, Secure, SameSite=Lax, /api/v1/auth; foreign/absent Origin rejected |
| Logout cookie clearing | PASS | Live API 204 with Max-Age=0; subsequent refresh rejected |
| Password change/revocation | PASS | Live API change; old access and refresh rejected; new password login succeeds |
| Direct browser password-form submission | BLOCKED | Browser automation policy reserves credential changes for user handoff. The actual API and automated React form test pass; no handoff was requested for this redundant check |
| Browser reaction to external revocation | PASS | Password changed through actual API; existing final-build browser token rejected on profile save, immediately returned to sign-in; login with new password succeeded |
| Fictional PDF analysis | PASS | Actual browser upload and independent API uploads; real text extraction and job parsing |
| Score/evidence/recommendations | PASS | 76.31/100 rounds to 76; eight categories, seven matched/three partial/five missing skills; visible evidence, missing section and rule-based recommendations |
| AI-disabled result | PASS | Actual report says no provider configured; complete deterministic output |
| Idempotent retry | PASS | Repeated live request key returns the same ID with 200, one saved report |
| Hosted JSON download | PASS | Clicked Download; actual 10,769-byte JSON file parsed; title, 76 score, eight categories/100 maxima, skill counts and recommendations agree with the report |
| Export privacy | PASS | Reviewed defined export fields; no auth tokens, passwords, database URLs, user ID or full resume-text field. Export intentionally contains fictional statement findings, job information and report metadata |
| Account ownership | PASS | Cross-user GET, PATCH and DELETE all return 404 |
| Isolated history | PASS | API A/B ownership and history checks; same browser SPA switches from A with two reports to B with zero dashboard/history entries, without reloading between accounts |
| Analysis deletion | PASS | Owner deletion 204, subsequent GET 404 |
| Selective account deletion | PASS | API A removed while B's report remained readable; both API accounts then deleted. Browser B deleted through the real confirmation form; browser A and its two reports deleted through the API |
| Database privacy and cleanup | PASS | Final read-only SQL at 13:45 UTC: neondb, migration 0004, nine application tables, zero rows in each. Only the four newly created fictional accounts were deleted through the application; no SQL deletion or unknown-data cleanup |
| Cache and logs | PASS | Private API responses no-store; inspected application logs contain request metadata/error codes, not fictional resume text, credentials or tokens |
| Responsive interface | PASS | Real mobile/tablet/desktop form, results, evidence, dashboard, navigation and History checks; mobile History defect corrected |
| Forms/loading/errors | PASS | Registration/analysis loading labels, session restore, short job-description validation and focused field; API security errors are structured |
| Basic accessibility | PASS | Named controls, keyboard focus/validation, expandable categories and mobile navigation; no formal WCAG audit claimed |
| Browser console | PASS | Final production tab: no warning/error entries; actual two-report Recharts trend rendered correctly. Old tabs across deployments can need reload |
| Natural Render sleep/wake | PASS | Logs show shutdown at 12:35:50 UTC, automatic startup at 13:04:45 and proxied refresh at 13:04:48 after first frontend visit at 13:04:12; registration and PDF analysis succeeded without manual restart |
| Authenticated restoration after actual sleep | NOT RUN | Attempted an idle window while retaining authentication, but Render stayed awake. The earlier genuine cold start and later expired-token recovery passed separately; this combined case is not claimed |
| External penetration/load test | NOT RUN | No external certification or load capacity claim |
| Paid AI | NOT RUN | Intentionally disabled; no billable requests |

This pass's disposable API helper completed **37 assertions**; a second browser-fixture helper completed **nine assertions** for persistence, actual password change/revocation and cleanup. Both API and both browser accounts were removed. The expired-token tab deliberately retained its pre-rollout JavaScript to preserve its real 30-minute token; the positive expiry path is also covered in the final automated suite. All later browser login, revocation, account-switch and deletion checks used 30e9eaf. The initial six-hour-old report was historical evidence only; current results above are fresh except explicitly identified automated coverage. Malformed/oversized PDF, concurrent refresh, resource-limit and migration failure cases are covered by the fresh automated suites; they were also tested live during the earlier release pass.

## Hosting and RM0 conditions

| Provider | Status | Inspected current configuration |
|---|---|---|
| Vercel | PASS | Existing resumeiq project, Hobby, feature branch, Ready 30e9eaf production deployment; Node 22, frontend root, Vite, npm ci, npm run build, dist; no project environment variables |
| Render | PASS | Existing resumeiq-api service, Free, Singapore, Docker, one worker, manual deployment, health /api/v1/health; backend e19b05e is byte-for-byte unchanged by all final frontend fixes |
| Neon | PASS | Existing dedicated resumeiq-prod, production, neondb, PostgreSQL 18, AWS Singapore, Free/no expiration, migration 0004 and nine application tables |
| Private configuration | PASS | Production/debug false, exact frontend Origin, AI false, bootstrap false, dedicated pooled runtime and direct migration URLs both require TLS; secret values never printed; only necessary flags and connection metadata were inspected privately and re-masked |
| Cost | PASS | No new resource, card, upgrade, paid disk/domain or AI call. Existing free plans retained |

Dated account snapshot: Render **7.15/750 shared hours**, **7 MB/5 GB bandwidth**, **2/500 pipeline minutes**, no card, **$0 current/projected**. Neon **0.81 CU-hours**, **32.57 MB storage**, **1.58 MB history**, **535.11 kB transfer**, six-hour history retention. Vercel showed **14.4 MB/100 GB transfer**, **541/1,000,000 CDN requests** and **12 minutes build CPU** in its displayed last-30-days period. Usage can lag. The other existing Render service shares workspace quotas but was not modified or tested.

The Neon console's own `pg_stat_ssl` query returned false for its internal console connection; that does not measure the Render client. Render's two private connection settings were independently checked for `sslmode=require`, correct driver and dedicated database host without printing credentials; production startup rejects non-TLS connection strings.

[Render Free rules](https://render.com/docs/free) include idle sleep, 750 shared monthly hours and suspension/build disabling when no-card quotas are exhausted. Two continually active services cannot both fit in 750 monthly hours. [Vercel Hobby](https://vercel.com/docs/plans/hobby) is for personal/non-commercial use; [Neon Free](https://neon.com/pricing) has finite allowances. RM0 is conditional on retaining these settings and limits; uninterrupted availability is not promised. No keep-alive traffic was installed.

## Remaining limitations and documentation

Recharts 2.15.4 is on an inactive major branch; its npm notice and the official v3 migration guide were checked. No current advisory or observed compatibility defect justifies a late major upgrade. This is documented maintenance risk in [dependency evidence](13-dependency-audit.md), not a suppressed warning.

Other limits remain: no OCR/DOCX, English lexical heuristics, no hiring prediction, process-local quotas, shared proxy-peer throttling, no email verification/recovery/MFA, temporary upload spooling, retained evidence excerpts and provider backup retention. A copied access JWT can survive logout until its 30-minute expiry. No claim is made that zero audit findings proves security.

All eleven existing JPEG screenshots were decoded, visually inspected and matched to the current interface; all 65 relative Markdown targets resolved. The screenshots remain genuine historical captures of fictional data and were retained. The README explains the scoring, ownership, bounded processing, session and deployment engineering, with real URLs and the feature-branch CI badge.

Earlier sample-ordering investigation remains documented: one older CI run failed equality without a diff while its parallel run passed; repeated local exports did not reproduce that exact event. Canonical database relationship serialization fixed a separately demonstrated ordering defect. Current sample checks and both application CI runs pass; the old failure's precise cause is not asserted.

The exact [post-merge transition](11-deployment.md#post-merge-transition--prepared-not-executed) is prepared. Neither main nor provider branch tracking has changed. Final merge approval remains with the owner.
