# ResumeIQ — Matching and Scoring Methodology

> Phase 1 deliverable; implemented in Phase 8. **This document is the single source of truth
> for the score.** It is written to be published — the landing page, the results page, and
> the README all draw from it. If the code and this document disagree, one of them is a bug.

---

## 1. Principles

1. **Every point is traceable.** For any score you can answer: which category, what weight,
   what evidence, what was missing.
2. **Deterministic.** Same resume text + same job description = same score. No randomness,
   no clock, no AI in the scoring path.
3. **Honest about its limits.** Every category publishes a limitation. The overall score
   carries a disclaimer everywhere it appears.
4. **Never punitive about facts it cannot verify.** Where the analyser cannot know something
   (whether a stated year of experience is real), it measures presence of evidence, not truth.

**The disclaimer, used verbatim throughout the product:**

> This score is an internal estimate produced by ResumeIQ's published rubric. It is not a
> simulation of any specific employer's applicant tracking system, and a high or low score
> does not predict whether you will be shortlisted.

---

## 2. Weights

| Key | Category | Weight |
|---|---|---:|
| `required_skills` | Required skill coverage | **30** |
| `experience_relevance` | Relevant experience indicators | **15** |
| `preferred_skills` | Preferred skill coverage | **10** |
| `education_alignment` | Education alignment | **10** |
| `keyword_coverage` | Job-description keyword coverage | **10** |
| `resume_completeness` | Resume section completeness | **10** |
| `measurable_achievements` | Measurable achievements | **10** |
| `statement_quality` | Statement quality | **5** |
| | **Total** | **100** |

**Why these weights.** Required skills dominate because that is the first filter a human or
automated screen applies. Experience is next because relevance beats breadth. Preferred
skills are worth a third of required — helpful, not decisive. The remaining categories
measure how well the resume *communicates* what is there; they matter, but a beautifully
written resume for the wrong role is still the wrong resume.

The weights are constants in `analyzers/scorer.py`, defined once, and the module asserts they
sum to 100 at import time. Changing a weight is a one-line change plus a test update — and
the test that asserts the sum makes an inconsistent rubric impossible to ship.

---

## 3. Category specifications

### 3.1 `required_skills` — 30 points

```
matched_units  = count(status == matched)  × 1.0
partial_units  = count(status == partial)  × 0.5
points = 30 × (matched_units + partial_units) / count(required_skills)
```

- **Exact** — canonical taxonomy term appears in the resume.
- **Alias** — a registered synonym appears (`postgres` → `postgresql`, `js` → `javascript`).
  Scored as **matched**, because it is the same skill.
- **Related** — a taxonomy-declared neighbour appears (`react` for a required `frontend
  frameworks`). Scored as **partial** at 0.5, because it is evidence, not proof.
- **Missing** — none of the above.

Matching is case-insensitive on word boundaries. Word boundaries are essential: without them
`R` matches every capital R in the document and `Go` matches "Google".

*Edge case:* if the JD yields zero required skills, this category reports
`points_possible: 0` with the explanation that no requirements could be extracted, and the
remaining categories are rescaled to 100. Never a divide-by-zero, never a silent zero.

**Limitation published to the user:** *Skills are matched against a curated list of roughly
300 terms with known aliases. A skill written in unusual wording, or one not in the list, may
not be recognised, which understates your score.*

### 3.2 `experience_relevance` — 15 points

Two independent halves.

**(a) Duration signal — 8 points.** Total months are estimated from date ranges in the
experience section (`Jan 2023 – Present`, `2021-2023`, `03/2022 – 06/2024`). Compared to the
JD's `min_years_experience`:

| Detected vs required | Points |
|---|---:|
| ≥ required | 8 |
| ≥ 60 % of required | 5 |
| > 0 but < 60 % | 3 |
| No dates detected | 4 *(neutral, not zero)* |
| JD states no requirement | 8 |

"No dates detected" scores neutral by design. A resume without parseable dates has a
formatting problem, not necessarily an experience problem, and the recommendation says so.

**(b) Contextual relevance — 7 points.** The proportion of required skills that appear
*within the experience section* rather than only in a skills list. A skill demonstrated in a
job bullet is stronger evidence than a skill named in a comma-separated list.

```
points_b = 7 × (required skills found in experience section) / (required skills found anywhere)
```

**Limitation:** *Employment dates are parsed from common formats. Unusual date formats, or
career gaps, may be measured inaccurately. This measures what your resume states; it does not
verify it.*

### 3.3 `preferred_skills` — 10 points

Identical formula to §3.1, applied to the preferred set. If the JD has no preferred section,
`points_possible` is 0 and the other categories are rescaled — a job with no preferences must
not cost the candidate 10 points.

**Limitation:** *"Preferred" is inferred from headings such as "nice to have" or "bonus". If
the job description does not use those cues, all requirements are treated as required, which
is disclosed on your result.*

### 3.4 `education_alignment` — 10 points

Both sides map to an ordinal: `none(0) < certificate(1) < diploma(2) < bachelor(3) <
master(4) < doctorate(5)`.

| Condition | Points |
|---|---:|
| Resume level ≥ required level | 10 |
| Exactly one level below | 6 |
| Two or more levels below | 3 |
| No education section detected | 2 |
| JD states no requirement | 10 |

Exceeding the requirement earns full marks, never bonus points — over-qualification is not
a scoring event.

**Limitation:** *Education is matched on qualification level only. Field of study, awarding
institution, and equivalency are not assessed.*

### 3.5 `keyword_coverage` — 10 points

