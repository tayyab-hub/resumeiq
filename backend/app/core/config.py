"""Application settings, loaded once from the environment."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_INSECURE_JWT_DEFAULT = "change-me-to-a-long-random-value-at-least-32-characters"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "ResumeIQ API"
    version: str = "1.0.0"
    environment: Literal["development", "production", "test"] = "development"
    debug: bool = True

    database_url: str = "sqlite+pysqlite:///./resumeiq.db"

    jwt_secret: str = _INSECURE_JWT_DEFAULT
    jwt_algorithm: str = "HS256"
    access_token_ttl_minutes: int = 30
    refresh_token_ttl_days: int = 7
    bcrypt_rounds: int = 12

    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    max_upload_bytes: int = 5 * 1024 * 1024
    min_extracted_chars: int = 200
    min_job_description_chars: int = 200
    max_job_description_chars: int = 8000

    login_max_attempts: int = 5
    login_window_seconds: int = 900
    register_max_per_hour: int = 10
    analyses_per_day: int = 20
    ai_calls_per_day: int = 20

    ai_api_key: str = ""
    ai_model: str = "claude-opus-5"
    ai_timeout_seconds: float = 20.0
    ai_max_tokens: int = 8000
    ai_effort: Literal["low", "medium", "high", "xhigh", "max"] = "medium"

    @field_validator("jwt_secret")
    @classmethod
    def _reject_short_secret(cls, value: str) -> str:
        if len(value) < 32:
            raise ValueError("JWT_SECRET must be at least 32 characters long")
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def ai_enabled(self) -> bool:
        return bool(self.ai_api_key.strip())

    def assert_production_ready(self) -> None:
        """Fail fast rather than serve production traffic with a known-bad secret."""
        if self.is_production and self.jwt_secret == _INSECURE_JWT_DEFAULT:
            raise RuntimeError(
                "JWT_SECRET is still the example value. Set a real secret before deploying."
            )
        if self.is_production and self.debug:
            raise RuntimeError("DEBUG must be false in production.")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
