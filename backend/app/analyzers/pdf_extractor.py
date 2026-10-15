"""PDF extraction isolated in a killable, resource-limited child process.

The multipart framework may spool uploads to temporary disk before this layer.
No original file is deliberately persisted. Magic bytes are only a format hint.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading

from app.analyzers.text_utils import meaningful_character_count, normalise_text
from app.core.config import settings
from app.core.error_codes import (
    RESUME_CORRUPT,
    RESUME_EMPTY,
    RESUME_ENCRYPTED,
    RESUME_INVALID_TYPE,
    RESUME_NO_TEXT_LAYER,
    RESUME_TOO_LARGE,
    ErrorSpec,
)
from app.core.exceptions import ExtractionError

PDF_MAGIC = b"%PDF-"
RESOURCE_LIMIT = ErrorSpec(
    "RESUME_RESOURCE_LIMIT",
    422,
    "This PDF is too complex to analyse safely.",
    "PDFs are limited to 10 pages, 100,000 extracted characters and 10 seconds of processing.",
    "Export a shorter, simpler text PDF and retry.",
)
EXTRACTION_BUSY = ErrorSpec(
    "EXTRACTION_BUSY",
    503,
    "Another PDF is being processed.",
    "The demo processes one PDF at a time to stay within its memory budget.",
    "Wait a few seconds and retry.",
)
_slot = threading.BoundedSemaphore(1)


def validate_pdf_bytes(data: bytes) -> None:
    if not data:
        raise ExtractionError(RESUME_EMPTY)
    if len(data) > settings.max_upload_bytes:
        raise ExtractionError(RESUME_TOO_LARGE)
    if not data.startswith(PDF_MAGIC):
        raise ExtractionError(RESUME_INVALID_TYPE)


def extract_text(data: bytes, min_chars: int = 200) -> str:
    validate_pdf_bytes(data)
    if not _slot.acquire(blocking=False):
        raise ExtractionError(EXTRACTION_BUSY)
    try:
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "app.analyzers.pdf_worker",
                    str(settings.pdf_max_pages),
                    str(settings.pdf_max_text_chars),
                    str(settings.pdf_memory_mb),
                    str(int(settings.pdf_timeout_seconds) + 1),
                ],
                input=data,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                timeout=settings.pdf_timeout_seconds,
                check=False,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
                env={
                    key: value
                    for key, value in os.environ.items()
                    if key.upper() in {"PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "LANG"}
                },
            )
        except subprocess.TimeoutExpired as exc:
            raise ExtractionError(RESOURCE_LIMIT) from exc
        if result.returncode or len(result.stdout) > settings.pdf_max_text_chars * 6 + 1024:
            raise ExtractionError(RESOURCE_LIMIT)
        try:
            payload = json.loads(result.stdout)
        except (ValueError, UnicodeError) as exc:
            raise ExtractionError(RESUME_CORRUPT) from exc
        error = payload.get("error")
        if error:
            raise ExtractionError(
                {
                    "encrypted": RESUME_ENCRYPTED,
                    "limit": RESOURCE_LIMIT,
                }.get(error, RESUME_CORRUPT)
            )
        text = normalise_text(payload["text"])
        if meaningful_character_count(text) < min_chars:
            raise ExtractionError(RESUME_NO_TEXT_LAYER)
        return text
    finally:
        _slot.release()
