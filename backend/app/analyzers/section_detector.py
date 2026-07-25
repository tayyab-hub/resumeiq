"""Resume section detection.

Headings are matched on their own line, because "experience" appearing inside a
sentence is not a section heading. Contact is the exception: it is detected from
content patterns, since most resumes place contact details at the top with no
heading at all.
"""

from __future__ import annotations

import re

from app.analyzers.domain import SECTION_ORDER, SectionResult
from app.analyzers.vocabulary import section_headings

_EMAIL = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
_PHONE = re.compile(r"(?:\+?\d[\d\s().\-]{7,}\d)")
_URL = re.compile(r"(?:https?://|www\.)[^\s]+|linkedin\.com/\S+|github\.com/\S+", re.IGNORECASE)

# A heading line is short and contains no sentence-ending punctuation.
_MAX_HEADING_WORDS = 6

_NOTES: dict[str, tuple[str, str]] = {
    # key: (note when present, note when missing)
    "contact": (
        "Found contact details.",
        "No email address or phone number was found. A reader must be able to contact you.",
    ),
    "summary": (
        "Found a professional summary.",
        "No professional summary detected. Two or three lines at the top help a reader place you quickly.",
    ),
    "skills": (
        "Found a skills section.",
        "No skills section detected. A grouped skills list makes your technologies easy to scan.",
    ),
    "experience": (
        "Found a work experience section.",
        "No work experience section detected. If you have none yet, a projects section can carry this weight.",
    ),
    "education": (
        "Found an education section.",
        "No education section detected. Include your qualification, institution, and completion year.",
    ),
    "projects": (
        "Found a projects section.",
        "No projects section detected. Projects are strong evidence of skills when experience is limited.",
    ),
    "certifications": (
        "Found certifications or training.",
        "No certifications section detected. Include any relevant courses or credentials you hold.",
    ),
    "achievements": (
        "Found an achievements section.",
        "No achievements section detected. This is optional, but awards and recognition are worth listing.",
    ),
    "languages": (
        "Found a languages section.",
        "No languages section detected. This is optional and matters only for some roles.",
    ),
}


def _looks_like_heading(line: str) -> bool:
    stripped = line.strip().strip(":").strip()
    if not stripped or len(stripped.split()) > _MAX_HEADING_WORDS:
        return False
    return not stripped.endswith((".", ",", ";"))


def _normalise_heading(line: str) -> str:
    return re.sub(r"[^a-z& ]+", " ", line.lower()).strip()


def detect_sections(text: str) -> tuple[SectionResult, ...]:
    """Return one result per known section, in display order.

    Absence is recorded explicitly rather than omitted, so "analysed and
    missing" stays distinguishable from "never analysed".
    """
    headings = section_headings()
    lines = text.split("\n")

    found: dict[str, tuple[str, int]] = {}
    offset = 0
    for line in lines:
        line_start = offset
        offset += len(line) + 1
        if not _looks_like_heading(line):
            continue
        normalised = _normalise_heading(line)
        if not normalised:
            continue
        for key, variants in headings.items():
            if key in found:
                continue
            if any(normalised == variant or normalised.startswith(variant + " ") for variant in variants):
                found[key] = (line.strip().strip(":").strip(), line_start)
                break

    # Contact is content-based: most resumes have the details without a heading.
    contact_detected = bool(_EMAIL.search(text) or _PHONE.search(text) or _URL.search(text))

    # Results are emitted in SECTION_ORDER, which is the display order; the
    # caller assigns the stored display_order index when persisting.
    results: list[SectionResult] = []
    for key in SECTION_ORDER:
        present_note, missing_note = _NOTES[key]
        heading, start = found.get(key, (None, None))
        detected = (contact_detected or key in found) if key == "contact" else key in found
        results.append(
            SectionResult(
                key=key,
                detected=detected,
                matched_heading=heading,
                note=present_note if detected else missing_note,
                start_index=start,
            )
        )
    return tuple(results)


def experience_span(text: str, sections: tuple[SectionResult, ...]) -> str:
    """Return the text of the experience section, or the whole document.

    Falling back to the whole document is deliberate: a resume with no
    detectable experience heading should not be scored as though it described
    no work at all.
    """
    experience = next((s for s in sections if s.key == "experience"), None)
    if experience is None or not experience.detected or experience.start_index is None:
        return text

    starts = sorted(
        s.start_index
        for s in sections
        if s.detected and s.start_index is not None and s.start_index > experience.start_index
    )
    end = starts[0] if starts else len(text)
    return text[experience.start_index : end]
