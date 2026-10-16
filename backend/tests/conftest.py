"""Shared test fixtures.

Integration tests run against a real database created from the SQLAlchemy
metadata. SQLite is used so the suite needs no database server; the models were
written with portable column types for exactly this reason. The production
target remains PostgreSQL, and the migrations are written against it.
"""

from __future__ import annotations

import os
import uuid
from collections.abc import Iterator

import pytest

# Must be set before app.core.config is imported anywhere.
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEBUG", "false")
os.environ.setdefault("JWT_SECRET", "test-secret-key-that-is-definitely-long-enough-here")
os.environ["AI_API_KEY"] = ""
os.environ["AI_ENABLED_OPT_IN"] = "false"
os.environ.setdefault("BCRYPT_ROUNDS", "4")  # keeps the suite fast; production uses 12

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.database.base import Base  # noqa: E402
from app.database.session import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import *  # noqa: E402,F403  - registers every table on the metadata
from app.security.rate_limit import limiter  # noqa: E402


@pytest.fixture()
def db_engine():
    test_url = os.environ.get("TEST_DATABASE_URL")
    if test_url:
        from alembic.config import Config
        from sqlalchemy.engine import make_url

        from alembic import command

        url = make_url(test_url)
        if url.host not in {"localhost", "127.0.0.1", "postgres"} or not (
            url.database or ""
        ).endswith("_test"):
            raise RuntimeError("TEST_DATABASE_URL must name a local disposable *_test database")
        schema = "resumeiq_test_" + uuid.uuid4().hex
        admin = create_engine(test_url)
        with admin.begin() as conn:
            conn.execute(text(f'CREATE SCHEMA "{schema}"'))
        engine = create_engine(test_url, connect_args={"options": f"-csearch_path={schema}"})
        try:
            with engine.begin() as conn:
                config = Config("alembic.ini")
                config.attributes["connection"] = conn
                command.upgrade(config, "head")
            yield engine
        finally:
            engine.dispose()
            # Only this test's UUID schema is removed, never public or production.
            with admin.begin() as conn:
                conn.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
            admin.dispose()
        return
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    from sqlalchemy import event

    @event.listens_for(engine, "connect")
    def _fk_on(dbapi_connection, _record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture()
def db_session(db_engine) -> Iterator:
    factory = sessionmaker(bind=db_engine, autoflush=False, expire_on_commit=False)
    session = factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_engine) -> Iterator[TestClient]:
    factory = sessionmaker(bind=db_engine, autoflush=False, expire_on_commit=False)

    def override_get_db():
        session = factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    limiter.clear()  # rate-limit counters are process-global
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    limiter.clear()


@pytest.fixture()
def client_swallowing_errors(db_engine) -> Iterator[TestClient]:
    """A client that lets the global exception handler produce its response.

    TestClient re-raises server exceptions by default, which is useful for most
    tests but hides the very thing the error-leakage test needs to inspect.
    """
    factory = sessionmaker(bind=db_engine, autoflush=False, expire_on_commit=False)

    def override_get_db():
        session = factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    limiter.clear()
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    limiter.clear()


def register_user(
    client: TestClient, email: str | None = None, password: str = "correct horse 7"
) -> dict:
    """Register a user and return {token, email, password, user}."""
    email = email or f"user-{uuid.uuid4().hex[:8]}@example.com"
    response = client.post(
        "/api/v1/auth/register",
        json={"full_name": "Test Person", "email": email, "password": password},
    )
    assert response.status_code == 201, response.text
    body = response.json()
    return {
        "token": body["access_token"],
        "email": email,
        "password": password,
        "user": body["user"],
        "headers": {"Authorization": f"Bearer {body['access_token']}"},
    }


@pytest.fixture()
def user_a(client: TestClient) -> dict:
    return register_user(client, "alice@example.com")


@pytest.fixture()
def user_b(client: TestClient) -> dict:
    return register_user(client, "bob@example.com")
