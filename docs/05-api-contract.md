# ResumeIQ — API Contract

> Phase 1 deliverable. This is the contract the frontend types in `frontend/src/types/`
> mirror. FastAPI generates live OpenAPI docs at `/docs`; this document is the design
> intent and the reference for error codes.

Base path: `/api/v1`
Auth: `Authorization: Bearer <access_token>` unless marked **public**.

---

## 1. Endpoint overview

| Method | Path | Auth | Purpose | Phase |
|---|---|---|---|---|
| `GET` | `/health` | public | Liveness + database reachability | 2 |
| `POST` | `/auth/register` | public | Create an account | 4 |
| `POST` | `/auth/login` | public | Exchange credentials for tokens | 4 |
| `POST` | `/auth/refresh` | cookie | New access token from the refresh cookie | 4 |
| `POST` | `/auth/logout` | Bearer | Revoke the refresh token | 4 |
| `GET` | `/auth/me` | Bearer | Current user profile | 4 |
| `PATCH` | `/users/me` | Bearer | Update full name | 12 |
| `POST` | `/users/me/password` | Bearer | Change password | 12 |
| `DELETE` | `/users/me` | Bearer | Delete account and all data | 12 |
| `POST` | `/analyses` | Bearer | Upload resume + JD, run analysis, persist | 5→9 |
| `GET` | `/analyses` | Bearer | Paginated history for the caller | 9 |
| `GET` | `/analyses/{id}` | Bearer | Full stored analysis | 9 |
| `PATCH` | `/analyses/{id}` | Bearer | Rename | 9 |
| `DELETE` | `/analyses/{id}` | Bearer | Delete analysis and children | 9 |
| `GET` | `/analyses/stats/summary` | Bearer | Dashboard aggregates | 10 |
| `POST` | `/analyses/{id}/recommendations` | Bearer | Re-request AI enrichment | 11 |

Seventeen endpoints. Nothing speculative — every route maps to a functional requirement.

---

## 2. Conventions

**Success envelopes.** Single resources return the object directly. Collections return:

```json
{ "items": [...], "total": 42, "page": 1, "page_size": 10, "has_next": true }
```

**Error envelope.** Every non-2xx returns exactly this shape (see `03-architecture.md` §7):

```json
{
  "error": {
    "code": "RESUME_NO_TEXT_LAYER",
    "what": "We could not read any text from this PDF.",
    "why": "The file appears to be a scan or an exported image rather than a text document.",
    "next_step": "Export a text-based PDF from Word or Google Docs, then upload it again.",
    "request_id": "b3f1c2d4e5"
  }
}
```

Validation failures (422) additionally carry `"fields": {"password": "..."}` so forms can
show messages inline.

**Status codes.** `200` read/update · `201` create · `204` delete · `400` malformed ·
`401` unauthenticated · `404` not found *or not owned* · `409` conflict · `413` too large ·
`415` unsupported media type · `422` validation · `429` rate limited · `500` internal.

**404 over 403 for ownership.** Requesting another user's analysis returns 404. A 403 would
confirm the ID exists (FR-G3).

---

## 3. Authentication

### `POST /auth/register` — public

```jsonc
// request
{ "full_name": "Ada Lovelace", "email": "ada@example.com", "password": "analytical2026" }

// 201
{ "id": "uuid", "full_name": "Ada Lovelace", "email": "ada@example.com",
  "created_at": "2026-07-25T10:00:00Z" }
```

Errors: `409 EMAIL_UNAVAILABLE` · `422 VALIDATION_ERROR`.
The response never contains `password_hash` — the Pydantic response model has no such field,
so it cannot leak by accident.

### `POST /auth/login` — public

```jsonc
// request
{ "email": "ada@example.com", "password": "analytical2026" }

// 200 — plus Set-Cookie: refresh_token=...; HttpOnly; Secure; SameSite=None; Path=/api/v1/auth
{ "access_token": "eyJ...", "token_type": "bearer", "expires_in": 1800,
  "user": { "id": "uuid", "full_name": "Ada Lovelace", "email": "ada@example.com" } }
```

Errors: `401 INVALID_CREDENTIALS` (identical for wrong password and unknown email) ·
`429 TOO_MANY_ATTEMPTS` with `Retry-After`.

### `POST /auth/refresh` — refresh cookie only
`200` → new access token. `401 REFRESH_INVALID` if missing, expired, revoked, or unknown.

### `POST /auth/logout` — Bearer
`204`. Sets `revoked_at` on the stored token hash and clears the cookie. Idempotent.