Distinct from skills: this measures the JD's meaningful non-skill vocabulary — domain nouns,
methodologies, tools ("agile", "stakeholder", "microservices", "accessibility").

Method: tokenise the JD, remove stopwords and hiring boilerplate, remove terms already
counted as skills, keep the top 25 by frequency, and measure how many appear in the resume.

```
points = 10 × min(1.0, coverage_ratio / 0.60)
```

**Full marks at 60 % coverage, not 100 %.** Requiring every keyword would reward stuffing the
resume with JD vocabulary — precisely the behaviour this tool should not encourage. The
threshold is a deliberate anti-gaming choice and the results page explains it.

**Limitation:** *Keyword coverage measures vocabulary overlap only. It cannot assess whether
you used a term meaningfully, and copying words from the job description to raise this number
will not make your resume stronger to a human reader.*

### 3.6 `resume_completeness` — 10 points

Weighted by how much each section matters to a reader:

| Section | Points |
|---|---:|
| Contact | 2.0 |
| Experience | 2.0 |
| Skills | 2.0 |
| Education | 1.5 |
| Summary | 1.0 |
| Projects | 1.0 |
| Certifications | 0.25 |
| Achievements | 0.25 |
| Languages | 0.0 *(reported, not scored)* |

Languages is detected and displayed but scores zero: it matters greatly for some roles and
not at all for others, and the scorer has no way to tell which. Reporting without scoring is
more honest than guessing.

**Limitation:** *Sections are detected from common headings and content patterns. An
unconventional layout may cause a section you do have to be reported as missing.*

### 3.7 `measurable_achievements` — 10 points

Counts bullets containing a quantified outcome — percentages, currency, counts with units,
time reductions, scale figures ("40%", "$12k", "3 000 users", "reduced from 8s to 2s").

| Bullets with a measurable result | Points |
|---|---:|
| 0 | 0 |
| 1–2 | 4 |
| 3–4 | 7 |
| 5+ | 10 |

Bands rather than a ratio: a 6-bullet resume with 4 metrics should not outscore a 20-bullet
resume with 8. What is being measured is the habit of quantifying, not a density figure.

**Limitation:** *Numbers are detected by pattern. A quantified outcome written in words
("halved the processing time") may be missed, and a number that is not an achievement (a
year, a version number) may occasionally be counted.*

### 3.8 `statement_quality` — 5 points

Starts at 5.0; deductions are applied per distinct issue, floored at 0.

| Issue | Deduction |
|---|---:|
| Action-verb rate < 50 % of bullets | −1.5 |
| ≥ 3 bullets using generic phrasing ("responsible for", "worked on", "helped with", "duties included") | −1.5 |
| ≥ 2 passive constructions | −1.0 |
| ≥ 2 bullets longer than 35 words | −1.0 |
| Any phrase repeated ≥ 3 times | −1.0 |

**Limitation:** *Writing quality is assessed by pattern rules, not comprehension. Strong,
unconventional writing may be flagged, and weak writing that follows the patterns may pass.*

---

## 4. Worked example

Job: Junior Backend Developer. Required: `python, postgresql, docker, rest apis, git, linux,
testing, sql, ci/cd` (9). Preferred: `kubernetes, redis` (2). 2+ years, bachelor's degree.

| Category | Calculation | Earned |
|---|---|---:|
| Required skills | 6 exact + 1 partial → `(6 + 0.5)/9 × 30` | 21.7 |
| Experience | 18 months vs 24 required → 5; 5 of 7 found in experience → `7 × 5/7 = 5.0` | 10.0 |
| Preferred skills | 1 of 2 → `10 × 0.5` | 5.0 |
| Education | Bachelor's = required | 10.0 |
| Keyword coverage | 11 of 25 = 44 % → `10 × (0.44/0.60)` | 7.3 |
| Completeness | All but summary and certifications | 8.75 |
| Achievements | 2 quantified bullets → band 1–2 | 4.0 |
| Statement quality | 5.0 − 1.5 (verbs) − 1.5 (generic) | 2.0 |
| **Overall** | | **68.75 → 69** |

Rounding: categories keep two decimals in the database; the overall score is rounded
half-up to an integer once, at the end.

Score bands used in the UI (colour and language only — they change nothing in the maths):
0–39 weak alignment · 40–59 partial · 60–74 moderate · 75–89 strong · 90–100 very strong.

---

## 5. What the score deliberately does not do

- It does not predict an interview or a hiring outcome.
- It does not replicate any named ATS product. No public specification of those systems
  exists, so claiming to match one would be a fabrication.
- It does not judge career quality, seniority, or the prestige of an employer.
- It does not reward keyword stuffing — §3.5's 60 % cap exists specifically to prevent it.
- It does not penalise a candidate for facts the analyser cannot parse; unparseable cases
  score neutral and generate a formatting recommendation instead.

---

## 6. Implementation contract

```python
def compute_score(resume: ResumeProfile, job: JobProfile) -> ScoreBreakdown: ...
```

Rules the implementation must satisfy, each with a corresponding test:

1. Pure function — no I/O, no database, no network, no `datetime.now()`, no randomness.
2. `sum(category.points_possible for category in result.categories) == 100` after rescaling.
3. `0 <= points_earned <= points_possible` for every category.
4. `overall_score == round(sum(points_earned))`.
5. Every category populates `explanation`, `evidence`, and `limitation` — never an empty
   string.
6. Calling it twice with identical inputs returns identical output.
7. Empty required-skills, empty preferred-skills, and no-experience-section inputs are all
   handled without exceptions.

Weight constants live in one dictionary with a module-level assertion that they sum to 100.
