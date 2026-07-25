"""Rule-based recommendations.

These are the deterministic baseline. They are always produced, whether or not
the AI service is available, which is what makes FR-F3 true: an AI outage
degrades the richness of the advice, never the existence of it.
"""

from __future__ import annotations

from app.analyzers.domain import JobProfile, ResumeProfile, ScoreBreakdown, SkillComparison


def _missing(comparisons: tuple[SkillComparison, ...], level: str) -> list[SkillComparison]:
    return [c for c in comparisons if c.requirement_level == level and c.match_status == "missing"]


def build_rule_recommendations(
    resume: ResumeProfile, job: JobProfile, breakdown: ScoreBreakdown
) -> list[dict]:
    """Return recommendation dicts ordered by priority, highest impact first."""
    recommendations: list[dict] = []

    missing_required = _missing(breakdown.skill_comparisons, "required")
    if missing_required:
        names = ", ".join(c.display for c in missing_required[:6])
        recommendations.append({
            "priority": "high",
            "source": "rule",
            "category": "skills",
            "title": f"{len(missing_required)} required skill(s) are missing",
            "detail": (
                f"These requirements do not appear anywhere in your resume: {names}. "
                "Add the ones you genuinely have — ideally inside an experience or project "
                "bullet rather than only in a list. Do not add a skill you cannot discuss in "
                "an interview."
            ),
        })

    partial = [
        c for c in breakdown.skill_comparisons
        if c.requirement_level == "required" and c.match_status == "partial"
    ]
    if partial:
        recommendations.append({
            "priority": "medium",
            "source": "rule",
            "category": "skills",
            "title": "Some skills matched only through a related technology",
            "detail": (
                "These matched indirectly: "
                f"{', '.join(c.display for c in partial[:6])}. If you have used the exact "
                "technology named in the posting, use that exact term so the match is "
                "unambiguous."
            ),
        })

    missing_sections = [
        section.key for section in resume.sections
        if not section.detected and section.key in {"summary", "skills", "experience", "education", "projects"}
    ]
    if missing_sections:
        recommendations.append({
            "priority": "high" if len(missing_sections) > 1 else "medium",
            "source": "rule",
            "category": "sections",
            "title": f"Add {len(missing_sections)} missing resume section(s)",
            "detail": (
                f"These standard sections were not detected: {', '.join(missing_sections)}. "
                "Either they are absent, or their headings are unconventional enough that an "
                "automated screen may also miss them. Use plain headings such as "
                '"Work Experience" and "Skills".'
            ),
        })

    if resume.statements.with_measurable_result < 3:
        recommendations.append({
            "priority": "high",
            "source": "rule",
            "category": "statements",
            "title": "Add measurable outcomes to your strongest statements",
            "detail": (
                f"Only {resume.statements.with_measurable_result} of "
                f"{resume.statements.total_bullets} statements contain a measurable result. "
                "Aim for five. Use figures you can substantiate — a percentage, a count, a "
                "time saved. Never estimate or invent a number for a resume."
            ),
        })

    if resume.statements.total_bullets and resume.statements.action_verb_rate < 0.6:
        recommendations.append({
            "priority": "medium",
            "source": "rule",
            "category": "statements",
            "title": "Open more statements with an action verb",
            "detail": (
                f"{round(resume.statements.action_verb_rate * 100)}% of your statements begin "
                "with an action verb. Starting with a verb such as \"Built\", \"Reduced\", or "
                "\"Automated\" puts your contribution first."
            ),
        })

    generic_findings = [
        f for f in resume.statements.findings if "GENERIC_PHRASING" in f.issue_codes
    ]
    if generic_findings:
        recommendations.append({
            "priority": "medium",
            "source": "rule",
            "category": "statements",
            "title": f"Rewrite {len(generic_findings)} statement(s) that describe duties rather than results",
            "detail": (
                'Phrases such as "responsible for" and "worked on" describe a job description, '
                "not your contribution. Replace them with what you did and what changed as a "
                "result."
            ),
        })

    if job.min_years_experience is not None and resume.experience.total_months is None:
        recommendations.append({
            "priority": "medium",
            "source": "rule",
            "category": "experience",
            "title": "Add clear date ranges to each role",
            "detail": (
                "No employment dates could be read from your resume, and this posting asks for "
                f"{job.min_years_experience} year(s) of experience. Use a consistent format "
                'such as "Jan 2023 – Present" so your total experience is obvious.'
            ),
        })

    missing_preferred = _missing(breakdown.skill_comparisons, "preferred")
    if missing_preferred:
        recommendations.append({
            "priority": "low",
            "source": "rule",
            "category": "skills",
            "title": "Preferred skills you could develop",
            "detail": (
                "These are listed as preferred rather than required: "
                f"{', '.join(c.display for c in missing_preferred[:6])}. They are a reasonable "
                "target for study if you are pursuing similar roles."
            ),
        })

    if job.requirement_split_inferred:
        recommendations.append({
            "priority": "low",
            "source": "rule",
            "category": "skills",
            "title": "This posting did not separate required from preferred skills",
            "detail": (
                "No \"nice to have\" or \"preferred\" section was found, so every requirement "
                "was treated as required. Your score may be stricter than the employer intends. "
                "Read the posting yourself to judge which requirements are genuinely essential."
            ),
        })

    order = {"high": 0, "medium": 1, "low": 2}
    recommendations.sort(key=lambda item: order[item["priority"]])
    for index, item in enumerate(recommendations):
        item["display_order"] = index
    return recommendations
