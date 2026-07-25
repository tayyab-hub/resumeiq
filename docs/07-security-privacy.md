# ResumeIQ — Security and Privacy Plan

> Phase 1 deliverable. Controls are implemented across Phases 3–5 and audited in Phase 13.
> Sections 2 and 6 double as the security testing checklist.

**Threat model in one sentence:** the application holds credentials and résumé-derived
personal data for many users, is reachable from the public internet, and accepts an
attacker-controlled file and an attacker-controlled text blob on every analysis request.

---

## 1. Assets, ranked

| Asset | Impact if compromised |
|---|---|
| Password hashes | Credential stuffing against the users' other accounts |
| Résumé-derived data (skills, employers implied by bullets, flagged statements) | Personal data disclosure; the résumé itself is the most sensitive document most users upload anywhere |
| Session tokens | Full account takeover |
| AI provider API key | Financial loss, quota exhaustion, provider account suspension |
| Database credentials | Total compromise |

---

## 2. Controls by risk

### R1 — Plaintext or weakly hashed passwords

- bcrypt via `passlib`, cost factor ≥ 12. Not SHA-256, not MD5, not an unsalted digest.
- The plaintext exists only in the request body and the local variable passed to `hash()`.
- `password_hash` appears in no Pydantic **response** model anywhere in the codebase.
- Minimum 10 characters with a letter and a digit, enforced server-side (client-side Zod is
  UX, not a control).
- **Test:** register, then query the row directly and assert the stored value neither equals
  nor contains the plaintext, and that it begins with a bcrypt identifier.

### R2 — Broken authentication

- JWT HS256 signed with a ≥ 32-byte secret from the environment. No default value in code —
  the application refuses to start if `JWT_SECRET` is unset.
- Access token TTL 30 minutes; refresh token TTL 7 days.
- Refresh tokens are stored as **SHA-256 hashes**, so a database dump yields no usable
  sessions.
- Logout sets `revoked_at`; every refresh checks expiry *and* revocation.
- `get_current_user` verifies signature, expiry, and that the user still exists and is active.
- **Test:** wrong-secret token, expired token, malformed token, `alg: none` token, and a token
  for a deleted user each return 401.

### R3 — Broken access control / IDOR

**The highest-severity risk in this application, and the one most likely to be got wrong.**

- Every analysis query takes `owner_id` as a **required** parameter inside the repository
  function. Ownership is a property of the query, not a check a route author might forget.
- Non-owned resources return **404**, never 403 (FR-G3).
- UUID primary keys, so IDs cannot be enumerated even if the check regressed.
- **Test:** create user A and user B, each with an analysis; assert A gets 404 on B's ID for
  `GET`, `PATCH`, and `DELETE`, and that A's list contains exactly one item.

### R4 — Unsafe file upload

Validation runs in this order, cheapest and most decisive first:

1. Extension is `.pdf` (case-insensitive).
2. Declared `Content-Type` is `application/pdf`.
3. **Magic bytes start with `%PDF-`** — the only one of the three an attacker cannot forge
   trivially, and therefore the authoritative check.
4. Size ≤ 5 MB, enforced while streaming so an oversized body is aborted rather than buffered.
5. PyMuPDF opens it successfully and reports it is not encrypted.

Additional controls:

- The uploaded filename is **never** used to build a path. It is sanitised
  (`os.path.basename`, then an allowlist regex, then truncation to 255 chars) and stored only
  as a display label.
- Files are processed in memory or in a `NamedTemporaryFile` deleted in a `finally` block.
  Nothing is persisted.
- The sanitised filename is rendered through React (auto-escaped) — never `dangerouslySetInnerHTML`.
- **Tests:** `.exe` renamed to `.pdf` → 415 · a 6 MB file → 413 · a 0-byte file → 422 ·
  `../../etc/passwd.pdf` → sanitised and no traversal · a temp-dir fixture asserts no residue
  after both success and failure paths.

### R5 — Injection

- **SQL:** SQLAlchemy ORM with bound parameters throughout. No f-string or `%`-format SQL
  anywhere. A grep for `execute(f"` and `text(f"` is part of the Phase 13 checklist.
