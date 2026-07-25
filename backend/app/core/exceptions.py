"""One exception type for every error the user can see."""

from __future__ import annotations

from typing import Any

from app.core.error_codes import ErrorSpec


class AppError(Exception):
    """An error with a stable code and a three-part, user-safe message.

    Anything raised as an AppError is safe to send to the client verbatim.
    Anything else is converted to INTERNAL_ERROR by the global handler.
    """

    def __init__(
        self,
        spec: ErrorSpec,
        *,
        fields: dict[str, str] | None = None,
        retry_after: int | None = None,
    ) -> None:
        super().__init__(f"{spec.code}: {spec.what}")
        self.spec = spec
        self.fields = fields or {}
        self.retry_after = retry_after

    @property
    def code(self) -> str:
        return self.spec.code

    @property
    def http_status(self) -> int:
        return self.spec.http_status

    def to_payload(self, request_id: str) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "code": self.spec.code,
            "what": self.spec.what,
            "why": self.spec.why,
            "next_step": self.spec.next_step,
            "request_id": request_id,
        }
        if self.fields:
            payload["fields"] = self.fields
        return {"error": payload}


class ExtractionError(AppError):
    """Raised by the PDF extractor. Carries its own specific error code."""
