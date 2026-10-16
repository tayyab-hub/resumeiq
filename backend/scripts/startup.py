"""Fail-fast forward migrations and a single Uvicorn worker for Render Free."""

from __future__ import annotations

import os
import sys

from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.pool import NullPool

from alembic import command
from app.core.config import settings


def migrate() -> None:
    settings.assert_production_ready()
    url = make_url(settings.migration_database_url or settings.database_url)
    if settings.is_production:
        # Explicit identity checks prevent accidentally migrating another project.
        expected_host = os.environ.get("EXPECTED_DATABASE_HOST")
        expected_name = os.environ.get("EXPECTED_DATABASE_NAME")
        if (
            not expected_host
            or not expected_name
            or (url.host, url.database) != (expected_host, expected_name)
        ):
            raise RuntimeError("Migration database identity has not been verified.")
        if "-pooler" in (url.host or ""):
            raise RuntimeError("Use a direct Neon connection for migrations and advisory locking.")
    engine = create_engine(
        url,
        poolclass=NullPool,
        connect_args={"connect_timeout": 10} if url.get_backend_name() == "postgresql" else {},
    )
    try:
        with engine.connect() as connection:
            if connection.dialect.name == "postgresql":
                # A session lock survives migration commits. A second deployment
                # fails rather than racing; the next deploy can retry safely.
                locked = connection.scalar(text("SELECT pg_try_advisory_lock(741839201)"))
                connection.commit()
                if not locked:
                    raise RuntimeError("Another ResumeIQ migration is running.")
            tables = set(inspect(connection).get_table_names())
            if settings.is_production:
                if tables and "alembic_version" not in tables:
                    raise RuntimeError(
                        "Nonempty unversioned database: refusing automatic migration."
                    )
                if not tables and os.environ.get("ALLOW_EMPTY_DATABASE_BOOTSTRAP") != "true":
                    raise RuntimeError(
                        "Verify the empty ResumeIQ database before enabling bootstrap."
                    )
            connection.commit()
            config = Config("alembic.ini")
            config.attributes["connection"] = connection
            command.upgrade(config, "head")
            connection.commit()
    finally:
        engine.dispose()  # releases advisory lock on success and failure


def main() -> None:
    try:
        migrate()
    except Exception:
        # Connection exceptions can include credentials: never print them.
        print(
            "ResumeIQ startup stopped: verify database identity, connectivity and migration state.",
            file=sys.stderr,
        )
        raise SystemExit(1) from None
    port = int(os.environ.get("PORT", "8000"))
    os.execv(
        sys.executable,
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "0.0.0.0",
            "--port",
            str(port),
            "--workers",
            "1",
            "--no-proxy-headers",
            "--no-access-log",
            "--limit-concurrency",
            "32",
        ],
    )


if __name__ == "__main__":
    main()
