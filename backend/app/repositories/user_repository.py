"""User and refresh-token database access."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from app.models.user import RefreshToken, User


def normalise_email(email: str) -> str:
    """Lower-cased and trimmed, so uniqueness is effectively case-insensitive
    on every database engine."""
    return email.strip().lower()


def get_by_email(db: Session, email: str) -> User | None:
    return db.execute(select(User).where(User.email == normalise_email(email))).scalar_one_or_none()


def get_by_id(db: Session, user_id: uuid.UUID) -> User | None:
    return db.get(User, user_id)


def create(db: Session, *, email: str, full_name: str, password_hash: str) -> User:
    user = User(
        email=normalise_email(email),
        full_name=full_name.strip(),
        password_hash=password_hash,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user: User) -> None:
    """Hard delete. Cascades remove every analysis and refresh token."""
    db.delete(user)
    db.commit()


def store_refresh_token(
    db: Session, *, user_id: uuid.UUID, token_hash: str, expires_at: datetime
) -> RefreshToken:
    token = RefreshToken(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
    db.add(token)
    db.commit()
    return token


def find_active_refresh_token(db: Session, token_hash: str) -> RefreshToken | None:
    token = db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    ).scalar_one_or_none()
    if token is None or token.revoked_at is not None:
        return None
    expires = token.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=UTC)
    if expires <= datetime.now(UTC):
        return None
    return token


def consume_refresh_token(db: Session, token_hash: str) -> uuid.UUID | None:
    """Exactly one concurrent redemption can revoke and return this token."""
    owner_id = db.scalar(select(RefreshToken.user_id).where(RefreshToken.token_hash == token_hash))
    if owner_id is None:
        return None
    # Password changes and token issuance share this user-row lock.
    db.execute(select(User).where(User.id == owner_id).with_for_update())
    now = datetime.now(UTC)
    user_id = db.execute(
        update(RefreshToken)
        .where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > now,
        )
        .values(revoked_at=now)
        .returning(RefreshToken.user_id)
    ).scalar_one_or_none()
    return user_id


def revoke_refresh_token(db: Session, token_hash: str) -> None:
    token = db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    ).scalar_one_or_none()
    if token is not None and token.revoked_at is None:
        token.revoked_at = datetime.now(UTC)
        db.commit()


def revoke_all_for_user(db: Session, user_id: uuid.UUID) -> None:
    """Used after a password change: every existing session must end."""
    now = datetime.now(UTC)
    tokens = (
        db.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None)
            )
        )
        .scalars()
        .all()
    )
    for token in tokens:
        token.revoked_at = now
    db.commit()


def prune_expired_tokens(db: Session, user_id: uuid.UUID) -> None:
    db.execute(
        delete(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.expires_at < datetime.now(UTC),
        )
    )
    # Committed together with the replacement token by store_refresh_token.
