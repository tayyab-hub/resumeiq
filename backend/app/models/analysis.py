"""The analysis aggregate: root row plus its six child tables.

Storage rules enforced here rather than only in code:
  * There is no column anywhere that can hold the uploaded PDF.
  * `resume_text` is NULL unless `store_resume_text` is true, guaranteed by a
    CHECK constraint so a future code path cannot quietly violate it.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import (
    Base,
    JsonType,
    UuidType,
    created_at_column,
    updated_at_column,
    uuid_pk,
)
from app.models.user import User


class Analysis(Base):
    __tablename__ = "analyses"
    __table_args__ = (
        CheckConstraint("overall_score >= 0 AND overall_score <= 100", name="ck_analyses_score_range"),
        # The privacy guarantee lives in the schema, not only in application
        # code: resume text cannot exist without the user's explicit opt-in.
        CheckConstraint(
            "store_resume_text OR resume_text IS NULL",
            name="ck_analyses_resume_text_optin",
        ),
        Index("ix_analyses_user_created", "user_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        UuidType, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    title: Mapped[str] = mapped_column(String(120), nullable=False)
    # Sanitised display label only. Never used to build a filesystem path.
    resume_filename: Mapped[str] = mapped_column(String(255), nullable=False)

    # Denormalised from score_categories so the history list and dashboard need
    # no aggregate join. Written once, in the same transaction, never mutated.
    overall_score: Mapped[int] = mapped_column(SmallInteger, nullable=False)

    store_resume_text: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    resume_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    ai_status: Mapped[str] = mapped_column(String(20), nullable=False, default="unavailable")
    ai_reason_code: Mapped[str | None] = mapped_column(String(40), nullable=True)

    created_at: Mapped[datetime] = created_at_column()
    updated_at: Mapped[datetime] = updated_at_column()

    user: Mapped[User] = relationship(back_populates="analyses")
    job_description: Mapped[JobDescription] = relationship(
        back_populates="analysis", cascade="all, delete-orphan",
        passive_deletes=True, uselist=False,
    )
    score_categories: Mapped[list[ScoreCategory]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan", passive_deletes=True,
        order_by="ScoreCategory.display_order",
    )
    skill_matches: Mapped[list[SkillMatch]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan", passive_deletes=True
    )
    sections: Mapped[list[ResumeSection]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan", passive_deletes=True,
        order_by="ResumeSection.display_order",
    )
    statement_findings: Mapped[list[StatementFinding]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan", passive_deletes=True
    )
    recommendations: Mapped[list[Recommendation]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan", passive_deletes=True,
        order_by="Recommendation.display_order",
    )


class JobDescription(Base):
    __tablename__ = "job_descriptions"

    id: Mapped[uuid.UUID] = uuid_pk()
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        UuidType, ForeignKey("analyses.id", ondelete="CASCADE"),
        nullable=False, unique=True,
    )

    job_title: Mapped[str | None] = mapped_column(String(160), nullable=True)
    company_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    # Employer content, not the user's personal data, so stored in full.
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)

    min_years_experience: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    required_education_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    requirement_split_inferred: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    analysis: Mapped[Analysis] = relationship(back_populates="job_description")


class ScoreCategory(Base):
    __tablename__ = "score_categories"
    __table_args__ = (
        UniqueConstraint("analysis_id", "category_key", name="uq_score_category"),
        CheckConstraint("points_earned >= 0", name="ck_score_earned_non_negative"),
        CheckConstraint("points_earned <= points_possible", name="ck_score_earned_within_possible"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        UuidType, ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False, index=True
    )

    category_key: Mapped[str] = mapped_column(String(40), nullable=False)
    category_name: Mapped[str] = mapped_column(String(80), nullable=False)
    weight: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    points_earned: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    points_possible: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)

    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    # Shape differs per category and is only ever read whole, never queried by
    # its internal fields: a considered use of JSON, not a missing schema.
    evidence: Mapped[list[dict[str, Any]]] = mapped_column(JsonType, nullable=False, default=list)
    recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)
    limitation: Mapped[str] = mapped_column(Text, nullable=False)
    display_order: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)

    analysis: Mapped[Analysis] = relationship(back_populates="score_categories")


class SkillMatch(Base):
    __tablename__ = "skill_matches"
    __table_args__ = (
        UniqueConstraint("analysis_id", "skill_name", name="uq_skill_match"),
        Index("ix_skill_matches_status", "analysis_id", "match_status"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        UuidType, ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False, index=True
    )

    skill_name: Mapped[str] = mapped_column(String(80), nullable=False)
    match_status: Mapped[str] = mapped_column(String(12), nullable=False)  # matched|partial|missing
    requirement_level: Mapped[str] = mapped_column(String(12), nullable=False)  # required|preferred
    matched_via: Mapped[str | None] = mapped_column(String(16), nullable=True)  # exact|alias|related
    # The only resume-derived text stored outside the opt-in field. Capped,
    # and present because a match the user cannot verify is not credible.
    evidence_snippet: Mapped[str | None] = mapped_column(String(240), nullable=True)

    analysis: Mapped[Analysis] = relationship(back_populates="skill_matches")


class ResumeSection(Base):
    __tablename__ = "resume_sections"
    __table_args__ = (
        UniqueConstraint("analysis_id", "section_key", name="uq_resume_section"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        UuidType, ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False, index=True
    )

    section_key: Mapped[str] = mapped_column(String(24), nullable=False)
    # Absence is recorded explicitly, so "analysed and missing" stays
    # distinguishable from "never analysed".
    detected: Mapped[bool] = mapped_column(Boolean, nullable=False)
    matched_heading: Mapped[str | None] = mapped_column(String(120), nullable=True)
    note: Mapped[str] = mapped_column(Text, nullable=False, default="")
    display_order: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)

    analysis: Mapped[Analysis] = relationship(back_populates="sections")


class StatementFinding(Base):
    __tablename__ = "statement_findings"

    id: Mapped[uuid.UUID] = uuid_pk()
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        UuidType, ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False, index=True
    )

    statement_text: Mapped[str] = mapped_column(String(600), nullable=False)
    issue_codes: Mapped[list[str]] = mapped_column(JsonType, nullable=False, default=list)
    word_count: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    has_measurable_result: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    suggestion: Mapped[str | None] = mapped_column(Text, nullable=True)

    analysis: Mapped[Analysis] = relationship(back_populates="statement_findings")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[uuid.UUID] = uuid_pk()
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        UuidType, ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False, index=True
    )

    priority: Mapped[str] = mapped_column(String(8), nullable=False)  # high|medium|low
    # Surfaced in the UI so the user always knows whether a suggestion came
    # from the rule engine or from the AI.
    source: Mapped[str] = mapped_column(String(16), nullable=False)  # rule|ai
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    detail: Mapped[str] = mapped_column(Text, nullable=False)
    display_order: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)

    analysis: Mapped[Analysis] = relationship(back_populates="recommendations")
