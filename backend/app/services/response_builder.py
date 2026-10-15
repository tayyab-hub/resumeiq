"""Converts a persisted Analysis into the API response shape."""

from __future__ import annotations

from app.models.analysis import Analysis
from app.schemas.analysis import (
    DISCLAIMER,
    AnalysisDetailOut,
    JobAnalysisOut,
    RecommendationOut,
    ResumeSectionOut,
    ScoreCategoryOut,
    SkillGroupsOut,
    SkillMatchOut,
    StatementFindingOut,
    StatementSummaryOut,
)
from app.services.ai_service import AI_AVAILABLE_MESSAGE, AI_UNAVAILABLE_MESSAGE

_PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def to_detail(analysis: Analysis) -> AnalysisDetailOut:
    matches = [SkillMatchOut.model_validate(match) for match in analysis.skill_matches]
    job = analysis.job_description
    warnings = []
    if not matches:
        warnings.append(
            "Insufficient recognised job-skill evidence: interpret this as a resume-quality rubric, not a reliable job-match estimate."
        )
    if not analysis.statements_total:
        warnings.append(
            "No readable bullet statements were detected. Statement quality is not assessed."
        )
    if job and job.requirement_split_inferred:
        warnings.append(
            "Required/preferred headings were not detected; recognised skills were treated as required."
        )

    findings = [
        StatementFindingOut.model_validate(finding) for finding in analysis.statement_findings
    ]

    recommendations = sorted(
        analysis.recommendations,
        key=lambda rec: (_PRIORITY_ORDER.get(rec.priority, 3), rec.display_order),
    )

    return AnalysisDetailOut(
        id=analysis.id,
        title=analysis.title,
        resume_filename=analysis.resume_filename,
        created_at=analysis.created_at,
        overall_score=analysis.overall_score,
        disclaimer=DISCLAIMER,
        evidence_warnings=warnings,
        score_breakdown=[
            ScoreCategoryOut(
                category_key=category.category_key,
                category_name=category.category_name,
                weight=float(category.weight),
                points_earned=float(category.points_earned),
                points_possible=float(category.points_possible),
                explanation=category.explanation,
                evidence=category.evidence,
                recommendation=category.recommendation,
                limitation=category.limitation,
            )
            for category in analysis.score_categories
        ],
        skills=SkillGroupsOut(
            matched=[m for m in matches if m.match_status == "matched"],
            partial=[m for m in matches if m.match_status == "partial"],
            missing=[m for m in matches if m.match_status == "missing"],
        ),
        sections=[ResumeSectionOut.model_validate(section) for section in analysis.sections],
        statements=StatementSummaryOut(
            # Read from the stored totals, not from `findings`: that list holds
            # only the flagged statements, so counting metrics in it would
            # report zero for a resume whose quantified bullets all passed.
            total_bullets=analysis.statements_total,
            with_measurable_result=analysis.statements_with_metric,
            action_verb_rate=float(analysis.statements_action_verb_rate),
            findings=findings,
        ),
        job_analysis=JobAnalysisOut(
            job_title=job.job_title if job else None,
            company_name=job.company_name if job else None,
            min_years_experience=job.min_years_experience if job else None,
            required_education_level=job.required_education_level if job else None,
            requirement_split_inferred=job.requirement_split_inferred if job else False,
            required_skills=[m.skill_name for m in matches if m.requirement_level == "required"],
            preferred_skills=[m.skill_name for m in matches if m.requirement_level == "preferred"],
        ),
        recommendations=[RecommendationOut.model_validate(rec) for rec in recommendations],
        ai_status=analysis.ai_status,  # type: ignore[arg-type]
        ai_reason_code=analysis.ai_reason_code,
        ai_message=(
            AI_AVAILABLE_MESSAGE if analysis.ai_status == "available" else AI_UNAVAILABLE_MESSAGE
        ),
    )
