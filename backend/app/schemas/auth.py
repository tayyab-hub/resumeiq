"""Request and response models for authentication.

Password rules are enforced here, on the server. The identical Zod rules in the
frontend are user experience, not a security control.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

PASSWORD_MIN_LENGTH = 10
_HAS_LETTER = re.compile(r"[A-Za-z]")
_HAS_DIGIT = re.compile(r"\d")


def validate_password(value: str) -> str:
    if len(value.encode("utf-8")) > 72:
        raise ValueError("Password must be at most 72 UTF-8 bytes")
    if len(value) < PASSWORD_MIN_LENGTH:
        raise ValueError(f"Password must be at least {PASSWORD_MIN_LENGTH} characters long")
    if not _HAS_LETTER.search(value):
        raise ValueError("Password must contain at least one letter")
    if not _HAS_DIGIT.search(value):
        raise ValueError("Password must contain at least one number")
    return value


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(max_length=128)

    @field_validator("password")
    @classmethod
    def _password_rules(cls, value: str) -> str:
        return validate_password(value)

    @field_validator("full_name")
    @classmethod
    def _strip_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Full name is required")
        return cleaned


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(max_length=128)


class UserPublic(BaseModel):
    """The only user shape ever returned. It has no password field, so the
    hash cannot leak through this route even by mistake."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    full_name: str
    email: str
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserPublic


class UpdateProfileRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=120)

    @field_validator("full_name")
    @classmethod
    def _strip_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Full name is required")
        return cleaned


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(max_length=128)
    new_password: str = Field(max_length=128)

    @field_validator("new_password")
    @classmethod
    def _password_rules(cls, value: str) -> str:
        return validate_password(value)


class DeleteAccountRequest(BaseModel):
    password: str = Field(max_length=128)
    confirmation: str

    @field_validator("confirmation")
    @classmethod
    def _must_confirm(cls, value: str) -> str:
        if value.strip().upper() != "DELETE":
            raise ValueError("Type DELETE to confirm account removal")
        return value
