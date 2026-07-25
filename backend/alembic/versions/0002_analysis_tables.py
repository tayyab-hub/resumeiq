"""Analyses and their child tables

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-25
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# JSONB on PostgreSQL, plain JSON elsewhere.
JSON_TYPE = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    op.create_table(
        "analyses",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        # A sanitised display label. There is no column here, or anywhere in
        # this schema, capable of holding the uploaded PDF.
        sa.Column("resume_filename", sa.String(length=255), nullable=False),
        sa.Column("overall_score", sa.SmallInteger(), nullable=False),
        sa.Column("store_resume_text", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("resume_text", sa.Text(), nullable=True),
        sa.Column("ai_status", sa.String(length=20), nullable=False, server_default="unavailable"),
        sa.Column("ai_reason_code", sa.String(length=40), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.CheckConstraint(
            "overall_score >= 0 AND overall_score <= 100", name="ck_analyses_score_range"
        ),
        # The privacy guarantee is enforced by the schema, not only by code.
        sa.CheckConstraint(
            "store_resume_text OR resume_text IS NULL", name="ck_analyses_resume_text_optin"
        ),
    )
    op.create_index("ix_analyses_user_id", "analyses", ["user_id"])
    # Serves both the history list and the dashboard trend chart.
    op.create_index("ix_analyses_user_created", "analyses", ["user_id", "created_at"])

    op.create_table(
        "job_descriptions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("analysis_id", sa.Uuid(), nullable=False),
        sa.Column("job_title", sa.String(length=160), nullable=True),
        sa.Column("company_name", sa.String(length=160), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("min_years_experience", sa.SmallInteger(), nullable=True),
        sa.Column("required_education_level", sa.String(length=20), nullable=True),
        sa.Column(
            "requirement_split_inferred", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["analysis_id"], ["analyses.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("analysis_id", name="uq_job_description_analysis"),
        sa.CheckConstraint("min_years_experience >= 0", name="ck_job_years_non_negative"),
    )

    op.create_table(
        "score_categories",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("analysis_id", sa.Uuid(), nullable=False),
        sa.Column("category_key", sa.String(length=40), nullable=False),
        sa.Column("category_name", sa.String(length=80), nullable=False),
        sa.Column("weight", sa.Numeric(5, 2), nullable=False),
        sa.Column("points_earned", sa.Numeric(5, 2), nullable=False),
        sa.Column("points_possible", sa.Numeric(5, 2), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("evidence", JSON_TYPE, nullable=False),
        sa.Column("recommendation", sa.Text(), nullable=True),
        sa.Column("limitation", sa.Text(), nullable=False),
        sa.Column("display_order", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["analysis_id"], ["analyses.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("analysis_id", "category_key", name="uq_score_category"),
        sa.CheckConstraint("points_earned >= 0", name="ck_score_earned_non_negative"),
        sa.CheckConstraint(
            "points_earned <= points_possible", name="ck_score_earned_within_possible"
        ),
    )
    op.create_index("ix_score_categories_analysis_id", "score_categories", ["analysis_id"])

    op.create_table(
        "skill_matches",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("analysis_id", sa.Uuid(), nullable=False),
        sa.Column("skill_name", sa.String(length=80), nullable=False),
        sa.Column("match_status", sa.String(length=12), nullable=False),
        sa.Column("requirement_level", sa.String(length=12), nullable=False),
        sa.Column("matched_via", sa.String(length=16), nullable=True),
        sa.Column("evidence_snippet", sa.String(length=240), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["analysis_id"], ["analyses.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("analysis_id", "skill_name", name="uq_skill_match"),
    )
    op.create_index("ix_skill_matches_analysis_id", "skill_matches", ["analysis_id"])
    # Powers the dashboard's "most common missing skills" aggregate.
    op.create_index("ix_skill_matches_status", "skill_matches", ["analysis_id", "match_status"])

    op.create_table(
        "resume_sections",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("analysis_id", sa.Uuid(), nullable=False),
        sa.Column("section_key", sa.String(length=24), nullable=False),
        sa.Column("detected", sa.Boolean(), nullable=False),
        sa.Column("matched_heading", sa.String(length=120), nullable=True),
        sa.Column("note", sa.Text(), nullable=False, server_default=""),
        sa.Column("display_order", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["analysis_id"], ["analyses.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("analysis_id", "section_key", name="uq_resume_section"),
    )
    op.create_index("ix_resume_sections_analysis_id", "resume_sections", ["analysis_id"])

    op.create_table(
        "statement_findings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("analysis_id", sa.Uuid(), nullable=False),
        sa.Column("statement_text", sa.String(length=600), nullable=False),
        sa.Column("issue_codes", JSON_TYPE, nullable=False),
        sa.Column("word_count", sa.SmallInteger(), nullable=False),
        sa.Column(
            "has_measurable_result", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column("suggestion", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["analysis_id"], ["analyses.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_statement_findings_analysis_id", "statement_findings", ["analysis_id"])

    op.create_table(
        "recommendations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("analysis_id", sa.Uuid(), nullable=False),
        sa.Column("priority", sa.String(length=8), nullable=False),
        # Surfaced in the UI so the user always knows whether a suggestion came
        # from the rule engine or from the AI.
        sa.Column("source", sa.String(length=16), nullable=False),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("detail", sa.Text(), nullable=False),
        sa.Column("display_order", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["analysis_id"], ["analyses.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_recommendations_analysis_id", "recommendations", ["analysis_id"])


def downgrade() -> None:
    op.drop_table("recommendations")
    op.drop_table("statement_findings")
    op.drop_table("resume_sections")
    op.drop_table("skill_matches")
    op.drop_table("score_categories")
    op.drop_table("job_descriptions")
    op.drop_index("ix_analyses_user_created", table_name="analyses")
    op.drop_index("ix_analyses_user_id", table_name="analyses")
    op.drop_table("analyses")
