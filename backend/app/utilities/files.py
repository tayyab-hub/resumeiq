"""Filename sanitisation.

The uploaded name is never used to build a filesystem path — nothing is written
to disk at all. It is still sanitised, because it is echoed back to the user and
stored, and because defending in depth costs nothing here.
"""

from __future__ import annotations

import os
import re

_ALLOWED = re.compile(r"[^A-Za-z0-9 ._\-()]")
_COLLAPSE = re.compile(r"[ _]{2,}")
MAX_FILENAME_LENGTH = 255


def sanitise_filename(raw_name: str | None) -> str:
    """Return a safe display label. Never returns an empty string."""
    if not raw_name:
        return "resume.pdf"

    # Strip any directory component, including Windows-style separators that
    # os.path.basename leaves alone on POSIX hosts.
    name = raw_name.replace("\\", "/")
    name = os.path.basename(name)

    name = _ALLOWED.sub("_", name).strip(" .")
    name = _COLLAPSE.sub("_", name)

    if name in ("", ".", ".."):
        return "resume.pdf"

    if len(name) > MAX_FILENAME_LENGTH:
        stem, extension = os.path.splitext(name)
        name = stem[: MAX_FILENAME_LENGTH - len(extension)] + extension

    return name


def has_pdf_extension(filename: str | None) -> bool:
    return bool(filename) and filename.strip().lower().endswith(".pdf")