- **XSS:** React escapes by default; `dangerouslySetInnerHTML` is banned by an ESLint rule
  rather than by discipline. Résumé and JD text is rendered as text, never as HTML.
- **Prompt injection:** a résumé could contain "ignore previous instructions". Mitigations:
  résumé content is passed as clearly delimited data, not as instructions; the system prompt
  states that document content is untrusted data; AI output is schema-validated before use;
  and — most importantly — **the AI has no tools and no database access**, so the worst
  outcome is a bad suggestion, not an action.
- **Test:** an analysis whose résumé contains an injection string still returns a
  schema-valid response and does not echo the instruction as a recommendation.

### R6 — Secrets exposure

- `.env` in `.gitignore` from the first commit, before any secret exists.
- `.env.example` lists every variable with placeholder values and a comment.
- Settings load via `pydantic-settings`; no secret has a code default.
- Secrets are set in the Render/Vercel dashboards, never committed.
- Phase 15 audit: `git log -p | grep -iE "sk-ant|api[_-]?key|password.*="` over the full
  history. **If a secret was ever committed, rotating it is mandatory — deleting the line is
  not sufficient**, because it remains in history.

### R7 — Brute force and abuse

| Endpoint | Limit |
|---|---|
| Login | 5 failures / 15 min, keyed on email **and** IP |
| Register | 10 / hour per IP |
| Analysis creation | 20 / day per user |
| AI enrichment | 20 / day per user |

Login responses are identical for "unknown email" and "wrong password", including
approximate timing (bcrypt runs against a dummy hash on the unknown-email path so the
response time does not reveal account existence).

### R8 — Information disclosure via errors and logs

- One global exception handler. Unhandled exceptions return `INTERNAL_ERROR` plus a request
  ID; the detail is logged server-side against that ID.
- No response ever contains a stack trace, a file path, a SQL fragment, or a library name.
- `DEBUG=false` in production; FastAPI's `/docs` and `/redoc` are disabled in production.
- **Logging rules:** log the request ID, route, status, duration, error code, and user ID.
  Never log résumé text, JD text, email addresses, tokens, passwords, or the AI prompt body.
- **Test:** a route forced to raise returns a body containing no `"Traceback"`, no `.py`
  path, and no exception class name.

### R9 — Misconfigured CORS

- Explicit origin allowlist; `allow_credentials=True`; enumerated methods and headers.
- Never `allow_origins=["*"]` with credentials — the browser rejects it, and the attempt
  usually means someone reached for the wildcard under time pressure.
- **Test:** a request with `Origin: https://evil.example` receives no
  `Access-Control-Allow-Origin` header.

### R10 — Transport and headers

HTTPS everywhere (Vercel and Render terminate TLS). Refresh cookie is
`httpOnly; Secure; SameSite=None` — `SameSite=None` is required because the frontend and API
are on different registrable domains, and it is safe here only *because* `Secure` is set and
the origin allowlist is strict. Response headers: `X-Content-Type-Options: nosniff`,
`X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`, and HSTS in production.

### R11 — Dependency risk

`pip-audit` and `npm audit` run in CI and are re-run in Phase 13. Versions are pinned in
`requirements.txt` and `package-lock.json`. Every new dependency is justified in the PR
description — an unexplained dependency is a review blocker.

---

## 3. Privacy plan

Résumés contain full name, address, phone, email, employment history, and sometimes date of
birth or nationality. This project's privacy posture is a design feature, not a policy page.

### Data minimisation — what is and is not kept

| Data | Stored? | Rationale |
|---|---|---|
| The PDF file | **Never** | Deleted in a `finally` block; there is no table and no bucket that could hold it |
| Full extracted résumé text | **Not by default** | Per-analysis opt-in only. Enforced by the DB constraint `CHECK (store_resume_text OR resume_text IS NULL)` |
| Flagged weak statements | Yes, ≤ 30 rows, ≤ 600 chars each | The results page must show the user their own bullets for the feedback to be usable |
| Skill evidence snippets | Yes, ≤ 240 chars | A match the user cannot verify is not credible |
| Job description text | Yes, in full | Employer content, not the user's personal data |
| Score, sections, recommendations | Yes | Derived data; the product |
| Email, name, password hash | Yes | Required for accounts |

