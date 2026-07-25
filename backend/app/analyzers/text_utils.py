"""Text normalisation and bullet segmentation.

Every function here is pure: text in, text or structure out. No I/O, no clock,
no randomness.
"""

from __future__ import annotations

import re
import unicodedata

# Bullet glyphs commonly produced by Word, Google Docs, and LaTeX exports.
_BULLET_GLYPHS = "•▪◦‣∙·●○■□–—*"
_BULLET_PREFIX = re.compile(rf"^[\s{re.escape(_BULLET_GLYPHS)}\-]+")
_LINE_BULLET = re.compile(rf"^\s*[{re.escape(_BULLET_GLYPHS)}]\s+")
_HYPHEN_LINEBREAK = re.compile(r"(\w)-\n(\w)")
_MULTI_SPACE = re.compile(r"[ \t ]+")
_MULTI_NEWLINE = re.compile(r"\n{3,}")
_TRAILING_SPACE = re.compile(r"[ \t]+\n")


def normalise_text(raw: str) -> str:
    """Collapse whitespace and rejoin split words without losing paragraphs.

    Paragraph boundaries survive deliberately: section detection depends on
    them.
    """
    if not raw:
        return ""

    text = unicodedata.normalize("NFKC", raw)
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # "develop-\nment" -> "development", before whitespace collapsing.
    text = _HYPHEN_LINEBREAK.sub(r"\1\2", text)

    text = _MULTI_SPACE.sub(" ", text)
    text = _TRAILING_SPACE.sub("\n", text)
    text = _MULTI_NEWLINE.sub("\n\n", text)

    # One bullet marker, so downstream splitting has a single case to handle.
    lines = [_LINE_BULLET.sub("- ", line) for line in text.split("\n")]
    return "\n".join(line.strip() for line in lines).strip()


def meaningful_character_count(text: str) -> int:
    """Letters and digits only.

    A scanned PDF often yields a page of whitespace and stray punctuation; that
    should not count as extracted text.
    """
    return sum(1 for char in text if char.isalnum())


def split_lines(text: str) -> list[str]:
    return [line.strip() for line in text.split("\n") if line.strip()]


def extract_bullets(text: str) -> list[str]:
    """Return candidate achievement statements.

    A statement is either an explicitly bulleted line or a standalone sentence
    line long enough to be a claim rather than a heading.
    """
    bullets: list[str] = []
    for line in split_lines(text):
        stripped = _BULLET_PREFIX.sub("", line).strip()
        if len(stripped) < 25:
            continue
        # Headings are short, title-cased, and unpunctuated; those are excluded
        # by the length rule above and by requiring at least four words.
        if len(stripped.split()) < 4:
            continue
        bullets.append(stripped)
    return bullets


def word_count(text: str) -> int:
    return len(text.split())


def truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def snippet_around(text: str, index: int, width: int = 90) -> str:
    """A short, single-line excerpt centred on `index`, for match evidence."""
    start = max(0, index - width // 2)
    end = min(len(text), index + width // 2)
    excerpt = text[start:end].replace("\n", " ").strip()
    if start > 0:
        excerpt = "…" + excerpt
    if end < len(text):
        excerpt = excerpt + "…"
    return _MULTI_SPACE.sub(" ", excerpt)
