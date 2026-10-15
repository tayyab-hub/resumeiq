# Security and privacy review

15 October 2026. Implemented controls and observed tests, not a comprehensive penetration test or security guarantee.

## Findings and remediation

| Priority / finding | Remediation | Residual limit |
|---|---|---|
| P1: bcrypt truncated overlong passwords | Reject over 72 UTF-8 bytes, including multibyte input | Old previously truncated passwords are not automatically migrated |
| P1: trusted spoofable forwarding headers | Transport peer only; production disables proxy-header interpretation | Proxy users share conservative quotas |
| P1: quota check/increment races | Atomic locked consume before costly work, bounded key store | Process-local and reset on restart |
| P1: registration and parsing abuse | Registration quota, global mutation rate/concurrency, request body/receive limits | Multiple identities can still consume finite capacity |
| P1: refresh redemption race | User-row lock and conditional consumption in replacement transaction | PostgreSQL concurrency regression now runs in CI |
| P1: password change left access JWTs valid | User session version is carried and checked | Logout only revokes current refresh; copied access JWT lives until expiry |
| P1: dropped cookie-deletion response | Return the response with matching deletion attributes | Secure/Lax cookie forwarding and clearing verified through the live proxy |
| P1: unbounded PDF parsing | Subprocess; file/page/text/time bounds; Linux memory/CPU limits | No Windows address-space enforcement; hostile parser bugs remain possible |
| P1: AI payload and output boundaries | Derived fields only; strict nested schema, length/list/64 KB caps; no SDK retries | Generated advice may be wrong; disabled for RM0 |
| P1: dependency vulnerabilities | Upgrade and lock dependencies; enforce audits in CI | Advisory results change over time |
| P2: duplicate reports after retry | User-scoped idempotency key and database uniqueness | Same key returns first report without comparing payload hashes |
| P2: exception/path logging could reveal data | Safe error codes/classes and route templates; no traceback messages | Provider logs have separate policies |
| P2: weak scoring evidence presented too confidently | Sparse-evidence warnings; unassessed statement quality; exclude contacts/skill lists from statement metrics | Lexical heuristics still produce false matches and omissions |
| P3: inaccurate privacy/testing/licensing claims | Replace with dated measurements, real screenshots and explicit limitations | Documentation must track future changes |

No active compromise or confirmed credential leak was discovered. Baseline npm audit found 17 affected packages (2 critical, 10 high, 5 moderate). Baseline Python audit reported 18 advisories across pip, PyJWT and pytest. Current local and CI audits report no known vulnerabilities. Counts describe advisory findings, not proven exploitability in this application.

## Authentication and authorization

Access JWTs are memory-only. Refresh values are stored as SHA-256 hashes; the cookie is host-only, HttpOnly, SameSite=Lax, path `/api/v1/auth`, and Secure in production. Rotation consumes each refresh once. Password changes revoke old refresh sessions and invalidate old access versions; logout revokes the current refresh but a copied access JWT may survive for 30 minutes.

Production mutations require an exact allowed Origin. Missing Origin is accepted only in local/test mode; foreign Origin is rejected everywhere. No wildcard CORS. Non-browser clients can forge Origin, so it is not a substitute for bearer authentication. Reports are scoped to their owner for read, rename, deletion, export and regeneration. Tests cover two-user isolation and deletion cascades. React renders text instead of injecting report/model HTML.

## Data inventory

| Data | Retention |
|---|---|
| PDF bytes | Temporary request/worker lifetime; multipart may spool to temporary storage; no durable upload repository |
| Full extracted text | Per-analysis opt-in only, until report/account deletion |
| Evidence snippets and flagged statements | Retained even without full-text opt-in; may contain personal information |
| Filename, job description, scores/findings | Retained with report until deletion |
| Name/email | Account lifetime; email ownership is not verified |
| Password | bcrypt hash only |
| Refresh sessions | Hash, expiry/revocation metadata; expired entries pruned on issuance |
| App logs | Request ID, method, route template, status/duration and safe error codes/classes |

Application deletion is not a promise of immediate erasure from provider backups or infrastructure records. Verify actual provider retention before making a hosted privacy claim. Secrets must stay in private provider configuration, not code, screenshots or artifacts.

## AI boundary

`AI_ENABLED_OPT_IN=false`, no key and no model for the verified free deployment. A key alone cannot activate it. No paid calls were made; failure tests mock the provider. If explicitly enabled elsewhere, prompts contain curated skill identifiers, section keys, counts and issue codes. They exclude raw resume/job text, free-form names/titles and flagged statements. Derived skills can still be sensitive in context. Advice is labelled and cannot change the deterministic score.

## Remaining limits

No email verification/recovery, MFA, distributed throttling, antivirus scan or external penetration test. Restart resets quotas; shared proxy-peer quotas can also deny legitimate users. Public signup can exhaust free resources. Live cookie, persistence, deletion and provider billing checks are recorded separately from local/CI tests. Neon displayed a six-hour restore window; application deletion cannot promise immediate erasure from provider backups. Login throttling was observed live: HTTP 429 and Retry-After after the shared peer exhausted five attempts in 15 minutes.

The custom secret scanner checks known key formats, private-key markers, credential URL patterns and tracked `.env` files across tracked files/history. The historical `pass` documentation placeholder was inspected before a narrow exemption; other explicit test/documentation passwords are also recognized. This cannot establish the absence of every possible secret.

## Final browser session review

The final verification found that TanStack Query's account-independent keys retained private report data across sign-out/sign-in, even though the API enforced ownership. The auth provider now clears queries and cancels pending queries when sessions end and before installing a newly signed-in account. A regression creates an old in-flight query, switches accounts, resolves that old request and verifies that neither cached nor late private results remain.

A revoked access token now clears the browser session on `TOKEN_INVALID`/`TOKEN_MISSING`, while an incorrect password confirmation does not sign the user out. Expired access tokens retain the single-flight refresh/replay behavior. Successful password changes end the current browser session too and return to sign-in with an accurate explanation. The API's session-version revocation remains unchanged.

These are application security checks, not an external penetration test or security certification. They do not remove the documented logout access-token TTL, provider retention, process-local limits or shared-proxy availability constraints.

Additional controlled race regressions reproduced late refresh success/failure replacing or clearing a later login. Ending a session now cancels its in-flight refresh, increments a session generation and ignores responses/errors belonging to an earlier generation. The tests also verify that an old rejected request cannot sign out the new account or replay under the wrong session. These are deterministic automated race tests, not a claim of inducing that race on public infrastructure.