### `GET /auth/me` — Bearer
`200` → user profile. `401 TOKEN_MISSING` | `TOKEN_EXPIRED` | `TOKEN_INVALID`.
The distinct codes let the client refresh on `TOKEN_EXPIRED` and log out on `TOKEN_INVALID`.

---

## 4. Analyses

### `POST /analyses` — Bearer — the core endpoint

`multipart/form-data`:

| Field | Type | Required | Rules |
|---|---|---|---|
| `resume` | file | yes | `.pdf`, ≤ 5 MB, `%PDF-` magic bytes |
| `job_description` | text | yes | 200–8,000 chars |
| `job_title` | text | no | ≤ 160 chars |
| `company_name` | text | no | ≤ 160 chars |
| `title` | text | no | ≤ 120 chars; defaults to job title or date |
| `store_resume_text` | bool | no | default `false` (FR-G2) |

**`201` response** — the full result, returned in one round trip so the results page needs no
follow-up fetch:

```jsonc
{
  "id": "uuid",
  "title": "Junior Backend Developer — Acme",
  "resume_filename": "ada_lovelace_cv.pdf",
  "created_at": "2026-07-25T10:04:11Z",

  "overall_score": 68,
  "disclaimer": "This score is an internal estimate produced by ResumeIQ's published rubric. It is not a simulation of any specific employer's applicant tracking system.",

  "score_breakdown": [
    {
      "category_key": "required_skills",
      "category_name": "Required skill coverage",
      "weight": 30,
      "points_earned": 19.5,
      "points_possible": 30,
      "explanation": "Your resume matched 6 of 9 required skills, and partially matched 1.",
      "evidence": [
        { "skill": "python",     "status": "matched", "matched_via": "exact",
          "snippet": "Built data pipelines in Python" },
        { "skill": "postgresql", "status": "partial", "matched_via": "alias",
          "snippet": "Managed Postgres databases" },
        { "skill": "docker",     "status": "missing", "matched_via": null, "snippet": null }
      ],
      "recommendation": "Add Docker to your skills section if you have used it, and reference it in a project bullet.",
      "limitation": "Skills are matched against a curated list of ~300 terms. A skill described in unusual wording may not be recognised."
    }
    // ... 7 more categories
  ],

  "skills": {
    "matched":  [{ "skill": "python", "requirement_level": "required", "matched_via": "exact", "snippet": "..." }],
    "partial":  [{ "skill": "postgresql", "requirement_level": "required", "matched_via": "alias", "snippet": "..." }],
    "missing":  [{ "skill": "docker", "requirement_level": "required" }]
  },

  "sections": [
    { "section_key": "contact",    "detected": true,  "matched_heading": null,
      "note": "Found an email address and a phone number." },
    { "section_key": "summary",    "detected": false, "matched_heading": null,
      "note": "No professional summary detected. A 2–3 line summary helps a reader place you quickly." }
  ],

  "statements": {
    "total_bullets": 18,
    "with_measurable_result": 4,
    "action_verb_rate": 0.61,
    "findings": [
      { "statement_text": "Responsible for maintaining the company website",
        "issue_codes": ["GENERIC_PHRASING", "NO_ACTION_VERB", "NO_METRIC"],
        "word_count": 7, "has_measurable_result": false,
        "suggestion": "Open with an action verb and state the outcome you achieved. Only add figures you can substantiate." }
    ]
  },

  "job_analysis": {
    "job_title": "Junior Backend Developer",
    "company_name": "Acme",
    "min_years_experience": 2,
    "required_education_level": "bachelor",
    "requirement_split_inferred": false,
    "required_skills": ["python", "postgresql", "docker"],
    "preferred_skills": ["kubernetes"]
  },

  "recommendations": [
    { "priority": "high", "source": "rule", "category": "skills",
      "title": "Three required skills are missing",
      "detail": "Docker, Redis, and CI/CD do not appear anywhere in your resume." }
  ],

  "ai_status": "unavailable",
  "ai_reason_code": "not_configured",
  "ai_message": "AI suggestions are not available right now. The analysis below is complete and was produced by ResumeIQ's rule-based engine."
}
```

Errors, all with the three-part message body:

