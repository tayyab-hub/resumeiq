"""Liveness and database reachability.

Deliberately returns nothing about build paths, dependency versions, or the
environment: a health endpoint is a reconnaissance target.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.session import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
def health(response: Response, db: Session = Depends(get_db)) -> dict[str, str]:
    try:
        db.execute(text("SELECT 1"))
        database_status = "ok"
    except Exception:  # noqa: BLE001 - the cause is logged, not returned
        database_status = "unreachable"
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "ok" if database_status == "ok" else "degraded",
        "database": database_status,
        "version": settings.version,
    }
