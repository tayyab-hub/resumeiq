"""JWT access tokens and opaque refresh tokens."""

from __future__ import annotations

import hashlib
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import jwt

from app.core.config import settings
from app.core.error_codes import TOKEN_EXPIRED, TOKEN_INVALID
from app.core.exceptions import AppError


@dataclass(frozen=True)
class AccessTokenClaims:
    user_id: uuid.UUID
    expires_at: datetime


def create_access_token(user_id: uuid.UUID) -> tuple[str, int]:
    """Return (token, seconds_until_expiry)."""
    ttl = timedelta(minutes=settings.access_token_ttl_minutes)
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "iat": int(now.timestamp()),
        "exp": int((now + ttl).timestamp()),
        "type": "access",
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return token, int(ttl.total_seconds())


def decode_access_token(token: str) -> AccessTokenClaims:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            # Pinning the algorithm list is what makes an `alg: none` token fail.
            algorithms=[settings.jwt_algorithm],
            options={"require": ["exp", "sub"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise AppError(TOKEN_EXPIRED) from exc
    except jwt.InvalidTokenError as exc:
        raise AppError(TOKEN_INVALID) from exc

    if payload.get("type") != "access":
        raise AppError(TOKEN_INVALID)

    try:
        user_id = uuid.UUID(str(payload["sub"]))
    except (ValueError, KeyError) as exc:
        raise AppError(TOKEN_INVALID) from exc

    return AccessTokenClaims(
        user_id=user_id,
        expires_at=datetime.fromtimestamp(payload["exp"], tz=UTC),
    )


def create_refresh_token() -> tuple[str, str, datetime]:
    """Return (raw_token, sha256_hash, expires_at).

    The raw value goes to the client in an httpOnly cookie; only the hash is
    stored, so a database dump yields no usable sessions.
    """
    raw = secrets.token_urlsafe(48)
    expires_at = datetime.now(UTC) + timedelta(days=settings.refresh_token_ttl_days)
    return raw, hash_refresh_token(raw), expires_at


def hash_refresh_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
