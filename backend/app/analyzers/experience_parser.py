"""Employment duration and education level parsing."""

from __future__ import annotations

import re
from datetime import date

from app.analyzers.domain import EDUCATION_LEVELS, ExperienceEstimate

_MONTHS = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "sept": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}
_MONTH_ALT = "|".join(_MONTHS)
_PRESENT = r"present|current|now|to date|ongoing"
_DASH = r"\s*(?:-|–|—|to|until)\s*"

# "Jan 2023 - Present", "March 2021 – Dec 2022"
_MONTH_YEAR_RANGE = re.compile(
    rf"\b({_MONTH_ALT})[a-z]*\.?\s+(\d{{4}}){_DASH}(?:({_MONTH_ALT})[a-z]*\.?\s+(\d{{4}})|({_PRESENT}))",
    re.IGNORECASE,
)
# "03/2022 - 06/2024"
_NUMERIC_RANGE = re.compile(
    rf"\b(\d{{1,2}})/(\d{{4}}){_DASH}(?:(\d{{1,2}})/(\d{{4}})|({_PRESENT}))",
    re.IGNORECASE,
)
# "2021 - 2023", "2020 – Present"
_YEAR_RANGE = re.compile(rf"\b(\d{{4}}){_DASH}(?:(\d{{4}})|({_PRESENT}))", re.IGNORECASE)

_EDUCATION_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("doctorate", re.compile(r"\b(ph\.?d|doctorate|doctoral|d\.phil)\b", re.IGNORECASE)),
    (
        "master",
        re.compile(
            r"\b(master'?s?|m\.?sc|m\.?a\b|m\.?eng|mba|m\.?tech|postgraduate)\b", re.IGNORECASE
        ),
    ),
    (
        "bachelor",
        re.compile(
            r"\b(bachelor'?s?|b\.?sc|b\.?a\b|b\.?eng|b\.?tech|bs\b|ba\b|undergraduate degree)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "diploma",
        re.compile(
            r"\b(diploma|associate'?s? degree|foundation degree|higher national)\b", re.IGNORECASE
        ),
    ),
    ("certificate", re.compile(r"\b(certificate|certification|certified)\b", re.IGNORECASE)),
)

_YEARS_REQUIRED = re.compile(
    r"\b(?:(\d{1,2})\s*\+|at least\s+(\d{1,2})|minimum(?:\s+of)?\s+(\d{1,2})|(\d{1,2})\s*(?:-|–|to)\s*\d{1,2})\s*(?:\+\s*)?years?\b",
    re.IGNORECASE,
)
_YEARS_SIMPLE = re.compile(
    r"\b(\d{1,2})\s*(?:\+\s*)?years?(?:\s+of)?\s+(?:relevant\s+|professional\s+|industry\s+)?experience\b",
    re.IGNORECASE,
)
_YEARS_WORDS = re.compile(
    r"\b(one|two|three|four|five|six|seven|eight|nine|ten)\s+(?:\+\s*)?years?\b", re.IGNORECASE
)
_WORD_NUMBERS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
}


def _merge(intervals: list[tuple[int, int]]) -> int:
    """Total months covered by the union of the intervals.

    Overlapping roles must not be double counted; two concurrent 12-month jobs
    are one year of experience, not two.
    """
    if not intervals:
        return 0
    ordered = sorted(intervals)
    merged: list[list[int]] = [list(ordered[0])]
    for start, end in ordered[1:]:
        if start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return sum(end - start for start, end in merged)


def estimate_experience_months(text: str, today: date | None = None) -> ExperienceEstimate:
    """Estimate total months of experience from date ranges.

    `today` is injected rather than read from the clock so the function stays
    pure and its tests stay deterministic.
    """
    reference = today or date.today()
    now_month_index = reference.year * 12 + reference.month
    intervals: list[tuple[int, int]] = []

    def add(start_year: int, start_month: int, end_year: int | None, end_month: int | None) -> None:
        start = start_year * 12 + start_month
        end = now_month_index if end_year is None else end_year * 12 + (end_month or 12)
        if 1900 * 12 < start <= end:
            intervals.append((start, end))

    for match in _MONTH_YEAR_RANGE.finditer(text):
        # The capture group is one of the dictionary keys by construction.
        s_month = _MONTHS[match.group(1).lower()]
        s_year = int(match.group(2))
        if match.group(5):
            add(s_year, s_month, None, None)
        else:
            add(s_year, s_month, int(match.group(4)), _MONTHS[match.group(3).lower()])

    for match in _NUMERIC_RANGE.finditer(text):
        s_month, s_year = int(match.group(1)), int(match.group(2))
        if not 1 <= s_month <= 12:
            continue
        if match.group(5):
            add(s_year, s_month, None, None)
        else:
            add(s_year, s_month, int(match.group(4)), int(match.group(3)))

    for match in _YEAR_RANGE.finditer(text):
        s_year = int(match.group(1))
        if not 1950 <= s_year <= reference.year:
            continue
        if match.group(3):
            add(s_year, 1, None, None)
        elif match.group(2):
            # A bare "2021 - 2023" is measured start-of-year to start-of-year.
            # Reading it as January to December would silently credit an extra
            # year; where the data is ambiguous, understate rather than inflate.
            add(s_year, 1, int(match.group(2)), 1)

    if not intervals:
        return ExperienceEstimate(total_months=None, date_ranges_found=0)

    return ExperienceEstimate(total_months=_merge(intervals), date_ranges_found=len(intervals))


def detect_education_level(text: str) -> str:
    """Highest qualification level named anywhere in the text."""
    for level, pattern in _EDUCATION_PATTERNS:
        if pattern.search(text):
            return level
    return "none"


def extract_required_years(text: str) -> int | None:
    """Smallest stated experience requirement.

    Smallest, not largest: "3+ years, 5+ preferred" sets the bar at three.
    """
    candidates: list[int] = []

    for match in _YEARS_SIMPLE.finditer(text):
        candidates.append(int(match.group(1)))

    for match in _YEARS_REQUIRED.finditer(text):
        for group in match.groups():
            if group and group.isdigit():
                candidates.append(int(group))
                break

    for match in _YEARS_WORDS.finditer(text):
        candidates.append(_WORD_NUMBERS[match.group(1).lower()])

    sane = [value for value in candidates if 0 < value <= 30]
    return min(sane) if sane else None


def extract_required_education(text: str) -> str | None:
    level = detect_education_level(text)
    return None if level == "none" else level


def education_ordinal(level: str | None) -> int:
    return EDUCATION_LEVELS.get(level or "none", 0)
