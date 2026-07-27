"""Store whole-resume statement statistics on the analysis

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-27

statement_findings holds only the flagged subset of a resume's bullets. A
well-written statement carrying a measurable result is never flagged, so
deriving the totals from that table reported zero achievements for a strong
resume while the score said otherwise. The true counts are now stored on the
analysis row alongside the score they produced.
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # server_default backfills existing rows; the ORM supplies the value on
    # every new insert.
    op.add_column(
        "analyses",
        sa.Column("statements_total", sa.SmallInteger(), nullable=False, server_default="0"),
    )
    op.add_column(
        "analyses",
        sa.Column("statements_with_metric", sa.SmallInteger(), nullable=False, server_default="0"),
    )
    op.add_column(
        "analyses",
        sa.Column(
            "statements_action_verb_rate",
            sa.Numeric(5, 4),
            nullable=False,
            server_default="0",
        ),
    )


def downgrade() -> None:
    op.drop_column("analyses", "statements_action_verb_rate")
    op.drop_column("analyses", "statements_with_metric")
    op.drop_column("analyses", "statements_total")
