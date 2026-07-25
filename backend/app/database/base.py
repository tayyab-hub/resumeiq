"""Declarative base and the portable column types used across all models.

The schema targets PostgreSQL. These aliases keep it runnable on SQLite so the
test suite does not require a database server, while still emitting native
PostgreSQL types (UUID, JSONB) in production and in migrations.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, mapped_column

# JSONB on PostgreSQL, plain JSON elsewhere.
JsonType = JSON().with_variant(JSONB(), "postgresql")

# Native uuid on PostgreSQL, CHAR(32) elsewhere.
UuidType = Uuid(as_uuid=True)


def utcnow() -> datetime:
    """Timezone-aware default. Applied in Python rather than by the database so
    the value is identical on PostgreSQL and SQLite."""
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


def uuid_pk():
    return mapped_column(UuidType, primary_key=True, default=uuid.uuid4)


def created_at_column():
    return mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)


def updated_at_column():
    return mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )
