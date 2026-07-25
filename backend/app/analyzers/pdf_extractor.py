"""PDF validation and text extraction.

Validation order is deliberate: cheapest and most decisive first. The magic-byte
check is authoritative, because it is the only one an attacker cannot forge by
renaming a file or setting a header.
"""

from __future__ import annotations

from app.analyzers.text_utils import meaningful_character_count, normalise_text
from app.core.error_codes import (
    RESUME_CORRUPT,
    RESUME_EMPTY,
    RESUME_ENCRYPTED,
    RESUME_INVALID_TYPE,
    RESUME_NO_TEXT_LAYER,
)
from app.core.exceptions import ExtractionError

PDF_MAGIC = b"%PDF-"


def validate_pdf_bytes(data: bytes) -> None:
    """Raise if the payload is not a usable PDF. Never returns a value."""
    if not data:
        raise ExtractionError(RESUME_EMPTY)
    if not data.startswith(PDF_MAGIC):
        raise ExtractionError(RESUME_INVALID_TYPE)


def extract_text(data: bytes, min_chars: int = 200) -> str:
    """Return normalised text from an in-memory PDF.

    The bytes are opened from memory: nothing is written to disk at any point,
    so there is no temporary file to leak or forget to delete.
    """
    validate_pdf_bytes(data)

    try:
        import fitz  # PyMuPDF
    except ImportError as exc:  # pragma: no cover - dependency is required
        raise ExtractionError(RESUME_CORRUPT) from exc

    document = None
    try:
        try:
            document = fitz.open(stream=data, filetype="pdf")
        except Exception as exc:
            # Any failure to open is reported as a damaged file. The underlying
            # library message is never surfaced to the client.
            raise ExtractionError(RESUME_CORRUPT) from exc

        if document.needs_pass:
            raise ExtractionError(RESUME_ENCRYPTED)

        if document.page_count == 0:
            raise ExtractionError(RESUME_CORRUPT)

        pages: list[str] = []
        for page in document:
            try:
                pages.append(page.get_text("text"))
            except Exception:  # noqa: BLE001 - a bad page should not lose the document
                continue

        text = normalise_text("\n".join(pages))
    finally:
        if document is not None:
            document.close()

    if meaningful_character_count(text) < min_chars:
        # A scan is a specific, fixable situation. Reporting it as a generic
        # failure would leave the user with nothing to act on.
        raise ExtractionError(RESUME_NO_TEXT_LAYER)

    return text
