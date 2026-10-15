"""Add session invalidation and optional analysis retry identifiers.

Revision ID: 0004
Revises: 0003
"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("session_version", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("analyses", sa.Column("request_key", sa.String(36), nullable=True))
    with op.batch_alter_table("analyses") as batch:
        batch.create_unique_constraint("uq_analysis_request", ["user_id", "request_key"])


def downgrade():
    with op.batch_alter_table("analyses") as batch:
        batch.drop_constraint("uq_analysis_request", type_="unique")
        batch.drop_column("request_key")
    op.drop_column("users", "session_version")
