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
    if user is None or not user.is_active or user.session_version != claims.session_version:
        raise AppError(TOKEN_INVALID)
    return user


def client_ip(request: Request) -> str:
    """Use the transport peer, never arbitrary forwarded headers.

    Deploy with --no-proxy-headers until the provider's trusted proxy chain is
    verified. Proxy users then share a conservative quota; email/account and
    global quotas remain effective even when the real client IP is unavailable.
    """
    return request.client.host if request.client else "unknown"
