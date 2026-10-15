"""Bound request bodies before multipart parsing and enforce browser origins."""

from __future__ import annotations

import asyncio
import threading

from starlette.datastructures import Headers
from starlette.responses import JSONResponse

from app.core.config import settings
from app.core.error_codes import RATE_LIMITED, RESUME_TOO_LARGE, ErrorSpec
from app.core.exceptions import AppError
from app.security.rate_limit import limiter


class RequestGuard:
    def __init__(self, app):
        self.app = app
        self.slots = threading.BoundedSemaphore(4)

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        headers = Headers(scope=scope)
        mutating = scope["method"] in {"POST", "PUT", "PATCH", "DELETE"}
        if not mutating:
            return await self.app(scope, receive, send)

        async def reject(spec, retry_after=None):
            error = AppError(spec, retry_after=retry_after)
            response = JSONResponse(
                error.to_payload(scope.get("state", {}).get("request_id", "unknown")),
                status_code=spec.http_status,
                headers={
                    "Cache-Control": "no-store",
                    **({"Retry-After": str(retry_after)} if retry_after else {}),
                },
            )
            await response(scope, receive, send)

        origin = headers.get("origin")
        if (origin is not None and origin not in settings.cors_origin_list) or (
            settings.is_production and origin is None
        ):
            return await reject(
                ErrorSpec(
                    "ORIGIN_REJECTED",
                    403,
                    "This request origin is not allowed.",
                    "Session-changing requests must come from the configured website.",
                    "Open ResumeIQ from its configured website and retry.",
                )
            )

        # Global anonymous ceiling prevents varying email/IP keys from bypassing
        # compute protection. All quotas are process-local and reset at restart.
        retry = limiter.consume("global:mutations", 120, 60)
        if retry is not None:
            return await reject(RATE_LIMITED, retry)
        if not self.slots.acquire(blocking=False):
            return await reject(RATE_LIMITED, 5)
        try:
            limit = (
                settings.max_upload_bytes + 64 * 1024
                if scope["path"] == "/api/v1/analyses"
                else 32 * 1024
            )
            length = headers.get("content-length")
            if length and (not length.isdigit() or int(length) > limit):
                return await reject(RESUME_TOO_LARGE)
            body = bytearray()
            try:
                async with asyncio.timeout(20):
                    while True:
                        message = await receive()
                        if message["type"] == "http.disconnect":
                            return
                        body.extend(message.get("body", b""))
                        if len(body) > limit:
                            return await reject(RESUME_TOO_LARGE)
                        if not message.get("more_body", False):
                            break
            except TimeoutError:
                return await reject(
                    ErrorSpec(
                        "UPLOAD_TIMEOUT",
                        408,
                        "The upload took too long.",
                        "The connection may be slow or interrupted.",
                        "Try a smaller PDF and retry.",
                    )
                )
            delivered = False

            async def bounded_receive():
                nonlocal delivered
                if not delivered:
                    delivered = True
                    return {"type": "http.request", "body": bytes(body), "more_body": False}
                return await receive()

            await self.app(scope, bounded_receive, send)
        finally:
            self.slots.release()
