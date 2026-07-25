# ResumeIQ — User Stories and Acceptance Criteria

> Phase 1 deliverable. Each story maps to functional requirements in `01-requirements.md`
> and becomes a GitHub issue. Acceptance criteria are written so they can be turned directly
> into test names.

Format: **US-x** — *As a [role], I want [capability], so that [outcome].*

---

## Epic A — Authentication

### US-1 — Registration
*As a job seeker, I want to create an account, so that my analyses are saved privately to me.*
Covers FR-A1, FR-A2, FR-A3.

**Acceptance criteria**
- [ ] Given valid name, email, and a password of ≥ 10 chars containing a letter and a digit, when I submit, then an account is created and I am returned a 201 with my profile (no password field present).
- [ ] Given an email already registered, when I submit, then I receive 409 with a message that does not confirm or deny anything beyond "this email cannot be registered".
- [ ] Given a password of 9 characters, when I submit, then I receive 422 and the field-level message names the length rule.
- [ ] Given `Test@Example.COM`, when I register and then log in with `test@example.com`, then login succeeds (email is normalised).
- [ ] The stored `password_hash` starts with a bcrypt identifier and never equals the plaintext.
- [ ] Client-side Zod validation blocks submission early, but disabling JavaScript and posting directly still triggers identical server-side rejection.

### US-2 — Login and session
*As a registered user, I want to log in, so that I can reach my dashboard.*
Covers FR-A4, FR-A5.

**Acceptance criteria**
- [ ] Correct credentials return an access token and set a refresh cookie; the user lands on `/dashboard`.
- [ ] Incorrect password and unknown email produce the **same** 401 body and a comparable response time.
- [ ] `GET /auth/me` with the access token returns the profile; without it returns 401.
- [ ] An expired access token returns 401 with code `TOKEN_EXPIRED`; the client silently refreshes once and retries, and only redirects to `/login` if the refresh also fails.
- [ ] A token signed with the wrong secret returns 401 and is logged as a security event without the token value.

### US-3 — Protected routes
*As a user, I want unauthenticated visitors kept out of my pages, so that my data is not exposed.*
Covers FR-A5.

**Acceptance criteria**
- [ ] Visiting `/dashboard` unauthenticated redirects to `/login?next=/dashboard`; after login I land back on `/dashboard`.
- [ ] Every `/api/v1/analyses*` route returns 401 without a valid token.
- [ ] The redirect happens after auth state resolves, so a logged-in user refreshing the page never sees a login flash.

### US-4 — Logout and account deletion
*As a user, I want to log out and to delete my account entirely, so that I control my data.*
Covers FR-A6, FR-A8.

**Acceptance criteria**
- [ ] Logout revokes the refresh token server-side; replaying the old refresh cookie returns 401.
- [ ] Account deletion requires re-entering the password and typing a confirmation phrase.
- [ ] After deletion, the user row and every one of their analyses and child rows are gone (verified by direct DB query in the test).

### US-5 — Brute-force resistance
*As the system owner, I want repeated failed logins throttled, so that passwords cannot be guessed at scale.*
Covers FR-A7.

**Acceptance criteria**
- [ ] After 5 failed attempts for one email within 15 minutes, further attempts return 429 with a `Retry-After` header.
- [ ] The throttle keys on both email and client IP.
- [ ] A successful login clears the counter.
- [ ] The 429 message tells the user what happened, why, and when to retry.

---

## Epic B — Upload and extraction

### US-6 — Upload a PDF resume
*As a user, I want to upload my resume as a PDF, so that it can be analysed.*
Covers FR-B1, FR-B2, FR-B3, FR-B6.

**Acceptance criteria**
- [ ] Drag-and-drop and click-to-browse both work; the chosen filename and size are displayed.
- [ ] A `.docx` selection is rejected client-side with a clear message and also rejected server-side if posted directly.
- [ ] A file renamed from `.exe` to `.pdf` is rejected server-side by the magic-byte check.
- [ ] A 6 MB file is rejected with 413 before the whole body is buffered.
- [ ] A filename such as `../../etc/passwd.pdf` is sanitised; no path traversal is possible and the raw name is never echoed unescaped into the DOM.
- [ ] After the request completes — successfully or not — no temporary file remains on disk (asserted in a test using a temp-dir fixture).

### US-7 — Handle unreadable resumes gracefully
*As a user who uploaded a scanned resume, I want to be told exactly what is wrong, so that I can fix it.*
Covers FR-B4, FR-B5, FR-B8.

**Acceptance criteria**
- [ ] A scanned/image-only PDF returns `RESUME_NO_TEXT_LAYER` with: what happened, the likely cause (scan or image export), and the fix (export from Word/Google Docs as PDF, or use a text-based version).
- [ ] A truncated/corrupt PDF returns `RESUME_CORRUPT` rather than a 500.
- [ ] A password-protected PDF returns `RESUME_ENCRYPTED`.
- [ ] A 0-byte file returns `RESUME_EMPTY`.
- [ ] No error message contains a server path, a library stack trace, or a Python exception class name.

### US-8 — Clean text extraction
*As the analyser, I want normalised text, so that section and skill detection behave predictably.*
Covers FR-B7.

**Acceptance criteria**
- [ ] Multi-column layouts extract in a readable order; runs of whitespace collapse to a single space.
- [ ] `•`, `▪`, `-`, `*` bullet glyphs normalise to one marker.
- [ ] Words hyphenated across a line break rejoin (`develop-\nment` → `development`).
- [ ] Blank-line paragraph boundaries survive normalisation (they are needed for section detection).

---

## Epic C — Analysis

### US-9 — Section completeness
*As a user, I want to see which standard resume sections I have and which are missing, so that I can fill gaps.*
Covers FR-C1, FR-C2, FR-C3.

**Acceptance criteria**
- [ ] All nine sections are reported with detected true/false.
- [ ] Detection tolerates case and common synonyms ("Work History" / "Professional Experience" / "Employment").
- [ ] Contact is detected from an email or phone pattern even with no heading.
- [ ] Each detected section shows the heading text that triggered it, so the user can see the reasoning.
- [ ] Missing sections are ordered by impact, with an explanation of why each matters.

### US-10 — Statement quality
*As a user, I want weak bullets identified with concrete suggestions, so that I can rewrite them.*
Covers FR-C5, FR-C6.

**Acceptance criteria**
- [ ] "Responsible for maintaining the company website" is flagged for generic phrasing, missing action verb, and missing measurable result.
- [ ] "Reduced page load time by 40% by adding image lazy-loading" is **not** flagged and is counted as a measurable achievement.
- [ ] A bullet over 35 words is flagged for length with its word count shown.
- [ ] A phrase repeated 3+ times across the resume is flagged once, listing the occurrences.
- [ ] Passive constructions ("was managed by", "were handled") are flagged.
- [ ] **No suggestion invents a number, a client, a technology, or an outcome not present in the original bullet.** Suggestions are structural ("start with an action verb; add the measurable result if you know it"), not fabricated.

### US-11 — Job description parsing
*As a user, I want the job description broken into requirements, so that the comparison is meaningful.*
Covers FR-D1 → FR-D6.

**Acceptance criteria**
- [ ] Pasting a JD under 200 chars is rejected with a clear minimum-length message.
- [ ] Skills are extracted and normalised: `React.js`, `ReactJS`, and `React` all resolve to one canonical skill.
- [ ] Skills under a "Requirements" heading are marked required; skills under "Nice to have" are marked preferred.
- [ ] When no required/preferred cue exists, all skills are treated as required and the UI displays that this assumption was made.
- [ ] "3+ years of experience" yields `min_years_experience: 3`.
- [ ] "Bachelor's degree in Computer Science or equivalent" yields education level `bachelor`.
- [ ] Boilerplate such as "equal opportunity employer" does not appear in extracted keywords.

### US-12 — Transparent score
*As a user, I want to understand exactly how my score was produced, so that I can trust and act on it.*
Covers FR-E1 → FR-E5.

**Acceptance criteria**
- [ ] The overall score is 0–100 and equals the sum of the eight category point values (assert the arithmetic in a test).
- [ ] Every category card shows: name, weight, earned/possible, explanation, evidence, recommendation, limitation.
- [ ] Matched, partially matched, and missing skills are listed separately, and each matched skill shows where it was found.
- [ ] The disclaimer — that this is an internal estimate and not any specific employer's ATS — is visible on the results page and included in the exported report.
- [ ] Re-running the identical resume text and JD produces a byte-identical deterministic result.
- [ ] A JD with zero extractable skills does not crash; the category reports zero possible points and explains why.

---

## Epic D — AI assistance

### US-13 — AI recommendations
*As a user, I want personalised suggestions, so that I know what to change first.*
Covers FR-F1, FR-F2, FR-F5.

