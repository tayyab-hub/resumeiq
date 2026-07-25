"""Registration, login, and session lifecycle."""

from __future__ import annotations

import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.error_codes import (
    EMAIL_UNAVAILABLE,
    INVALID_CREDENTIALS,
    PASSWORD_INCORRECT,
    REFRESH_INVALID,
)
from app.core.exceptions import AppError
from app.models.user import User
from app.repositories import user_repository as users
from app.security.password import (
    hash_password,
    verify_password,
    waste_time_like_a_real_verification,
)
from app.security.tokens import create_refresh_token, hash_refresh_token


def register(db: Session, *, full_name: str, email: str, password: str) -> User:
    if users.get_by_email(db, email) is not None:
        raise AppError(EMAIL_UNAVAILABLE)
    try:
        return users.create(
            db, email=email, full_name=full_name, password_hash=hash_password(password)
        )
    except IntegrityError as exc:
        # Two simultaneous registrations for the same address: the unique
        # constraint is the authority, not the check above.
        db.rollback()
        raise AppError(EMAIL_UNAVAILABLE) from exc


def authenticate(db: Session, *, email: str, password: str) -> User:
    user = users.get_by_email(db, email)
    if user is None:
        # Run a comparable bcrypt comparison so response time does not reveal
        # whether the account exists.
        waste_time_like_a_real_verification()
        raise AppError(INVALID_CREDENTIALS)
    if not user.is_active or not verify_password(password, user.password_hash):
        raise AppError(INVALID_CREDENTIALS)
    return user


def issue_refresh_token(db: Session, user_id: uuid.UUID) -> tuple[str, int]:
    """Return (raw_token, cookie_max_age_seconds)."""
    users.prune_expired_tokens(db, user_id)
    raw, digest, expires_at = create_refresh_token()
    users.store_refresh_token(db, user_id=user_id, token_hash=digest, expires_at=expires_at)
    return raw, settings.refresh_token_ttl_days * 86_400


def redeem_refresh_token(db: Session, raw_token: str | None) -> User:
    if not raw_token:
        raise AppError(REFRESH_INVALID)
    stored = users.find_active_refresh_token(db, hash_refresh_token(raw_token))
    if stored is None:
        raise AppError(REFRESH_INVALID)
    user = users.get_by_id(db, stored.user_id)
    if user is None or not user.is_active:
        raise AppError(REFRESH_INVALID)
    return user


def revoke(db: Session, raw_token: str | None) -> None:
    if raw_token:
        users.revoke_refresh_token(db, hash_refresh_token(raw_token))


def change_password(db: Session, user: User, *, current: str, new: str) -> None:
    if not verify_password(current, user.password_hash):
        raise AppError(PASSWORD_INCORRECT)
    user.password_hash = hash_password(new)
    db.commit()
    # A password change must end every existing session.
    users.revoke_all_for_user(db, user.id)


def delete_account(db: Session, user: User, *, password: str) -> None:
    if not verify_password(password, user.password_hash):
        raise AppError(PASSWORD_INCORRECT)
    users.delete_user(db, user)
