"""Skill extraction against the curated taxonomy.

Matching is lexical and word-boundary aware. This is a deliberate trade: an
embedding model would match more, but it could not tell the user *why* a skill
was considered present, which is the whole point of the product.
"""

from __future__ import annotations

from app.analyzers.domain import DetectedSkill
from app.analyzers.text_utils import snippet_around
from app.analyzers.vocabulary import compiled_terms, skills_by_name


def extract_skills(text: str, experience_text: str = "") -> tuple[DetectedSkill, ...]:
    """Find every taxonomy skill present in the text.

    `experience_text` is used only to record whether the skill appears inside
    the work experience section — a skill demonstrated in a job bullet is
    stronger evidence than one named in a comma-separated list.
    """
    if not text:
        return ()

    catalogue = skills_by_name()
    found: dict[str, DetectedSkill] = {}

    for canonical, matched_via, pattern in compiled_terms():
        if canonical in found and found[canonical].matched_via == "exact":
            continue
        match = pattern.search(text)
        if match is None:
            continue

        skill = catalogue[canonical]
        in_experience = bool(experience_text) and pattern.search(experience_text) is not None
        candidate = DetectedSkill(
            name=canonical,
            display=skill.display,
            matched_via=matched_via,  # type: ignore[arg-type]
            snippet=snippet_around(text, match.start()),
            in_experience=in_experience,
        )
        # An exact hit always beats an alias hit for the same skill.
        existing = found.get(canonical)
        if existing is None or (existing.matched_via != "exact" and matched_via == "exact"):
            found[canonical] = candidate

    return tuple(sorted(found.values(), key=lambda item: item.name))


def extract_skill_names(text: str) -> tuple[str, ...]:
    """Canonical skill names only. Used for job descriptions, where evidence
    snippets are not needed."""
    return tuple(skill.name for skill in extract_skills(text))
