"""FastAPI application: middleware, error handling, and route registration."""

from __future__ import annotations

import time
import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.error_codes import INTERNAL_ERROR, VALIDATION_ERROR
from app.core.exceptions import AppError
from app.core.logging import configure_logging, get_logger

configure_logging(settings.debug)
logger = get_logger("resumeiq")

settings.assert_production_ready()

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    # Interactive docs are a reconnaissance aid; they are development-only.
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
    openapi_url=None if settings.is_production else "/openapi.json",
)

# Exact origins only. Never "*" while credentials are enabled — the browser
# would reject it, and reaching for the wildcard is how CORS gets broken open.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
    expose_headers=["X-Request-ID", "Retry-After"],
    max_age=600,
)


@app.middleware("http")
async def request_context(request: Request, call_next):
    """Assign a request ID, time the request, and set security headers.

    The log line deliberately carries no query string, body, or user content —
    only the route, the status, and the duration.
    """
    request_id = uuid.uuid4().hex[:16]
    request.state.request_id = request_id
    started = time.perf_counter()

    response = await call_next(request)

    duration_ms = round((time.perf_counter() - started) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    if settings.is_production:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    logger.info(
        "request",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": duration_ms,
        },
    )
    return response


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "unknown")


@app.exception_handler(AppError)
async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
    """AppError bodies are safe to return verbatim: they contain no internals."""
    headers = {"Retry-After": str(exc.retry_after)} if exc.retry_after else None
    logger.info(
        "handled_error",
        extra={"request_id": _request_id(request), "code": exc.code, "path": request.url.path},
    )
    return JSONResponse(
        status_code=exc.http_status,
        content=exc.to_payload(_request_id(request)),
        headers=headers,
    )


@app.exception_handler(RequestValidationError)
async def handle_validation_error(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Field names and rule messages only — never the submitted values."""
    fields: dict[str, str] = {}
    for error in exc.errors():
        location = [str(part) for part in error.get("loc", []) if part not in ("body", "query")]
        field = ".".join(location) or "request"
        message = error.get("msg", "Invalid value")
        fields[field] = message.removeprefix("Value error, ")

    error = AppError(VALIDATION_ERROR, fields=fields)
    return JSONResponse(
        status_code=error.http_status, content=error.to_payload(_request_id(request))
    )


@app.exception_handler(Exception)
async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    """Anything unhandled becomes a generic body plus a request ID.

    The traceback is written to the server log against that ID, so the failure
    stays traceable without exposing paths, SQL, or library internals.
    """
    request_id = _request_id(request)
    logger.exception(
        "unhandled_error",
        extra={"request_id": request_id, "path": request.url.path,
               "error_type": type(exc).__name__},
    )
    return JSONResponse(
        status_code=INTERNAL_ERROR.http_status,
        content=AppError(INTERNAL_ERROR).to_payload(request_id),
    )


app.include_router(api_router)


@app.get("/", include_in_schema=False)
def root() -> dict[str, str]:
    return {"service": settings.app_name, "version": settings.version, "docs": "/api/v1/health"}
