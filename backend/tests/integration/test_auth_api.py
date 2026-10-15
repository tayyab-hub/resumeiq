"""Authentication endpoint tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import settings
from app.models.user import User

VALID = {"full_name": "Ada Lovelace", "email": "ada@example.com", "password": "analytical2026"}


class TestRegistration:
    def test_creates_an_account(self, client: TestClient):
        response = client.post("/api/v1/auth/register", json=VALID)
        assert response.status_code == 201
        body = response.json()
        assert body["user"]["email"] == "ada@example.com"
        assert body["access_token"]

    def test_response_never_contains_a_password_field(self, client: TestClient):
        response = client.post("/api/v1/auth/register", json=VALID)
        assert "password" not in response.text.lower().replace("password must", "")
        assert "password_hash" not in response.text

    def test_password_is_hashed_in_the_database(self, client: TestClient, db_session):
        client.post("/api/v1/auth/register", json=VALID)
        user = db_session.execute(select(User).where(User.email == "ada@example.com")).scalar_one()
        assert user.password_hash != VALID["password"]
        assert VALID["password"] not in user.password_hash
        assert user.password_hash.startswith("$2")

    def test_duplicate_email_is_rejected_without_confirming_the_account(self, client: TestClient):
        client.post("/api/v1/auth/register", json=VALID)
        response = client.post("/api/v1/auth/register", json=VALID)
        assert response.status_code == 409
        assert response.json()["error"]["code"] == "EMAIL_UNAVAILABLE"
        assert "already" not in response.json()["error"]["what"].lower()

    def test_email_is_normalised_so_case_does_not_create_a_second_account(self, client: TestClient):
        client.post("/api/v1/auth/register", json={**VALID, "email": "Ada@Example.COM"})
        login = client.post(
            "/api/v1/auth/login", json={"email": "ada@example.com", "password": VALID["password"]}
        )
        assert login.status_code == 200

    @pytest.mark.parametrize(
        ("password", "reason"),
        [("short1", "too short"), ("nodigitshere", "no digit"), ("1234567890", "no letter")],
    )
    def test_server_enforces_the_password_rules(self, client: TestClient, password, reason):
        response = client.post("/api/v1/auth/register", json={**VALID, "password": password})
        assert response.status_code == 422, reason
        assert response.json()["error"]["code"] == "VALIDATION_ERROR"
        assert "password" in response.json()["error"]["fields"]

    def test_validation_errors_name_the_field(self, client: TestClient):
        response = client.post("/api/v1/auth/register", json={**VALID, "email": "not-an-email"})
        assert response.status_code == 422
        assert "email" in response.json()["error"]["fields"]

    def test_every_error_carries_the_three_part_message(self, client: TestClient):
        response = client.post("/api/v1/auth/register", json={**VALID, "password": "x"})
        error = response.json()["error"]
        assert error["what"] and error["why"] and error["next_step"]
        assert error["request_id"]


class TestLogin:
    def test_valid_credentials_return_a_token_and_set_the_refresh_cookie(self, client: TestClient):
        client.post("/api/v1/auth/register", json=VALID)
        response = client.post(
            "/api/v1/auth/login", json={"email": VALID["email"], "password": VALID["password"]}
        )
        assert response.status_code == 200
        assert response.json()["access_token"]
        assert "resumeiq_refresh" in response.cookies

    def test_refresh_cookie_is_http_only(self, client: TestClient):
        client.post("/api/v1/auth/register", json=VALID)
        response = client.post(
            "/api/v1/auth/login", json={"email": VALID["email"], "password": VALID["password"]}
        )
        cookie_header = response.headers.get("set-cookie", "")
        assert "httponly" in cookie_header.lower()

    def test_unknown_email_and_wrong_password_are_indistinguishable(self, client: TestClient):
        client.post("/api/v1/auth/register", json=VALID)
        wrong_password = client.post(
            "/api/v1/auth/login", json={"email": VALID["email"], "password": "wrong password 9"}
        )
        unknown_email = client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@example.com", "password": "wrong password 9"},
        )
        assert wrong_password.status_code == unknown_email.status_code == 401
        assert wrong_password.json()["error"]["code"] == unknown_email.json()["error"]["code"]
        assert wrong_password.json()["error"]["what"] == unknown_email.json()["error"]["what"]


class TestProtectedRoutes:
    def test_me_returns_the_profile(self, client: TestClient, user_a):
        response = client.get("/api/v1/auth/me", headers=user_a["headers"])
        assert response.status_code == 200
        assert response.json()["email"] == "alice@example.com"

    def test_me_requires_a_token(self, client: TestClient):
        assert client.get("/api/v1/auth/me").status_code == 401

    def test_expired_token_reports_its_own_code(self, client: TestClient, user_a):
        payload = {
            "sub": user_a["user"]["id"],
            "type": "access",
            "exp": int((datetime.now(UTC) - timedelta(minutes=1)).timestamp()),
        }
        expired = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
        response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired}"})
        assert response.status_code == 401
        # A distinct code lets the client refresh rather than log the user out.
        assert response.json()["error"]["code"] == "TOKEN_EXPIRED"

    def test_forged_token_is_rejected(self, client: TestClient, user_a):
        payload = {
            "sub": user_a["user"]["id"],
            "type": "access",
            "exp": int((datetime.now(UTC) + timedelta(minutes=30)).timestamp()),
        }
        forged = jwt.encode(payload, "attacker-secret-that-is-long-enough-x", algorithm="HS256")
        response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {forged}"})
        assert response.status_code == 401

    def test_token_for_a_deleted_account_is_rejected(self, client: TestClient, user_a, db_session):
        user = db_session.execute(
            select(User).where(User.email == "alice@example.com")
        ).scalar_one()
        db_session.delete(user)
        db_session.commit()
        response = client.get("/api/v1/auth/me", headers=user_a["headers"])
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "TOKEN_INVALID"

    def test_malformed_authorization_header_is_rejected(self, client: TestClient):
        for header in (
            {"Authorization": "Basic abc"},
            {"Authorization": "Bearer"},
            {"Authorization": ""},
        ):
            assert client.get("/api/v1/auth/me", headers=header).status_code == 401


class TestSessionLifecycle:
    def test_refresh_issues_a_new_access_token(self, client: TestClient):
        client.post("/api/v1/auth/register", json=VALID)
        response = client.post("/api/v1/auth/refresh")
        assert response.status_code == 200
        assert response.json()["access_token"]

    def test_refresh_without_a_cookie_fails(self, client: TestClient):
        response = client.post("/api/v1/auth/refresh")
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "REFRESH_INVALID"

    def test_logout_revokes_the_refresh_token(self, client: TestClient):
        client.post("/api/v1/auth/register", json=VALID)
        assert client.post("/api/v1/auth/logout").status_code == 204
        assert client.post("/api/v1/auth/refresh").status_code == 401

    def test_refresh_rotates_the_token(self, client: TestClient):
        client.post("/api/v1/auth/register", json=VALID)
        first = client.cookies.get("resumeiq_refresh")
        client.post("/api/v1/auth/refresh")
        assert client.cookies.get("resumeiq_refresh") != first


class TestRateLimiting:
    def test_repeated_failures_are_throttled(self, client: TestClient):
        client.post("/api/v1/auth/register", json=VALID)
        payload = {"email": VALID["email"], "password": "definitely wrong 1"}

        for _ in range(settings.login_max_attempts):
            assert client.post("/api/v1/auth/login", json=payload).status_code == 401

        blocked = client.post("/api/v1/auth/login", json=payload)
        assert blocked.status_code == 429
        assert blocked.json()["error"]["code"] == "TOO_MANY_ATTEMPTS"
        assert blocked.headers.get("Retry-After")

    def test_successful_login_does_not_reset_abuse_budget(self, client: TestClient):
        client.post("/api/v1/auth/register", json=VALID)
        for _ in range(settings.login_max_attempts - 1):
            client.post(
                "/api/v1/auth/login", json={"email": VALID["email"], "password": "nope 12345"}
            )

        good = client.post(
            "/api/v1/auth/login", json={"email": VALID["email"], "password": VALID["password"]}
        )
        assert good.status_code == 200
        again = client.post(
            "/api/v1/auth/login", json={"email": VALID["email"], "password": "nope 12345"}
        )
        assert again.status_code == 429  # success cannot reset the shared abuse budget


class TestAccountManagement:
    def test_update_profile(self, client: TestClient, user_a):
        response = client.patch(
            "/api/v1/users/me", json={"full_name": "Alice Smith"}, headers=user_a["headers"]
        )
        assert response.status_code == 200
        assert response.json()["full_name"] == "Alice Smith"

    def test_change_password_requires_the_current_one(self, client: TestClient, user_a):
        response = client.post(
            "/api/v1/users/me/password",
            json={"current_password": "wrong password 1", "new_password": "brand new pass 9"},
            headers=user_a["headers"],
        )
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "PASSWORD_INCORRECT"

    def test_change_password_works_and_ends_sessions(self, client: TestClient, user_a):
        response = client.post(
            "/api/v1/users/me/password",
            json={"current_password": user_a["password"], "new_password": "brand new pass 9"},
            headers=user_a["headers"],
        )
        assert response.status_code == 204
        assert client.post("/api/v1/auth/refresh").status_code == 401

        login = client.post(
            "/api/v1/auth/login",
            json={"email": user_a["email"], "password": "brand new pass 9"},
        )
        assert login.status_code == 200

    def test_delete_account_requires_confirmation(self, client: TestClient, user_a):
        response = client.request(
            "DELETE",
            "/api/v1/users/me",
            json={"password": user_a["password"], "confirmation": "yes"},
            headers=user_a["headers"],
        )
        assert response.status_code == 422

    def test_delete_account_removes_the_user(self, client: TestClient, user_a, db_session):
        response = client.request(
            "DELETE",
            "/api/v1/users/me",
            json={"password": user_a["password"], "confirmation": "DELETE"},
            headers=user_a["headers"],
        )
        assert response.status_code == 204
        remaining = db_session.execute(
            select(User).where(User.email == "alice@example.com")
        ).scalar_one_or_none()
        assert remaining is None


class TestResponseHeaders:
    def test_security_headers_are_present(self, client: TestClient):
        response = client.get("/api/v1/health")
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["Referrer-Policy"] == "no-referrer"
        assert response.headers["X-Request-ID"]

    def test_health_reports_the_database(self, client: TestClient):
        body = client.get("/api/v1/health").json()
        assert body["status"] == "ok"
        assert body["database"] == "ok"

    def test_a_disallowed_origin_gets_no_allow_header(self, client: TestClient):
        response = client.get("/api/v1/health", headers={"Origin": "https://evil.example"})
        assert "access-control-allow-origin" not in {k.lower() for k in response.headers}

    def test_an_allowed_origin_is_accepted(self, client: TestClient):
        response = client.get("/api/v1/health", headers={"Origin": "http://localhost:5173"})
        assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
