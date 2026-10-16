"""Regressions for security defects confirmed during the release audit."""

from __future__ import annotations

import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.analysis import Analysis
from app.repositories.user_repository import consume_refresh_token
from app.security.tokens import hash_refresh_token
from tests.conftest import register_user
from tests.fixtures.sample_documents import FICTIONAL_JOB_DESCRIPTION, FICTIONAL_RESUME, build_pdf


@pytest.mark.parametrize("action", ["logout", "password", "delete"])
def test_session_end_returns_cookie_expiry_header(client, action):
    user = register_user(client)
    if action == "logout":
        response = client.post("/api/v1/auth/logout")
    elif action == "password":
        response = client.post(
            "/api/v1/users/me/password",
            headers=user["headers"],
            json={
                "current_password": user["password"],
                "new_password": "new valid password 8",
            },
        )
        assert client.get("/api/v1/auth/me", headers=user["headers"]).status_code == 401
    else:
        response = client.request(
            "DELETE",
            "/api/v1/users/me",
            headers=user["headers"],
            json={
                "password": user["password"],
                "confirmation": "DELETE",
            },
        )
    assert response.status_code == 204
    cookie = response.headers["set-cookie"]
    assert "Max-Age=0" in cookie and "Path=/api/v1/auth" in cookie
    assert "HttpOnly" in cookie and "SameSite=lax" in cookie
    assert not client.cookies.get("resumeiq_refresh")


def test_cookie_secure_in_production_and_origin_required(client, monkeypatch):
    monkeypatch.setattr(settings, "environment", "production")
    assert client.post("/api/v1/auth/refresh").status_code == 403
    response = client.post(
        "/api/v1/auth/register",
        headers={"Origin": settings.cors_origin_list[0]},
        json={
            "full_name": "Fictional",
            "email": "secure@example.com",
            "password": "correct horse 7",
        },
    )
    assert response.status_code == 201
    assert "Secure" in response.headers["set-cookie"]
    assert "SameSite=lax" in response.headers["set-cookie"]


@pytest.mark.parametrize("path", ["/auth/refresh", "/auth/logout", "/auth/login", "/auth/register"])
def test_foreign_origin_rejected_before_mutation(client, path):
    response = client.post("/api/v1" + path, headers={"Origin": "https://attacker.invalid"})
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "ORIGIN_REJECTED"


def test_forwarded_headers_cannot_reset_registration_quota(client, monkeypatch):
    monkeypatch.setattr(settings, "register_max_per_hour", 1)
    payload = {"full_name": "Fictional", "email": "one@example.com", "password": "correct horse 7"}
    assert (
        client.post(
            "/api/v1/auth/register", json=payload, headers={"X-Forwarded-For": "1.1.1.1"}
        ).status_code
        == 201
    )
    payload["email"] = "two@example.com"
    assert (
        client.post(
            "/api/v1/auth/register", json=payload, headers={"X-Forwarded-For": "2.2.2.2"}
        ).status_code
        == 429
    )


@pytest.mark.parametrize("password", ["a1" + "x" * 71, "a1" + "é" * 36])
def test_oversized_password_rejected_in_utf8_bytes(client, password):
    result = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Fictional",
            "email": "long@example.com",
            "password": password,
        },
    )
    assert result.status_code == 422
    assert "72 UTF-8 bytes" in result.json()["error"]["fields"]["password"]


def test_private_responses_not_cacheable(client, user_a):
    for path in ["/api/v1/auth/me", "/api/v1/analyses", "/api/v1/analyses/" + str(uuid.uuid4())]:
        response = client.get(path, headers=user_a["headers"])
        assert response.headers["cache-control"] == "no-store"


def test_refresh_token_cannot_be_replayed(client):
    register_user(client)
    token = client.cookies.get("resumeiq_refresh")
    assert client.post("/api/v1/auth/refresh").status_code == 200
    assert (
        client.post(
            "/api/v1/auth/refresh", headers={"Cookie": f"resumeiq_refresh={token}"}
        ).status_code
        == 401
    )


def test_refresh_consumption_is_atomic_on_postgresql(client, db_engine):
    if db_engine.dialect.name != "postgresql":
        pytest.skip("Requires TEST_DATABASE_URL for independent PostgreSQL connections")
    register_user(client)
    digest = hash_refresh_token(client.cookies.get("resumeiq_refresh"))

    def redeem(_):
        with Session(db_engine) as db:
            result = consume_refresh_token(db, digest)
            db.commit()
            return result

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(redeem, range(2)))
    assert sum(result is not None for result in results) == 1


def test_retried_upload_returns_one_owned_record(client, user_a, user_b, db_session):
    key = str(uuid.uuid4())
    data = {"job_description": FICTIONAL_JOB_DESCRIPTION}
    files = {"resume": ("fictional.pdf", build_pdf(FICTIONAL_RESUME), "application/pdf")}
    headers = {**user_a["headers"], "X-Idempotency-Key": key}
    first = client.post("/api/v1/analyses", headers=headers, data=data, files=files)
    second = client.post("/api/v1/analyses", headers=headers, data=data, files=files)
    assert first.status_code == 201 and second.status_code == 200
    assert first.json()["id"] == second.json()["id"]
    assert db_session.query(Analysis).count() == 1
    other = client.post(
        "/api/v1/analyses",
        headers={**user_b["headers"], "X-Idempotency-Key": key},
        data=data,
        files=files,
    )
    assert other.status_code == 201
    assert other.json()["id"] != first.json()["id"]


def test_body_limit_rejects_before_multipart_processing(client):
    response = client.post(
        "/api/v1/analyses", content=b"small", headers={"Content-Length": "999999999"}
    )
    assert response.status_code == 413
    # Streaming clients cannot evade the limit by omitting Content-Length.
    response = client.post("/api/v1/auth/login", content=iter([b"a" * 20_000, b"b" * 20_000]))
    assert response.status_code == 413


def test_metadata_lengths_are_validated(client, user_a):
    response = client.post(
        "/api/v1/analyses",
        headers=user_a["headers"],
        data={"job_description": FICTIONAL_JOB_DESCRIPTION, "job_title": "a" * 161},
        files={"resume": ("sample.pdf", build_pdf(FICTIONAL_RESUME), "application/pdf")},
    )
    assert response.status_code == 422
