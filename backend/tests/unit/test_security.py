"""Password hashing, JWT handling, filename sanitisation, and rate limiting."""

from __future__ import annotations

import time
import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.core.config import settings
from app.core.error_codes import TOKEN_EXPIRED, TOKEN_INVALID
from app.core.exceptions import AppError
from app.security.password import hash_password, verify_password
from app.security.rate_limit import RateLimiter
from app.security.tokens import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    hash_refresh_token,
)
from app.utilities.files import has_pdf_extension, sanitise_filename


class TestPasswordHashing:
    def test_hash_is_not_the_plaintext(self):
        digest = hash_password("correct horse 7")
        assert digest != "correct horse 7"
        assert "correct horse 7" not in digest

    def test_hash_uses_bcrypt(self):
        assert hash_password("correct horse 7").startswith("$2")

    def test_correct_password_verifies(self):
        assert verify_password("correct horse 7", hash_password("correct horse 7"))

    def test_wrong_password_fails(self):
        assert not verify_password("wrong password 9", hash_password("correct horse 7"))

    def test_same_password_hashes_differently_each_time(self):
        # Per-password salting: two identical passwords must not share a digest.
        assert hash_password("correct horse 7") != hash_password("correct horse 7")

    def test_malformed_stored_hash_fails_closed(self):
        assert verify_password("anything", "not-a-bcrypt-hash") is False


class TestAccessTokens:
    def test_round_trip(self):
        user_id = uuid.uuid4()
        token, expires_in = create_access_token(user_id)
        assert decode_access_token(token).user_id == user_id
        assert expires_in == settings.access_token_ttl_minutes * 60

    def test_expired_token_is_rejected(self):
        payload = {
            "sub": str(uuid.uuid4()),
            "type": "access",
            "exp": int((datetime.now(UTC) - timedelta(minutes=5)).timestamp()),
        }
        expired = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
        with pytest.raises(AppError) as exc:
            decode_access_token(expired)
        assert exc.value.code == TOKEN_EXPIRED.code

    def test_token_signed_with_another_secret_is_rejected(self):
        payload = {
            "sub": str(uuid.uuid4()),
            "type": "access",
            "exp": int((datetime.now(UTC) + timedelta(minutes=5)).timestamp()),
        }
        forged = jwt.encode(payload, "an-entirely-different-secret", algorithm="HS256")
        with pytest.raises(AppError) as exc:
            decode_access_token(forged)
        assert exc.value.code == TOKEN_INVALID.code

    def test_unsigned_alg_none_token_is_rejected(self):
        """Pinning the algorithm list is what defeats this classic attack."""
        payload = {
            "sub": str(uuid.uuid4()),
            "type": "access",
            "exp": int((datetime.now(UTC) + timedelta(minutes=5)).timestamp()),
        }
        unsigned = jwt.encode(payload, key="", algorithm="none")
        with pytest.raises(AppError) as exc:
            decode_access_token(unsigned)
        assert exc.value.code == TOKEN_INVALID.code

    def test_garbage_is_rejected(self):
        with pytest.raises(AppError):
            decode_access_token("not.a.token")

    def test_a_refresh_token_cannot_be_used_as_an_access_token(self):
        payload = {
            "sub": str(uuid.uuid4()),
            "type": "refresh",
            "exp": int((datetime.now(UTC) + timedelta(minutes=5)).timestamp()),
        }
        token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
        with pytest.raises(AppError):
            decode_access_token(token)


class TestRefreshTokens:
    def test_only_the_hash_is_ever_stored(self):
        raw, digest, _ = create_refresh_token()
        assert digest != raw
        assert len(digest) == 64  # sha256 hex
        assert hash_refresh_token(raw) == digest

    def test_tokens_are_unique(self):
        assert create_refresh_token()[0] != create_refresh_token()[0]


class TestFilenameSanitisation:
    @pytest.mark.parametrize(
        ("raw", "must_not_contain"),
        [
            ("../../etc/passwd.pdf", "/"),
            ("..\\..\\windows\\system32\\config.pdf", "\\"),
            ("/absolute/path/resume.pdf", "/"),
        ],
    )
    def test_strips_every_path_component(self, raw, must_not_contain):
        cleaned = sanitise_filename(raw)
        assert must_not_contain not in cleaned
        assert ".." not in cleaned

    def test_strips_script_characters(self):
        cleaned = sanitise_filename("<script>alert(1)</script>.pdf")
        assert "<" not in cleaned and ">" not in cleaned

    def test_never_returns_an_empty_name(self):
        for raw in (None, "", "   ", "..", "."):
            assert sanitise_filename(raw)

    def test_truncates_an_absurd_name(self):
        assert len(sanitise_filename("a" * 500 + ".pdf")) <= 255

    def test_keeps_a_reasonable_name_readable(self):
        assert sanitise_filename("Jordan Reyes CV (2026).pdf") == "Jordan Reyes CV (2026).pdf"

    @pytest.mark.parametrize(
        ("name", "expected"),
        [("cv.pdf", True), ("cv.PDF", True), ("cv.docx", False), ("cv", False), (None, False)],
    )
    def test_extension_check(self, name, expected):
        assert has_pdf_extension(name) is expected


class TestRateLimiter:
    def test_allows_up_to_the_limit(self):
        limiter = RateLimiter()
        for _ in range(3):
            assert limiter.check("k", 3, 60) is None
            limiter.hit("k", 60)
        assert limiter.check("k", 3, 60) is not None

    def test_reports_a_retry_delay(self):
        limiter = RateLimiter()
        for _ in range(2):
            limiter.hit("k", 60)
        retry_after = limiter.check("k", 2, 60)
        assert retry_after is not None and 0 < retry_after <= 61

    def test_reset_clears_the_counter(self):
        limiter = RateLimiter()
        limiter.hit("k", 60)
        limiter.hit("k", 60)
        limiter.reset("k")
        assert limiter.check("k", 2, 60) is None

    def test_the_window_expires(self):
        limiter = RateLimiter()
        limiter.hit("k", 1)
        time.sleep(1.05)
        assert limiter.check("k", 1, 1) is None

    def test_keys_are_independent(self):
        limiter = RateLimiter()
        limiter.hit("a", 60)
        assert limiter.check("b", 1, 60) is None
