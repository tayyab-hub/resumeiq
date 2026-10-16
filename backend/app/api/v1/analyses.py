"""Analysis endpoints — the core of the application."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, File, Form, Header, Query, Response, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.core.config import settings
from app.core.error_codes import (
    AI_QUOTA_EXCEEDED,
    ANALYSIS_NOT_FOUND,
    RATE_LIMITED,
    RESUME_INVALID_TYPE,
    RESUME_MISSING,
    RESUME_TOO_LARGE,
)
from app.core.exceptions import AppError
from app.database.session import get_db
from app.models.analysis import Analysis
from app.models.user import User
from app.repositories import analysis_repository as repo
from app.schemas.analysis import (
    AnalysisDetailOut,
    AnalysisListOut,
    AnalysisSummaryOut,
    DashboardStatsOut,
    RenameAnalysisRequest,
)
from app.security.dependencies import get_current_user
from app.security.rate_limit import SECONDS_PER_DAY, limiter
from app.services import analysis_service
from app.services.response_builder import to_detail
from app.utilities.files import has_pdf_extension, sanitise_filename

router = APIRouter(prefix="/analyses", tags=["analyses"])

ALLOWED_MIME_TYPES = {"application/pdf", "application/x-pdf", "application/octet-stream"}
_CHUNK_SIZE = 64 * 1024


async def _read_upload_within_limit(upload: UploadFile, limit: int) -> bytes:
    """Read the body in chunks, aborting as soon as the limit is passed.

    Reading the whole body first and checking afterwards would let a large
    upload consume memory before being rejected.
    """
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await upload.read(_CHUNK_SIZE)
        if not chunk:
            break
        total += len(chunk)
        if total > limit:
            raise AppError(RESUME_TOO_LARGE)
        chunks.append(chunk)
    return b"".join(chunks)


def _summary(analysis) -> AnalysisSummaryOut:
    return AnalysisSummaryOut(
        id=analysis.id,
        title=analysis.title,
        job_title=analysis.job_description.job_title if analysis.job_description else None,
        overall_score=analysis.overall_score,
        created_at=analysis.created_at,
    )


@router.post("", response_model=AnalysisDetailOut, status_code=status.HTTP_201_CREATED)
async def create_analysis(
    response: Response,
    resume: UploadFile | None = File(default=None),
    job_description: str = Form(...),
    job_title: str | None = Form(default=None, max_length=160),
    company_name: str | None = Form(default=None, max_length=160),
    title: str | None = Form(default=None, max_length=120),
    store_resume_text: bool = Form(default=False),
    idempotency_key: uuid.UUID | None = Header(default=None, alias="X-Idempotency-Key"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AnalysisDetailOut:
    if idempotency_key:
        existing = db.scalar(
            select(Analysis).where(
                Analysis.user_id == current_user.id,
                Analysis.request_key == str(idempotency_key),
            )
        )
        if existing is not None:
            response.status_code = status.HTTP_200_OK
            return to_detail(existing)
    quota_key = f"analyses:{current_user.id}"
    retry_after = limiter.consume(quota_key, settings.analyses_per_day, SECONDS_PER_DAY)
    if retry_after is not None:
        response.headers["Retry-After"] = str(retry_after)
        raise AppError(RATE_LIMITED, retry_after=retry_after)

    if resume is None or not resume.filename:
        raise AppError(RESUME_MISSING)

    # These are format hints; the isolated parser also checks PDF structure.
    if not has_pdf_extension(resume.filename):
        raise AppError(RESUME_INVALID_TYPE)
    if resume.content_type and resume.content_type.lower() not in ALLOWED_MIME_TYPES:
        raise AppError(RESUME_INVALID_TYPE)

    cleaned_jd = analysis_service.validate_job_description(job_description)
    try:
        data = await _read_upload_within_limit(resume, settings.max_upload_bytes)
    finally:
        await resume.close()

    resume_profile, job_profile, breakdown, extracted_text = await run_in_threadpool(
        analysis_service.run_analysis, data, cleaned_jd
    )

    safe_filename = sanitise_filename(resume.filename)
    resolved_title = (title or "").strip() or (
        f"{job_profile.job_title} — {job_profile.company_name}"
        if job_profile.job_title and job_profile.company_name
        else job_profile.job_title or f"Analysis {datetime.now(UTC):%d %b %Y}"
    )

    analysis = analysis_service.persist_analysis(
        db,
        user_id=current_user.id,
        title=resolved_title,
        resume_filename=safe_filename,
        resume_text=extracted_text,
        store_resume_text=store_resume_text,
        resume=resume_profile,
        job=job_profile,
        breakdown=breakdown,
        job_title=(job_title or "").strip() or None,
        company_name=(company_name or "").strip() or None,
        raw_job_description=cleaned_jd,
        request_key=str(idempotency_key) if idempotency_key else None,
    )

    # The analysis is already committed. Everything below is enrichment, and
    # its failure cannot lose the user's result.
    ai_key = f"ai:{current_user.id}"
    if limiter.consume(ai_key, settings.ai_calls_per_day, SECONDS_PER_DAY) is None:
        analysis = analysis_service.enrich_with_ai(
            db, analysis, resume_profile, job_profile, breakdown
        )
    else:
        analysis.ai_status = "unavailable"
        analysis.ai_reason_code = "quota_exceeded"
        db.commit()
        db.refresh(analysis)

    return to_detail(analysis)


@router.get("", response_model=AnalysisListOut)
def list_analyses(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AnalysisListOut:
    rows, total = repo.list_for_owner(db, current_user.id, page=page, page_size=page_size)
    return AnalysisListOut(
        items=[_summary(row) for row in rows],
        total=total,
        page=page,
        page_size=page_size,
        has_next=page * page_size < total,
    )


@router.get("/stats/summary", response_model=DashboardStatsOut)
def dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardStatsOut:
    # Zero analyses returns zeroed counters, never a 404: the empty state is
    # the frontend's job, not an error.
    return DashboardStatsOut(**repo.dashboard_stats(db, current_user.id))


@router.get("/{analysis_id}", response_model=AnalysisDetailOut)
def get_analysis(
    analysis_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AnalysisDetailOut:
    analysis = repo.get_owned(db, analysis_id, current_user.id)
    if analysis is None:
        # 404 rather than 403: a 403 would confirm that the ID exists.
        raise AppError(ANALYSIS_NOT_FOUND)
    return to_detail(analysis)


@router.patch("/{analysis_id}", response_model=AnalysisSummaryOut)
def rename_analysis(
    analysis_id: uuid.UUID,
    payload: RenameAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AnalysisSummaryOut:
    analysis = repo.rename_owned(db, analysis_id, current_user.id, payload.title.strip())
    if analysis is None:
        raise AppError(ANALYSIS_NOT_FOUND)
    return _summary(analysis)


@router.delete("/{analysis_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_analysis(
    analysis_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    if not repo.delete_owned(db, analysis_id, current_user.id):
        raise AppError(ANALYSIS_NOT_FOUND)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{analysis_id}/recommendations", response_model=AnalysisDetailOut)
def regenerate_recommendations(
    analysis_id: uuid.UUID,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AnalysisDetailOut:
    """Re-run AI enrichment for a stored analysis.

    Requires the resume text, so it is available only for analyses the user
    chose to store. The rule-based recommendations remain regardless.
    """
    analysis = repo.get_owned(db, analysis_id, current_user.id)
    if analysis is None:
        raise AppError(ANALYSIS_NOT_FOUND)

    ai_key = f"ai:{current_user.id}"
    retry_after = limiter.consume(ai_key, settings.ai_calls_per_day, SECONDS_PER_DAY)
    if retry_after is not None:
        response.headers["Retry-After"] = str(retry_after)
        raise AppError(AI_QUOTA_EXCEEDED, retry_after=retry_after)

    if not analysis.resume_text or not analysis.job_description:
        analysis.ai_status = "unavailable"
        analysis.ai_reason_code = "resume_text_not_stored"
        db.commit()
        db.refresh(analysis)
        return to_detail(analysis)

    from app.analyzers.jd_parser import parse_job_description
    from app.analyzers.resume_analyzer import build_resume_profile
    from app.analyzers.scorer import compute_score

    resume_profile = build_resume_profile(analysis.resume_text)
    job_profile = parse_job_description(analysis.job_description.raw_text)
    breakdown = compute_score(resume_profile, job_profile)

    analysis = analysis_service.replace_ai_recommendations(
        db, analysis, resume_profile, job_profile, breakdown
    )
    return to_detail(analysis)
