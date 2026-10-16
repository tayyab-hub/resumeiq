"""The transparent weighted scoring model.

This module is the executable form of `docs/06-scoring-methodology.md`. If the
two disagree, one of them is a bug. Every category publishes its weight, its
evidence, and its limitation, because a score whose derivation is hidden cannot
be acted on.

`compute_score` is a pure function: no I/O, no database, no clock, no
randomness. The same inputs always produce the same output.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from app.analyzers.domain import (
    JobProfile,
    ResumeProfile,
    ScoreBreakdown,
    ScoredCategory,
    SkillComparison,
)
from app.analyzers.experience_parser import education_ordinal
from app.analyzers.statement_analyzer import (
    ISSUE_GENERIC_PHRASING,
    ISSUE_PASSIVE_VOICE,
    ISSUE_TOO_LONG,
)
from app.analyzers.vocabulary import skills_by_name

# --- Weights ---------------------------------------------------------------
# Defined once. The assertion below makes an inconsistent rubric impossible to
# ship: changing a weight without rebalancing fails at import time.

WEIGHTS: dict[str, float] = {
    "required_skills": 30.0,
    "experience_relevance": 15.0,
    "preferred_skills": 10.0,
    "education_alignment": 10.0,
    "keyword_coverage": 10.0,
    "resume_completeness": 10.0,
    "measurable_achievements": 10.0,
    "statement_quality": 5.0,
}
assert sum(WEIGHTS.values()) == 100.0, "Scoring weights must sum to exactly 100"

CATEGORY_NAMES: dict[str, str] = {
    "required_skills": "Required skill coverage",
    "experience_relevance": "Relevant experience indicators",
    "preferred_skills": "Preferred skill coverage",
    "education_alignment": "Education alignment",
    "keyword_coverage": "Job-description keyword coverage",
    "resume_completeness": "Resume section completeness",
    "measurable_achievements": "Measurable achievements",
    "statement_quality": "Statement quality",
}

LIMITATIONS: dict[str, str] = {
    "required_skills": (
        "Skills are matched against a curated list of roughly 300 terms with known aliases. "
        "A skill written in unusual wording, or one not in the list, may not be recognised, "
        "which understates your score."
    ),
    "experience_relevance": (
        "Employment dates are parsed from common formats. Unusual date formats, or career "
        "gaps, may be measured inaccurately. This measures what your resume states; it does "
        "not verify it."
    ),
    "preferred_skills": (
        '"Preferred" is inferred from headings such as "nice to have" or "bonus". If the job '
        "description does not use those cues, all requirements are treated as required, which "
        "is disclosed on your result."
    ),
    "education_alignment": (
        "Education is matched on qualification level only. Field of study, awarding "
        "institution, and equivalency are not assessed."
    ),
    "keyword_coverage": (
        "Keyword coverage measures vocabulary overlap only. It cannot assess whether you used "
        "a term meaningfully, and copying words from the job description to raise this number "
        "will not make your resume stronger to a human reader."
    ),
    "resume_completeness": (
        "Sections are detected from common headings and content patterns. An unconventional "
        "layout may cause a section you do have to be reported as missing."
    ),
    "measurable_achievements": (
        'Numbers are detected by pattern. A quantified outcome written in words ("halved the '
        'processing time") may be missed, and a number that is not an achievement may '
        "occasionally be counted."
    ),
    "statement_quality": (
        "Writing quality is assessed by pattern rules, not comprehension. Strong, "
        "unconventional writing may be flagged, and weak writing that follows the patterns "
        "may pass."
    ),
}

PARTIAL_CREDIT = 0.5
KEYWORD_FULL_MARKS_AT = 0.60  # Deliberate anti-gaming cap; see §3.5 of the methodology.

SECTION_POINTS: dict[str, float] = {
    "contact": 2.0,
    "experience": 2.0,
    "skills": 2.0,
    "education": 1.5,
    "summary": 1.0,
    "projects": 1.0,
    "certifications": 0.25,
    "achievements": 0.25,
    "languages": 0.0,  # Reported but not scored: relevance varies too much by role.
}
assert sum(SECTION_POINTS.values()) == WEIGHTS["resume_completeness"]


def _q2(value: float) -> float:
    """Round half-up to two decimal places (not Python's banker's rounding)."""
    return float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _q0(value: float) -> int:
    return int(Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


# --- Skill comparison ------------------------------------------------------


def compare_skills(resume: ResumeProfile, job: JobProfile) -> tuple[SkillComparison, ...]:
    """Classify every job requirement as matched, partial, or missing."""
    catalogue = skills_by_name()
    resume_names = resume.skill_names()
    comparisons: list[SkillComparison] = []

    for level, names in (("required", job.required_skills), ("preferred", job.preferred_skills)):
        for name in names:
            skill = catalogue.get(name)
            display = skill.display if skill else name
            detected = resume.skill_by_name(name)

            if detected is not None:
                comparisons.append(
                    SkillComparison(
                        skill_name=name,
                        display=display,
                        match_status="matched",
                        requirement_level=level,  # type: ignore[arg-type]
                        matched_via=detected.matched_via,
                        evidence_snippet=detected.snippet,
                    )
                )
                continue

            related_hit = _find_related(name, resume_names, catalogue)
            if related_hit is not None:
                neighbour = resume.skill_by_name(related_hit)
                comparisons.append(
                    SkillComparison(
                        skill_name=name,
                        display=display,
                        match_status="partial",
                        requirement_level=level,  # type: ignore[arg-type]
                        matched_via="related",
                        evidence_snippet=neighbour.snippet if neighbour else None,
                    )
                )
                continue

            comparisons.append(
                SkillComparison(
                    skill_name=name,
                    display=display,
                    match_status="missing",
                    requirement_level=level,  # type: ignore[arg-type]
                    matched_via=None,
                    evidence_snippet=None,
                )
            )

    return tuple(comparisons)


def _find_related(required: str, resume_names: frozenset[str], catalogue: dict) -> str | None:
    """A neighbouring skill is evidence, not proof, so it earns partial credit."""
    skill = catalogue.get(required)
    if skill is not None:
        for neighbour in skill.related:
            if neighbour in resume_names:
                return neighbour
    for name in sorted(resume_names):
        candidate = catalogue.get(name)
        if candidate is not None and required in candidate.related:
            return name
    return None


def _units(comparisons: tuple[SkillComparison, ...], level: str) -> tuple[float, int, int, int]:
    """Return (credited_units, matched, partial, total) for one requirement level."""
    subset = [c for c in comparisons if c.requirement_level == level]
    matched = sum(1 for c in subset if c.match_status == "matched")
    partial = sum(1 for c in subset if c.match_status == "partial")
    return matched + partial * PARTIAL_CREDIT, matched, partial, len(subset)


def _evidence(comparisons: tuple[SkillComparison, ...], level: str) -> list[dict]:
    return [
        {
            "skill": c.skill_name,
            "display": c.display,
            "status": c.match_status,
            "matched_via": c.matched_via,
            "snippet": c.evidence_snippet,
        }
        for c in comparisons
        if c.requirement_level == level
    ]


# --- Individual categories -------------------------------------------------


def _score_skill_category(
    key: str, comparisons: tuple[SkillComparison, ...], level: str
) -> tuple[ScoredCategory, bool]:
    weight = WEIGHTS[key]
    units, matched, partial, total = _units(comparisons, level)

    if total == 0:
        explanation = (
            f"No {level} skills could be extracted from this job description, so this "
            "category was not scored. The remaining categories were rescaled to total 100."
        )
        return (
            ScoredCategory(
                key=key,
                name=CATEGORY_NAMES[key],
                weight=weight,
                points_earned=0.0,
                points_possible=0.0,
                explanation=explanation,
                evidence=[],
                recommendation=None,
                limitation=LIMITATIONS[key],
            ),
            False,
        )

    points = weight * (units / total)
    missing = total - matched - partial

    explanation = f"Your resume matched {matched} of {total} {level} skills" + (
        f", and partially matched {partial}." if partial else "."
    )
    recommendation = None
    if missing:
        missing_names = [
            c.display
            for c in comparisons
            if c.requirement_level == level and c.match_status == "missing"
        ][:5]
        recommendation = (
            f"{missing} {level} skill(s) were not found: {', '.join(missing_names)}. "
            "Add any you genuinely have, and reference them in a project or experience bullet "
            "rather than only in a list."
        )
    elif partial:
        recommendation = (
            "Some skills matched only through a related technology. Naming the exact term used "
            "in the job description makes the match unambiguous."
        )

    return (
        ScoredCategory(
            key=key,
            name=CATEGORY_NAMES[key],
            weight=weight,
            points_earned=points,
            points_possible=weight,
            explanation=explanation,
            evidence=_evidence(comparisons, level),
            recommendation=recommendation,
            limitation=LIMITATIONS[key],
        ),
        True,
    )


def _score_experience(
    resume: ResumeProfile, job: JobProfile, comparisons: tuple[SkillComparison, ...]
) -> ScoredCategory:
    key = "experience_relevance"
    weight = WEIGHTS[key]
    duration_max, context_max = 8.0, 7.0

    months = resume.experience.total_months
    required_months = (job.min_years_experience or 0) * 12

    if job.min_years_experience is None:
        duration_points = duration_max
        duration_note = "The job description does not state a minimum experience requirement."
    elif months is None:
        # Neutral, not zero: unparseable dates are a formatting problem, not
        # evidence of missing experience.
        duration_points = 4.0
        duration_note = (
            "No employment dates could be read from your resume, so duration was scored "
            "neutrally rather than penalised."
        )
    else:
        ratio = months / required_months if required_months else 1.0
        if ratio >= 1.0:
            duration_points = duration_max
        elif ratio >= 0.6:
            duration_points = 5.0
        else:
            duration_points = 3.0
        duration_note = (
            f"Your resume shows about {months // 12} year(s) and {months % 12} month(s) of "
            f"experience against a stated requirement of {job.min_years_experience} year(s)."
        )

    required = [c for c in comparisons if c.requirement_level == "required"]
    found_anywhere = [c for c in required if c.match_status in ("matched", "partial")]
    in_experience = [
        c
        for c in found_anywhere
        if (detected := resume.skill_by_name(c.skill_name)) is not None and detected.in_experience
    ]

    if not required:
        context_points = context_max
        context_note = (
            "No required skills were extracted, so contextual relevance was not penalised."
        )
    elif not found_anywhere:
        context_points = 0.0
        context_note = "None of the required skills appear anywhere in your resume."
    else:
        context_points = context_max * (len(in_experience) / len(found_anywhere))
        context_note = (
            f"{len(in_experience)} of the {len(found_anywhere)} required skills you do have "
            "appear inside your work experience section rather than only in a list."
        )

    recommendation = None
    if context_points < context_max:
        recommendation = (
            "Reference the required technologies inside your experience bullets. A skill shown "
            "in the context of work you did is stronger evidence than one named in a list."
        )
    elif months is None and job.min_years_experience is not None:
        recommendation = (
            'Add clear date ranges to each role (for example "Jan 2023 – Present") so your '
            "total experience can be read at a glance."
        )

    return ScoredCategory(
        key=key,
        name=CATEGORY_NAMES[key],
        weight=weight,
        points_earned=duration_points + context_points,
        points_possible=weight,
        explanation=f"{duration_note} {context_note}",
        evidence=[
            {
                "measure": "duration",
                "earned": _q2(duration_points),
                "possible": duration_max,
                "detected_months": months,
                "required_months": required_months or None,
            },
            {
                "measure": "contextual_relevance",
                "earned": _q2(context_points),
                "possible": context_max,
                "skills_in_experience": len(in_experience),
                "skills_found": len(found_anywhere),
            },
        ],
        recommendation=recommendation,
        limitation=LIMITATIONS[key],
    )


def _score_education(resume: ResumeProfile, job: JobProfile) -> ScoredCategory:
    key = "education_alignment"
    weight = WEIGHTS[key]
    education_section = resume.section("education")
    has_section = education_section is not None and education_section.detected

    if job.required_education_level is None:
        return ScoredCategory(
            key=key,
            name=CATEGORY_NAMES[key],
            weight=weight,
            points_earned=weight,
            points_possible=weight,
            explanation="The job description does not state an education requirement.",
            evidence=[{"required": None, "detected": resume.education_level}],
            recommendation=None,
            limitation=LIMITATIONS[key],
        )

    required_ordinal = education_ordinal(job.required_education_level)
    resume_ordinal = education_ordinal(resume.education_level)

    if not has_section and resume.education_level == "none":
        points = 2.0
        explanation = (
            "No education section was detected, and the job description asks for a "
            f"{job.required_education_level}-level qualification."
        )
        recommendation = (
            "Add an education section with your qualification, institution, and completion "
            "year, even if the qualification is in progress."
        )
    else:
        difference = resume_ordinal - required_ordinal
        if difference >= 0:
            points = weight
            explanation = (
                f"Your highest detected qualification ({resume.education_level}) meets or "
                f"exceeds the {job.required_education_level} level requested."
            )
            recommendation = None
        elif difference == -1:
            points = 6.0
            explanation = (
                f"Your detected qualification ({resume.education_level}) is one level below "
                f"the {job.required_education_level} requested."
            )
            recommendation = (
                "Many employers accept equivalent experience. Make relevant coursework, "
                "certifications, or in-progress study visible."
            )
        else:
            points = 3.0
            explanation = (
                f"Your detected qualification ({resume.education_level}) is more than one "
                f"level below the {job.required_education_level} requested."
            )
            recommendation = (
                "Highlight certifications, courses, and practical projects that demonstrate "
                "the same knowledge."
            )

    return ScoredCategory(
        key=key,
        name=CATEGORY_NAMES[key],
        weight=weight,
        points_earned=points,
        points_possible=weight,
        explanation=explanation,
        evidence=[{"required": job.required_education_level, "detected": resume.education_level}],
        recommendation=recommendation,
        limitation=LIMITATIONS[key],
    )


def _score_keywords(resume: ResumeProfile, job: JobProfile) -> tuple[ScoredCategory, bool]:
    key = "keyword_coverage"
    weight = WEIGHTS[key]

    if not job.keywords:
        return (
            ScoredCategory(
                key=key,
                name=CATEGORY_NAMES[key],
                weight=weight,
                points_earned=0.0,
                points_possible=0.0,
                explanation=(
                    "No distinctive keywords could be extracted from this job description, so "
                    "this category was not scored. The remaining categories were rescaled."
                ),
                evidence=[],
                recommendation=None,
                limitation=LIMITATIONS[key],
            ),
            False,
        )

    present = [word for word in job.keywords if word in resume.keywords_present]
    ratio = len(present) / len(job.keywords)
    points = weight * min(1.0, ratio / KEYWORD_FULL_MARKS_AT)
    missing = [word for word in job.keywords if word not in resume.keywords_present]

    explanation = (
        f"Your resume contains {len(present)} of the {len(job.keywords)} most frequent "
        f"non-skill terms in this posting ({round(ratio * 100)}%). Full marks are awarded at "
        f"{round(KEYWORD_FULL_MARKS_AT * 100)}% rather than 100%, so that padding your resume "
        "with job-description vocabulary cannot inflate the score."
    )
    recommendation = (
        "Where these terms genuinely describe your work, use the posting's wording: "
        f"{', '.join(missing[:8])}."
        if missing
        else None
    )

    return (
        ScoredCategory(
            key=key,
            name=CATEGORY_NAMES[key],
            weight=weight,
            points_earned=points,
            points_possible=weight,
            explanation=explanation,
            evidence=[{"present": present, "missing": missing[:15]}],
            recommendation=recommendation,
            limitation=LIMITATIONS[key],
        ),
        True,
    )


def _score_completeness(resume: ResumeProfile) -> ScoredCategory:
    key = "resume_completeness"
    weight = WEIGHTS[key]

    earned = 0.0
    evidence: list[dict] = []
    missing_scored: list[str] = []

    for section in resume.sections:
        available = SECTION_POINTS.get(section.key, 0.0)
        if section.detected:
            earned += available
        elif available > 0:
            missing_scored.append(section.key)
        evidence.append(
            {
                "section": section.key,
                "detected": section.detected,
                "points": available,
                "heading": section.matched_heading,
            }
        )

    explanation = (
        f"{sum(1 for s in resume.sections if s.detected)} of {len(resume.sections)} standard "
        "sections were detected. Sections are weighted by how much a reader relies on them; "
        "languages is reported but not scored, because its relevance varies too much by role."
    )
    recommendation = f"Consider adding: {', '.join(missing_scored)}." if missing_scored else None

    return ScoredCategory(
        key=key,
        name=CATEGORY_NAMES[key],
        weight=weight,
        points_earned=earned,
        points_possible=weight,
        explanation=explanation,
        evidence=evidence,
        recommendation=recommendation,
        limitation=LIMITATIONS[key],
    )


def _score_achievements(resume: ResumeProfile) -> ScoredCategory:
    key = "measurable_achievements"
    weight = WEIGHTS[key]
    count = resume.statements.with_measurable_result

    # Bands rather than a ratio: this measures the habit of quantifying, not a
    # density figure that would reward short resumes.
    if count == 0:
        points = 0.0
    elif count <= 2:
        points = 4.0
    elif count <= 4:
        points = 7.0
    else:
        points = weight

    explanation = (
        f"{count} of your {resume.statements.total_bullets} statements contain a measurable "
        "result such as a percentage, an amount, a count, or a time saved."
    )
    recommendation = (
        "Add outcomes to your strongest bullets. Use only figures you can substantiate — an "
        "invented number is worse than none."
        if count < 5
        else None
    )

    return ScoredCategory(
        key=key,
        name=CATEGORY_NAMES[key],
        weight=weight,
        points_earned=points,
        points_possible=weight,
        explanation=explanation,
        evidence=[
            {"measurable_statements": count, "total_statements": resume.statements.total_bullets}
        ],
        recommendation=recommendation,
        limitation=LIMITATIONS[key],
    )


def _score_statement_quality(resume: ResumeProfile) -> ScoredCategory:
    key = "statement_quality"
    weight = WEIGHTS[key]
    analysis = resume.statements
    if analysis.total_bullets == 0:
        return ScoredCategory(
            key=key,
            name=CATEGORY_NAMES[key],
            weight=weight,
            points_earned=0,
            points_possible=0,
            explanation="No readable bullet statements were detected; writing quality cannot be assessed.",
            evidence=[],
            recommendation="Use clear bullet statements describing your work.",
            limitation=LIMITATIONS[key],
        )

    points = weight
    deductions: list[dict] = []

    def deduct(amount: float, reason: str) -> None:
        nonlocal points
        points -= amount
        deductions.append({"reason": reason, "points": -amount})

    if analysis.total_bullets and analysis.action_verb_rate < 0.5:
        deduct(
            1.5,
            f"Only {round(analysis.action_verb_rate * 100)}% of statements open with an action verb",
        )

    generic = sum(1 for f in analysis.findings if ISSUE_GENERIC_PHRASING in f.issue_codes)
    if generic >= 3:
        deduct(1.5, f'{generic} statements use generic phrasing such as "responsible for"')

    passive = sum(1 for f in analysis.findings if ISSUE_PASSIVE_VOICE in f.issue_codes)
    if passive >= 2:
        deduct(1.0, f"{passive} statements are written in the passive voice")

    too_long = sum(1 for f in analysis.findings if ISSUE_TOO_LONG in f.issue_codes)
    if too_long >= 2:
        deduct(1.0, f"{too_long} statements are longer than 35 words")

    if analysis.repeated_phrases:
        deduct(1.0, f"{len(analysis.repeated_phrases)} phrase(s) are repeated three or more times")

    points = max(0.0, points)

    explanation = (
        "Statement quality starts at full marks; points are deducted for patterns that weaken "
        "a resume."
        if deductions
        else "No weakening patterns were detected across your statements."
    )
    recommendation = (
        "Rewrite the flagged statements to open with an action verb and to state what changed "
        "as a result of your work."
        if deductions
        else None
    )

    return ScoredCategory(
        key=key,
        name=CATEGORY_NAMES[key],
        weight=weight,
        points_earned=points,
        points_possible=weight,
        explanation=explanation,
        evidence=deductions,
        recommendation=recommendation,
        limitation=LIMITATIONS[key],
    )


# --- Entry point -----------------------------------------------------------


def compute_score(resume: ResumeProfile, job: JobProfile) -> ScoreBreakdown:
    """Produce the full, explainable breakdown. Pure and deterministic."""
    comparisons = compare_skills(resume, job)

    required_category, required_applicable = _score_skill_category(
        "required_skills", comparisons, "required"
    )
    preferred_category, preferred_applicable = _score_skill_category(
        "preferred_skills", comparisons, "preferred"
    )
    keyword_category, keyword_applicable = _score_keywords(resume, job)

    scored: list[tuple[ScoredCategory, bool]] = [
        (required_category, required_applicable),
        (_score_experience(resume, job, comparisons), True),
        (preferred_category, preferred_applicable),
        (_score_education(resume, job), True),
        (keyword_category, keyword_applicable),
        (_score_completeness(resume), True),
        (_score_achievements(resume), True),
        (_score_statement_quality(resume), resume.statements.total_bullets > 0),
    ]

    # Rescale so the applicable categories always total exactly 100. A job with
    # no preferred skills must not cost the candidate ten points.
    applicable_weight = sum(cat.weight for cat, ok in scored if ok)
    factor = 100.0 / applicable_weight if applicable_weight else 0.0
    possible = {cat.key: _q2(cat.points_possible * factor) for cat, ok in scored if ok}
    # Put the rounding residual on the largest category (stable rubric order
    # breaks ties). Displayed maxima must add to 100, including sparse inputs.
    if possible:
        largest = max(possible, key=possible.__getitem__)
        possible[largest] = _q2(possible[largest] + 100.0 - sum(possible.values()))

    categories: list[ScoredCategory] = []
    for category, applicable in scored:
        if not applicable:
            categories.append(
                ScoredCategory(
                    key=category.key,
                    name=category.name,
                    weight=category.weight,
                    points_earned=0.0,
                    points_possible=0.0,
                    explanation=category.explanation,
                    evidence=category.evidence,
                    recommendation=category.recommendation,
                    limitation=category.limitation,
                )
            )
            continue
        categories.append(
            ScoredCategory(
                key=category.key,
                name=category.name,
                weight=category.weight,
                points_earned=_q2(
                    category.points_earned / category.points_possible * possible[category.key]
                ),
                points_possible=possible[category.key],
                explanation=category.explanation,
                evidence=category.evidence,
                recommendation=category.recommendation,
                limitation=category.limitation,
            )
        )

    overall = _q0(sum(category.points_earned for category in categories))
    return ScoreBreakdown(
        overall_score=max(0, min(100, overall)),
        categories=tuple(categories),
        skill_comparisons=comparisons,
    )
