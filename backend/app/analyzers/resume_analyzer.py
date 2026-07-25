"""Assembles a ResumeProfile from extracted text.

Pure: the whole resume-side analysis is a single function of a single string,
which is what makes it cheap to test and easy to explain.
"""

from __future__ import annotations

import re
from datetime import date

from app.analyzers.domain import ResumeProfile
from app.analyzers.experience_parser import detect_education_level, estimate_experience_months
from app.analyzers.section_detector import detect_sections, experience_span
from app.analyzers.skill_extractor import extract_skills
from app.analyzers.statement_analyzer import analyse_statements

_WORD = re.compile(r"[A-Za-z][A-Za-z+#.\-]{2,}")


def resume_keywords(text: str) -> frozenset[str]:
    """Every distinct word in the resume, for keyword-coverage comparison."""
    return frozenset(match.group(0).strip(".-").lower() for match in _WORD.finditer(text))


def build_resume_profile(text: str, today: date | None = None) -> ResumeProfile:
    sections = detect_sections(text)
    experience_text = experience_span(text, sections)

    return ResumeProfile(
        text=text,
        skills=extract_skills(text, experience_text=experience_text),
        sections=sections,
        statements=analyse_statements(text),
        experience=estimate_experience_months(text, today=today),
        education_level=detect_education_level(text),
        keywords_present=resume_keywords(text),
    )