### User control

- Delete any analysis at any time (hard delete, cascading).
- Delete the entire account, which cascades to every child row.
- Per-analysis retention choice for résumé text, defaulted to off.
- The privacy page states all of the above in plain language, plus what the AI provider
  receives.

### Third-party data flow

The AI provider receives a **bounded, derived summary**: matched and missing skill names, the
text of flagged bullets, which sections are absent, and the job title. It does **not** receive
the résumé file, the full résumé text, the user's name, email, phone, or address. The prompt
is assembled from analysis output, not from the raw document.

This is stated explicitly on the privacy page. It is also the honest answer to the interview
question *"you sent someone's résumé to a third-party API — what did you actually send?"*

### Logging

No résumé content, JD content, or PII at any log level, in any environment. Phase 13 includes
a test that captures log output during a full analysis and asserts that neither a known
résumé phrase nor a test email address appears in it.

### Demonstration data

The demo account contains analyses built from a **fictional résumé for a fictional person**,
committed to `backend/tests/fixtures/` and labelled as demonstration data in the file itself,
in the README, and in the UI. No real person's résumé appears in any screenshot, fixture, or
seed script.

---

## 4. Statement of limitations (for the README and privacy page)

Publishing these is part of the security posture, not a weakness:

- No third-party penetration test has been performed.
- No formal security audit or compliance certification (SOC 2, ISO 27001, GDPR DPA) exists.
- Email addresses are not verified; a user can register with an address they do not control.
- No multi-factor authentication.
- Backups and disaster recovery are whatever the hosting provider's free tier offers.
- This is a portfolio project. It should not be used to process résumés belonging to other
  people without their knowledge.

---

## 5. Secret inventory

| Variable | Where set | Rotation |
|---|---|---|
| `DATABASE_URL` | Render environment | Via provider on suspicion |
| `JWT_SECRET` | Render environment (≥ 32 random bytes) | Rotation invalidates all sessions — acceptable |
| `AI_API_KEY` | Render environment | Immediately if exposed |
| `CORS_ORIGINS` | Render environment | Not secret, but environment-specific |
| `VITE_API_BASE_URL` | Vercel environment | **Public by nature** — it is compiled into the client bundle. Never put a secret in a `VITE_`-prefixed variable |

That last row is worth remembering: every `VITE_*` variable ships to the browser.

---

## 6. Security testing checklist (Phase 13)

Automated:

- [ ] Password is hashed, and the hash is absent from every response
- [ ] Expired / malformed / wrong-secret / `alg:none` tokens all return 401
- [ ] Cross-user `GET`, `PATCH`, `DELETE` all return 404
- [ ] List endpoint returns only the caller's rows
- [ ] Non-PDF, oversized, empty, corrupt, encrypted, and traversal-named uploads all rejected
- [ ] No temporary file remains after success or failure
- [ ] Rate limits return 429 with `Retry-After`
- [ ] Unknown email and wrong password are indistinguishable in body and timing
- [ ] Disallowed CORS origin receives no allow header
- [ ] Forced 500 leaks no path, trace, or class name
- [ ] Logs during a full analysis contain no résumé text and no email address
- [ ] Application starts and analyses successfully with `AI_API_KEY` unset

Manual:

- [ ] `grep -rn "execute(f\"\|text(f\"" backend/` → no results
- [ ] `grep -rn "dangerouslySetInnerHTML" frontend/src` → no results
- [ ] `git log -p | grep -iE "sk-ant|api[_-]?key|secret"` → no results
- [ ] `.env` absent from `git ls-files`
- [ ] `pip-audit` and `npm audit` → no high or critical findings
- [ ] Response headers verified in DevTools on the deployed site
- [ ] Refresh cookie confirmed `HttpOnly`, `Secure`, `SameSite=None` in production
- [ ] `/docs` returns 404 in production
- [ ] No real personal data in any screenshot, fixture, or seed file
