"""Password hashing.

bcrypt is used directly rather than through passlib: passlib 1.7.x imports the
stdlib `crypt` module, which was removed in Python 3.13.
"""

from __future__ import annotations

import bcrypt

from app.core.config import settings

# bcrypt truncates silently at 72 bytes. Rejecting longer input is clearer than
# accepting a password whose tail is ignored.
MAX_PASSWORD_BYTES = 72

# Used to keep the timing of an unknown-email login comparable to a real one,
# so response time does not reveal whether an account exists.
_DUMMY_HASH = bcrypt.hashpw(b"resumeiq-timing-equalisation", bcrypt.gensalt(rounds=12)).decode()


def hash_password(plain_password: str) -> str:
    encoded = plain_password.encode("utf-8")
    if len(encoded) > MAX_PASSWORD_BYTES:
        raise ValueError("Password must be at most 72 UTF-8 bytes")
    salt = bcrypt.gensalt(rounds=settings.bcrypt_rounds)
    return bcrypt.hashpw(encoded, salt).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        if len(plain_password.encode("utf-8")) > MAX_PASSWORD_BYTES:
            return False
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            password_hash.encode("utf-8"),
        )
    except (ValueError, TypeError):
        # A malformed stored hash must fail closed, not raise.
        return False


def waste_time_like_a_real_verification() -> None:
    """Run a bcrypt comparison against a dummy hash.

    Called on the unknown-email login path so that "no such user" and "wrong
    password" take a comparable amount of time.
    """
    bcrypt.checkpw(b"resumeiq-timing-equalisation", _DUMMY_HASH.encode())
