"""Orchestrates one analysis: extract, analyse, score, persist, then enrich.

The ordering matters and is load-bearing: the analysis is committed *before*
the AI call. If the provider hangs or fails, the user's result already exists.
"""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy.orm import Session

from app.analyzers.domain import JobProfile, ResumeProfile, ScoreBreakdown
from app.analyzers.jd_parser import parse_job_description
from app.analyzers.pdf_extractor import extract_text
from app.analyzers.resume_analyzer import build_resume_profile
from app.analyzers.scorer import compute_score
from app.core.config import settings
from app.core.error_codes import JOB_DESCRIPTION_TOO_LONG, JOB_DESCRIPTION_TOO_SHORT
from app.core.exceptions import AppError
from app.models.analysis import (
    Analysis,
    JobDescription,
    Recommendation,
    ResumeSection,
    ScoreCategory,
    SkillMatch,
    StatementFinding,
)
from app.services import ai_service
from app.services.recommendation_builder import build_rule_recommendations

MAX_STATEMENT_ROWS = 30


def validate_job_description(text: str) -> str:
    cleaned = (text or "").strip()
    if len(cleaned) < settings.min_job_description_chars:
        raise AppError(JOB_DESCRIPTION_TOO_SHORT)
    if len(cleaned) > settings.max_job_description_chars:
        raise AppError(JOB_DESCRIPTION_TOO_LONG)
    return cleaned


def run_analysis(
    resume_bytes: bytes, job_description: str, *, today: date | None = None
) -> tuple[ResumeProfile, JobProfile, ScoreBreakdown, str]:
    """The deterministic core. No database, no network, no AI."""
    text = extract_text(resume_bytes, min_chars=settings.min_extracted_chars)
    resume = build_resume_profile(text, today=today)
    job = parse_job_description(job_description)
    breakdown = compute_score(resume, job)
    return resume, job, breakdown, text


def persist_analysis(
    db: Session,
    *,
    user_id: uuid.UUID,
    title: str,
    resume_filename: str,
    resume_text: str,
    store_resume_text: bool,
    resume: ResumeProfile,
    job: JobProfile,
    breakdown: ScoreBreakdown,
    job_title: str | None,
    company_name: str | None,
    raw_job_description: str,
) -> Analysis:
    analysis = Analysis(
        user_id=user_id,
        title=title[:120],
        resume_filename=resume_filename[:255],
        overall_score=breakdown.overall_score,
        store_resume_text=store_resume_text,
        # Absent unless the user opted in. The database CHECK constraint
        # enforces the same rule independently of this line.
        resume_text=resume_text if store_resume_text else None,
        # Whole-resume statistics. Stored because `statement_findings` below
        # keeps only the flagged subset, and a strong resume's quantified
        # bullets are precisely the ones that never get flagged.
        statements_total=resume.statements.total_bullets,
        statements_with_metric=resume.statements.with_measurable_result,
        statements_action_verb_rate=resume.statements.action_verb_rate,
        ai_status="unavailable",
        ai_reason_code=None,
    )

    analysis.job_description = JobDescription(
        job_title=job_title or job.job_title,
        company_name=company_name or job.company_name,
        raw_text=raw_job_description,
        min_years_experience=job.min_years_experience,
        required_education_level=job.required_education_level,
        requirement_split_inferred=job.requirement_split_inferred,
    )

    analysis.score_categories = [
        ScoreCategory(
            category_key=category.key,
            category_name=category.name,
            weight=category.weight,
            points_earned=category.points_earned,
            points_possible=category.points_possible,
            explanation=category.explanation,
            evidence=category.evidence,
            recommendation=category.recommendation,
            limitation=category.limitation,
            display_order=index,
        )
        for index, category in enumerate(breakdown.categories)
    ]

    analysis.skill_matches = [
        SkillMatch(
            skill_name=comparison.skill_name,
            match_status=comparison.match_status,
            requirement_level=comparison.requirement_level,
            matched_via=comparison.matched_via,
            evidence_snippet=(comparison.evidence_snippet or "")[:240] or None,
        )
        for comparison in breakdown.skill_comparisons
    ]

    analysis.sections = [
        ResumeSection(
            section_key=section.key,
            detected=section.detected,
            matched_heading=section.matched_heading,
            note=section.note,
            display_order=index,
        )
        for index, section in enumerate(resume.sections)
    ]

    # Bounded storage: only the bullets the user needs to see again.
    analysis.statement_findings = [
        StatementFinding(
            statement_text=finding.text[:600],
            issue_codes=list(finding.issue_codes),
            word_count=finding.word_count,
            has_measurable_result=finding.has_measurable_result,
            suggestion=finding.suggestion,
        )
        for finding in resume.statements.findings[:MAX_STATEMENT_ROWS]
    ]

    analysis.recommendations = [
        Recommendation(**row) for row in build_rule_recommendations(resume, job, breakdown)
    ]

    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return analysis


def enrich_with_ai(
    db: Session, analysis: Analysis, resume: ResumeProfile, job: JobProfile,
    breakdown: ScoreBreakdown,
) -> Analysis:
    """Attach AI recommendations if the provider cooperates.

    Never raises, and never removes the rule-based recommendations that are
    already stored.
    """
    payload, reason = ai_service.generate_recommendations(resume, job, breakdown)

    if payload is None:
        analysis.ai_status = "unavailable"
        analysis.ai_reason_code = reason
        db.commit()
        db.refresh(analysis)
        return analysis

    next_order = len(analysis.recommendations)
    for row in ai_service.to_recommendation_rows(payload, next_order):
        analysis.recommendations.append(Recommendation(analysis_id=analysis.id, **row))

    analysis.ai_status = "available"
    analysis.ai_reason_code = None
    db.commit()
    db.refresh(analysis)
    return analysis


def replace_ai_recommendations(
    db: Session, analysis: Analysis, resume: ResumeProfile, job: JobProfile,
    breakdown: ScoreBreakdown,
) -> Analysis:
    """Re-run AI enrichment for a stored analysis, discarding previous AI rows.

    Rule-based recommendations are untouched, so a failed retry still leaves a
    complete result.
    """
    analysis.recommendations = [r for r in analysis.recommendations if r.source == "rule"]
    db.commit()
    return enrich_with_ai(db, analysis, resume, job, breakdown)