| Code | Status | Trigger |
|---|---|---|
| `RESUME_MISSING` | 422 | No file part |
| `RESUME_INVALID_TYPE` | 415 | Extension, MIME, or magic bytes disagree |
| `RESUME_TOO_LARGE` | 413 | > 5 MB |
| `RESUME_EMPTY` | 422 | 0 bytes |
| `RESUME_CORRUPT` | 422 | PyMuPDF cannot open it |
| `RESUME_ENCRYPTED` | 422 | Password-protected |
| `RESUME_NO_TEXT_LAYER` | 422 | < 200 meaningful characters extracted |
| `JOB_DESCRIPTION_TOO_SHORT` | 422 | < 200 chars |
| `JOB_DESCRIPTION_TOO_LONG` | 422 | > 8,000 chars |
| `RATE_LIMITED` | 429 | Analysis quota exceeded |
| `INTERNAL_ERROR` | 500 | Anything unhandled — request ID only |

> **Note that the AI provider has no error code here.** An AI failure is not a request
> failure; it surfaces as `ai_status` inside a `201`. That is FR-F3 expressed in the contract.

### `GET /analyses?page=1&page_size=10` — Bearer

```jsonc
{ "items": [ { "id": "uuid", "title": "Junior Backend Developer — Acme",
               "job_title": "Junior Backend Developer", "overall_score": 68,
               "created_at": "2026-07-25T10:04:11Z" } ],
  "total": 12, "page": 1, "page_size": 10, "has_next": true }
```

Summary rows only — the list must not ship every user's full analysis payload.

### `GET /analyses/{id}` — Bearer
`200` → the same object shape as the `POST` response. `404 ANALYSIS_NOT_FOUND` when the ID
does not exist **or is not owned by the caller**.

### `PATCH /analyses/{id}` — Bearer
`{"title": "..."}` → `200` with the updated summary. `404` on non-ownership.

### `DELETE /analyses/{id}` — Bearer
`204`. Cascades to all child rows. `404` on non-ownership. Idempotent from the client's view.

### `GET /analyses/stats/summary` — Bearer

```jsonc
{
  "total_analyses": 12,
  "average_score": 64.3,
  "best_score": 81,
  "analyses_this_month": 5,
  "score_trend": [ { "date": "2026-07-01", "score": 55 }, { "date": "2026-07-14", "score": 68 } ],
  "common_missing_skills": [ { "skill": "docker", "occurrences": 7 } ]
}
```

With zero analyses: zeroed counters, `null` averages, empty arrays — never a 404. The empty
state is the frontend's job, not an error.

### `POST /analyses/{id}/recommendations` — Bearer
Re-runs AI enrichment for a stored analysis (used when AI was unavailable at creation, or
after the user edits and re-uploads). Returns the updated recommendations plus `ai_status`.
`429 AI_QUOTA_EXCEEDED` when the daily per-user quota is spent — and even then the stored
deterministic recommendations remain available.

---

## 5. Users

| Endpoint | Body | Notes |
|---|---|---|
| `PATCH /users/me` | `{ "full_name": "..." }` | Email changes are out of scope for v1 |
| `POST /users/me/password` | `{ "current_password": "...", "new_password": "..." }` | Verifies the current password; revokes all refresh tokens on success |
| `DELETE /users/me` | `{ "password": "...", "confirmation": "DELETE" }` | Cascade-deletes everything. `204` |

---

## 6. Health

`GET /health` → `{"status": "ok", "database": "ok", "version": "1.0.0"}`, or `503` with
`"database": "unreachable"`. No authentication, and no build paths, dependency versions, or
environment details in the payload.

---

## 7. Cross-cutting rules

**Rate limits**

| Scope | Limit | Response |
|---|---|---|
| `POST /auth/login` | 5 failures / 15 min per email **and** per IP | `429 TOO_MANY_ATTEMPTS` + `Retry-After` |
| `POST /auth/register` | 10 / hour per IP | `429 RATE_LIMITED` |
| `POST /analyses` | 20 / day per user | `429 RATE_LIMITED` |
| AI enrichment | 20 / day per user | Degrades to fallback; never fails the request |

**CORS.** `allow_origins` is an explicit list (production frontend origin +
`http://localhost:5173`), `allow_credentials=True`, methods and headers enumerated. Never
`*` alongside credentials (NFR-6).

**Security headers.** `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`,
`Referrer-Policy: no-referrer`, HSTS in production.

**Request IDs.** Middleware assigns one per request, returns it as `X-Request-ID`, and
includes it in every log line and error body — traceability without exposing internals.

**Versioning.** Everything under `/api/v1`. A breaking change becomes `/api/v2`; the
frontend's `VITE_API_BASE_URL` carries the version segment.
