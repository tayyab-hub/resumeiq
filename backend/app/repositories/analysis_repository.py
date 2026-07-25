"""All analysis database access.

Ownership is a property of every query in this module, not a check a route
author might forget: `owner_id` is a required parameter, so a new endpoint
cannot accidentally read another user's data.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.analysis import Analysis, SkillMatch


def _with_children(statement):
    return statement.options(
        selectinload(Analysis.job_description),
        selectinload(Analysis.score_categories),
        selectinload(Analysis.skill_matches),
        selectinload(Analysis.sections),
        selectinload(Analysis.statement_findings),
        selectinload(Analysis.recommendations),
    )


def get_owned(db: Session, analysis_id: uuid.UUID, owner_id: uuid.UUID) -> Analysis | None:
    """Filter by owner rather than fetch-then-check.

    Returning None for someone else's row lets the route answer 404, so an
    analysis ID cannot be confirmed to exist by probing.
    """
    statement = _with_children(
        select(Analysis).where(Analysis.id == analysis_id, Analysis.user_id == owner_id)
    )
    return db.execute(statement).scalar_one_or_none()


def list_for_owner(
    db: Session, owner_id: uuid.UUID, *, page: int = 1, page_size: int = 10
) -> tuple[Sequence[Analysis], int]:
    total = db.execute(
        select(func.count()).select_from(Analysis).where(Analysis.user_id == owner_id)
    ).scalar_one()

    rows = db.execute(
        select(Analysis)
        .where(Analysis.user_id == owner_id)
        .options(selectinload(Analysis.job_description))
        .order_by(Analysis.created_at.desc())
        .offset(max(0, (page - 1) * page_size))
        .limit(page_size)
    ).scalars().all()

    return rows, total


def delete_owned(db: Session, analysis_id: uuid.UUID, owner_id: uuid.UUID) -> bool:
    analysis = db.execute(
        select(Analysis).where(Analysis.id == analysis_id, Analysis.user_id == owner_id)
    ).scalar_one_or_none()
    if analysis is None:
        return False
    # ORM-level delete so the configured cascades run on every engine.
    db.delete(analysis)
    db.commit()
    return True


def rename_owned(
    db: Session, analysis_id: uuid.UUID, owner_id: uuid.UUID, title: str
) -> Analysis | None:
    analysis = db.execute(
        select(Analysis).where(Analysis.id == analysis_id, Analysis.user_id == owner_id)
    ).scalar_one_or_none()
    if analysis is None:
        return None
    analysis.title = title
    db.commit()
    db.refresh(analysis)
    return analysis


def dashboard_stats(db: Session, owner_id: uuid.UUID) -> dict:
    rows = db.execute(
        select(Analysis.overall_score, Analysis.created_at)
        .where(Analysis.user_id == owner_id)
        .order_by(Analysis.created_at.asc())
    ).all()

    if not rows:
        return {
            "total_analyses": 0,
            "average_score": None,
            "best_score": None,
            "analyses_this_month": 0,
            "score_trend": [],
            "common_missing_skills": [],
        }

    scores = [row[0] for row in rows]
    month_ago = datetime.now(UTC) - timedelta(days=30)

    def _aware(value: datetime) -> datetime:
        return value if value.tzinfo else value.replace(tzinfo=UTC)

    missing = db.execute(
        select(SkillMatch.skill_name, func.count().label("occurrences"))
        .join(Analysis, Analysis.id == SkillMatch.analysis_id)
        .where(
            Analysis.user_id == owner_id,
            SkillMatch.match_status == "missing",
            SkillMatch.requirement_level == "required",
        )
        .group_by(SkillMatch.skill_name)
        .order_by(func.count().desc())
        .limit(8)
    ).all()

    return {
        "total_analyses": len(scores),
        "average_score": round(sum(scores) / len(scores), 1),
        "best_score": max(scores),
        "analyses_this_month": sum(1 for _, created in rows if _aware(created) >= month_ago),
        "score_trend": [
            {"date": _aware(created).date().isoformat(), "score": score}
            for score, created in rows[-20:]
        ],
        "common_missing_skills": [
            {"skill": name, "occurrences": count} for name, count in missing
        ],
    }
