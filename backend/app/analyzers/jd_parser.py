"""Job description parsing.

The required/preferred split is cue-based. When a posting uses no recognisable
cue the parser treats every requirement as required and sets
`requirement_split_inferred`, which the UI surfaces to the user. Disclosing the
assumption is more honest than presenting a guess as a fact.
"""

from __future__ import annotations

import re
from collections import Counter

from app.analyzers.domain import JobProfile
from app.analyzers.experience_parser import extract_required_education, extract_required_years
from app.analyzers.skill_extractor import extract_skill_names
from app.analyzers.text_utils import normalise_text
from app.analyzers.vocabulary import jd_boilerplate, preferred_cues, required_cues, stopwords

MAX_KEYWORDS = 25

_WORD = re.compile(r"[A-Za-z][A-Za-z+#.\-]{2,}")
_TITLE_LINE = re.compile(
    r"^\s*(?:job\s+title|position|role)\s*[:\-]\s*(.+)$", re.IGNORECASE | re.MULTILINE
)
_COMPANY_LINE = re.compile(
    r"^\s*(?:company|organisation|organization|employer)\s*[:\-]\s*(.+)$",
    re.IGNORECASE | re.MULTILINE,
)


def _strip_boilerplate(text: str) -> str:
    lowered = text.lower()
    for phrase in jd_boilerplate():
        lowered = lowered.replace(phrase, " ")
    return lowered


def _split_by_requirement_cue(text: str) -> tuple[str, str, bool]:
    """Return (required_block, preferred_block, split_was_inferred)."""
    lowered = text.lower()

    preferred_start: int | None = None
    for cue in preferred_cues():
        index = lowered.find(cue)
        if index != -1 and (preferred_start is None or index < preferred_start):
            preferred_start = index

    required_start: int | None = None
    for cue in required_cues():
        index = lowered.find(cue)
        if index != -1 and (required_start is None or index < required_start):
            required_start = index

    if preferred_start is None:
        # No "nice to have" cue anywhere: treat the whole posting as required
        # and disclose that this assumption was made.
        return text, "", True

    if required_start is not None and required_start < preferred_start:
        return text[required_start:preferred_start], text[preferred_start:], False

    # A preferred block exists but no explicit required heading: everything
    # before it is treated as the requirement body.
    return text[:preferred_start], text[preferred_start:], False


def extract_keywords(text: str, exclude: set[str]) -> tuple[str, ...]:
    """Meaningful non-skill vocabulary from the posting.

    Skills are excluded because they are already scored, in full, by their own
    categories; counting them twice would double-weight them.
    """
    cleaned = _strip_boilerplate(text)
    stops = stopwords()
    counts: Counter[str] = Counter()

    for match in _WORD.finditer(cleaned):
        word = match.group(0).strip(".-").lower()
        if len(word) < 3 or word in stops or word in exclude:
            continue
        counts[word] += 1

    return tuple(word for word, _ in counts.most_common(MAX_KEYWORDS))


def _first_line_title(text: str) -> str | None:
    for line in text.split("\n"):
        candidate = line.strip()
        if 3 <= len(candidate) <= 80 and not candidate.endswith((".", ":")):
            return candidate
    return None


def parse_job_description(
    raw_text: str,
    job_title: str | None = None,
    company_name: str | None = None,
) -> JobProfile:
    text = normalise_text(raw_text)

    required_block, preferred_block, inferred = _split_by_requirement_cue(text)

    required = list(extract_skill_names(required_block))
    preferred = [name for name in extract_skill_names(preferred_block) if name not in required]

    # A skill named anywhere else in the posting still counts as required: a
    # requirement stated in the responsibilities section is still a requirement.
    for name in extract_skill_names(text):
        if name not in required and name not in preferred:
            required.append(name)

    all_skills = set(required) | set(preferred)
    keywords = extract_keywords(text, exclude=all_skills)

    resolved_title = (job_title or "").strip() or None
    if resolved_title is None:
        match = _TITLE_LINE.search(text)
        resolved_title = match.group(1).strip() if match else _first_line_title(text)

    resolved_company = (company_name or "").strip() or None
    if resolved_company is None:
        match = _COMPANY_LINE.search(text)
        resolved_company = match.group(1).strip() if match else None

    return JobProfile(
        raw_text=text,
        job_title=resolved_title[:160] if resolved_title else None,
        company_name=resolved_company[:160] if resolved_company else None,
        required_skills=tuple(sorted(required)),
        preferred_skills=tuple(sorted(preferred)),
        min_years_experience=extract_required_years(text),
        required_education_level=extract_required_education(text),
        keywords=keywords,
        requirement_split_inferred=inferred,
    )
