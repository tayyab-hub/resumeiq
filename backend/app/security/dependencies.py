"""FastAPI dependencies for the authenticated user."""

from __future__ import annotations

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.error_codes import TOKEN_INVALID, TOKEN_MISSING
from app.core.exceptions import AppError
from app.database.session import get_db
from app.models.user import User
from app.security.tokens import decode_access_token


def _bearer_token(request: Request) -> str:
    header = request.headers.get("Authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise AppError(TOKEN_MISSING)
    return token.strip()


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    claims = decode_access_token(_bearer_token(request))
    user = db.get(User, claims.user_id)
    # A token for a deleted or deactivated account must fail, not merely expire.
    if user is None or not user.is_active:
        raise AppError(TOKEN_INVALID)
    return user


def client_ip(request: Request) -> str:
    """Best-effort client address for rate limiting.

    Behind Render's proxy the real address is the first X-Forwarded-For entry.
    This is a rate-limit key, never an authorisation input, so a spoofed header
    can only cost the spoofer their own quota.
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
