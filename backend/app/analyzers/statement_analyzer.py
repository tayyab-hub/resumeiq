"""Resume statement (bullet) quality analysis.

Every suggestion produced here is *structural*. It tells the user what shape a
stronger statement takes; it never supplies a number, an employer, or an
outcome. Inventing an achievement on a resume would be worse than useless, and
the anti-fabrication rule is enforced by a test.
"""

from __future__ import annotations

import re
from collections import Counter

from app.analyzers.domain import StatementAnalysis, StatementFinding
from app.analyzers.text_utils import extract_bullets, truncate, word_count
from app.analyzers.vocabulary import action_verbs, generic_phrases

MAX_BULLET_WORDS = 35
MAX_STORED_FINDINGS = 30
REPETITION_THRESHOLD = 3

ISSUE_NO_ACTION_VERB = "NO_ACTION_VERB"
ISSUE_NO_METRIC = "NO_METRIC"
ISSUE_GENERIC_PHRASING = "GENERIC_PHRASING"
ISSUE_PASSIVE_VOICE = "PASSIVE_VOICE"
ISSUE_TOO_LONG = "TOO_LONG"
ISSUE_REPETITION = "REPETITION"

# Percentages, currency, counts with units, time reductions, plain magnitudes.
_MEASURABLE = re.compile(
    r"""
    \d+\s?%                                   # 40%
    | [£$€]\s?\d                              # $12k
    | \b\d[\d,]*\s?(?:k|m|bn|million|billion|thousand)\b
    | \b\d[\d,]*\s?(?:users|customers|clients|records|requests|transactions|
        students|employees|hours|days|weeks|months|items|orders|tickets|
        queries|rows|files|sites|pages|servers|tests|bugs|calls)\b
    | \b\d+(?:\.\d+)?\s?(?:ms|milliseconds|seconds|secs|minutes|mins|hours|
        gb|mb|tb|kb|fps|rps|qps)\b
    | \bfrom\s+\d[\d,.]*\s+to\s+\d[\d,.]*
    | \bby\s+\d[\d,.]*
    """,
    re.IGNORECASE | re.VERBOSE,
)

_PASSIVE = re.compile(
    r"\b(?:was|were|been|being|is|are)\s+(?:\w+ly\s+)?\w+(?:ed|en)\b(?:\s+by\b)?",
    re.IGNORECASE,
)

# Years, versions, and dates are numbers but not achievements.
_NON_ACHIEVEMENT_NUMBER = re.compile(r"\b(?:19|20)\d{2}\b|\bv?\d+\.\d+(?:\.\d+)?\b")


def _has_measurable_result(statement: str) -> bool:
    cleaned = _NON_ACHIEVEMENT_NUMBER.sub(" ", statement)
    return bool(_MEASURABLE.search(cleaned))


def _starts_with_action_verb(statement: str) -> bool:
    first = re.sub(r"[^a-zA-Z]", "", statement.split()[0]) if statement.split() else ""
    return first.lower() in action_verbs()


def _matched_generic_phrases(statement: str) -> list[str]:
    lowered = statement.lower()
    return [phrase for phrase in generic_phrases() if phrase in lowered]


def _normalised_phrase_key(statement: str) -> str:
    words = re.findall(r"[a-z]+", statement.lower())
    return " ".join(words[:6])


def _build_suggestion(issues: tuple[str, ...], statement: str) -> str | None:
    """Structural guidance only. Never supplies facts the user did not write."""
    if not issues:
        return None

    parts: list[str] = []
    if ISSUE_GENERIC_PHRASING in issues or ISSUE_NO_ACTION_VERB in issues:
        parts.append(
            "Open with a specific action verb describing what you did, rather than a phrase "
            "about your duties"
        )
    if ISSUE_PASSIVE_VOICE in issues:
        parts.append("Rewrite in the active voice so it is clear that you did the work")
    if ISSUE_NO_METRIC in issues:
        parts.append(
            "State the result. If you know a figure — a percentage, a count, a time saved — "
            "include it. Do not estimate or invent one"
        )
    if ISSUE_TOO_LONG in issues:
        parts.append(
            f"Shorten to roughly {MAX_BULLET_WORDS} words, or split it into two statements"
        )
    if ISSUE_REPETITION in issues:
        parts.append("Vary the opening: this phrasing is repeated elsewhere in your resume")

    if not parts:
        return None
    return ". ".join(parts) + "."


def analyse_statements(text: str) -> StatementAnalysis:
    bullets = extract_bullets(text)
    if not bullets:
        return StatementAnalysis(
            total_bullets=0, with_measurable_result=0, action_verb_rate=0.0, findings=()
        )

    phrase_counts = Counter(_normalised_phrase_key(bullet) for bullet in bullets)
    repeated = {
        phrase for phrase, count in phrase_counts.items()
        if count >= REPETITION_THRESHOLD and phrase
    }

    findings: list[StatementFinding] = []
    measurable_count = 0
    action_verb_count = 0

    for bullet in bullets:
        issues: list[str] = []

        has_verb = _starts_with_action_verb(bullet)
        if has_verb:
            action_verb_count += 1
        else:
            issues.append(ISSUE_NO_ACTION_VERB)

        measurable = _has_measurable_result(bullet)
        if measurable:
            measurable_count += 1
        else:
            issues.append(ISSUE_NO_METRIC)

        if _matched_generic_phrases(bullet):
            issues.append(ISSUE_GENERIC_PHRASING)
        if _PASSIVE.search(bullet):
            issues.append(ISSUE_PASSIVE_VOICE)

        words = word_count(bullet)
        if words > MAX_BULLET_WORDS:
            issues.append(ISSUE_TOO_LONG)
        if _normalised_phrase_key(bullet) in repeated:
            issues.append(ISSUE_REPETITION)

        # A bullet whose only shortfall is a missing metric is not "weak"; many
        # legitimate statements have no number. It is reported only when it also
        # fails on structure.
        if issues == [ISSUE_NO_METRIC]:
            continue
        if not issues:
            continue

        ordered = tuple(issues)
        findings.append(
            StatementFinding(
                text=truncate(bullet, 600),
                issue_codes=ordered,
                word_count=words,
                has_measurable_result=measurable,
                suggestion=_build_suggestion(ordered, bullet),
            )
        )

    findings.sort(key=lambda f: len(f.issue_codes), reverse=True)

    return StatementAnalysis(
        total_bullets=len(bullets),
        with_measurable_result=measurable_count,
        action_verb_rate=round(action_verb_count / len(bullets), 4),
        findings=tuple(findings[:MAX_STORED_FINDINGS]),
        repeated_phrases=tuple(sorted(repeated)),
    )