**Acceptance criteria**
- [ ] Suggestions are prioritised high/medium/low with a stated reason for each.
- [ ] Rewritten statements preserve the original facts; a test with a fact-free bullet asserts the rewrite introduces no company, metric, or technology.
- [ ] Missing-skill guidance suggests how to learn or evidence a skill; it never suggests claiming an unheld skill.
- [ ] Interview preparation points reference only content present in the resume and JD.
- [ ] AI output failing schema validation is discarded and treated as an AI failure.

### US-14 — Works without AI
*As a user, I want the analysis to work even when the AI service is down, so that the product is dependable.*
Covers FR-F3, FR-F4, NFR-9.

**Acceptance criteria**
- [ ] With `AI_API_KEY` unset, an analysis completes and returns HTTP 200 with the full deterministic result.
- [ ] The response carries `ai_status: "unavailable"` with a reason code (`not_configured`, `timeout`, `rate_limited`, `provider_error`, `invalid_output`).
- [ ] The UI shows a calm, non-alarming notice plus deterministic rule-based suggestions — not an error state.
- [ ] A provider timeout does not extend the request beyond the configured ceiling.
- [ ] Exceeding the per-user daily AI quota degrades to the same fallback rather than failing the request.

---

## Epic E — History and ownership

### US-15 — Save and browse history
*As a returning user, I want my past analyses listed, so that I can track progress.*
Covers FR-G1, FR-G5.

**Acceptance criteria**
- [ ] Each row shows title, job title, score, and creation date (relative + absolute on hover).
- [ ] The list is paginated (10 per page) and newest-first.
- [ ] A new user sees an empty state with a call to action, not a blank table.
- [ ] Opening a row reproduces the stored analysis exactly as first shown.

### US-16 — Rename and delete
*As a user, I want to organise and remove my analyses, so that I control my records.*
Covers FR-G4.

**Acceptance criteria**
- [ ] Inline rename validates length (1–120 chars) and persists.
- [ ] Delete requires confirmation in an accessible modal (focus trapped, Escape closes, focus returns to the trigger).
- [ ] Deletion removes all child rows; a follow-up fetch of that ID returns 404.

### US-17 — Ownership enforcement
*As a user, I want it to be impossible for anyone else to read my analysis, so that my resume data stays private.*
Covers FR-G3. **This is the single most important security test in the project.**

**Acceptance criteria**
- [ ] User A requesting user B's analysis ID receives **404**, not 403 and not the data.
- [ ] The same applies to update and delete.
- [ ] The list endpoint returns only the caller's rows, enforced in the repository query and not merely by a route check.
- [ ] A test creates two users, an analysis for each, and asserts cross-access fails for GET, PATCH, and DELETE.

---

## Epic F — Interface

### US-18 — Dashboard
*As a returning user, I want an at-a-glance view, so that I know where I stand.*
Covers FR-H3, FR-H2.

**Acceptance criteria**
- [ ] Cards show total analyses, average score, best score, and analyses this month.
- [ ] A line chart shows score over time; with fewer than 2 analyses it shows an explanatory empty state rather than a broken axis.
- [ ] The most frequent missing skills are listed with occurrence counts.
- [ ] Skeleton loaders render while data is loading; a failed fetch shows a retry affordance.
- [ ] Sidebar navigation on ≥ 1024 px; a slide-over drawer below that, closable by Escape and by backdrop click.

### US-19 — Results page
*As a user, I want a complete, readable report, so that I can act on it.*
Covers FR-H1, FR-H4.

**Acceptance criteria**
- [ ] Overall score, per-category breakdown, matched/partial/missing skills, section analysis, achievement analysis, weak statements, AI recommendations, and a prioritised action list are all present.
- [ ] Long lists collapse behind "show all" so the page is scannable.
- [ ] Print view hides the sidebar, header, and interactive controls, and keeps the disclaimer.
- [ ] The page is fully navigable by keyboard, with a visible focus ring on every control.

### US-20 — Landing and privacy pages
*As a visitor evaluating the tool, I want to understand what it does and what happens to my data before I sign up.*
Covers FR-H1.

**Acceptance criteria**
- [ ] The landing page states the value proposition in specific terms and contains no unsupported claims ("guaranteed", "100% accurate", "beats any ATS").
- [ ] It includes a worked example of the scoring rubric.
- [ ] The privacy page states plainly: the PDF is never stored, resume text is not stored by default, what *is* stored, how to delete it, and what the AI provider receives.
- [ ] A "Limitations" section is reachable from the landing page and lists the known weaknesses honestly.
