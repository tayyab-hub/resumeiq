"""Loads the curated data files once and exposes them as immutable lookups."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Characters that may legitimately form part of a skill token ("c++", "node.js",
# "c#"). A match must not be flanked by any of them, which is what stops "R"
# matching "Requirements" and "Go" matching "Google".
_TOKEN_CHARS = r"A-Za-z0-9+#\.\-"


@dataclass(frozen=True)
class Skill:
    name: str
    display: str
    category: str
    aliases: tuple[str, ...]
    related: tuple[str, ...]


def _compile_term(term: str) -> re.Pattern[str]:
    return re.compile(
        rf"(?<![{_TOKEN_CHARS}]){re.escape(term)}(?![{_TOKEN_CHARS}])",
        re.IGNORECASE,
    )


@lru_cache(maxsize=1)
def load_taxonomy() -> tuple[Skill, ...]:
    payload = json.loads((_DATA_DIR / "skills_taxonomy.json").read_text(encoding="utf-8"))
    return tuple(
        Skill(
            name=entry["name"],
            display=entry["display"],
            category=entry["category"],
            aliases=tuple(entry.get("aliases", ())),
            related=tuple(entry.get("related", ())),
        )
        for entry in payload["skills"]
    )


@lru_cache(maxsize=1)
def skills_by_name() -> dict[str, Skill]:
    return {skill.name: skill for skill in load_taxonomy()}


@lru_cache(maxsize=1)
def _compiled_terms() -> tuple[tuple[str, str, re.Pattern[str]], ...]:
    """(canonical_name, matched_via, pattern) for every canonical name and alias.

    Longer terms first, so "spring boot" is tested before "spring".
    """
    entries: list[tuple[str, str, str]] = []
    for skill in load_taxonomy():
        entries.append((skill.name, "exact", skill.name))
        for alias in skill.aliases:
            entries.append((skill.name, "alias", alias))
    entries.sort(key=lambda item: len(item[2]), reverse=True)
    return tuple((name, via, _compile_term(term)) for name, via, term in entries)


def compiled_terms() -> tuple[tuple[str, str, re.Pattern[str]], ...]:
    return _compiled_terms()


@lru_cache(maxsize=1)
def _language_data() -> dict:
    return json.loads((_DATA_DIR / "language_data.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def action_verbs() -> frozenset[str]:
    return frozenset(_language_data()["action_verbs"])


@lru_cache(maxsize=1)
def generic_phrases() -> tuple[str, ...]:
    return tuple(_language_data()["generic_phrases"])


@lru_cache(maxsize=1)
def jd_boilerplate() -> tuple[str, ...]:
    return tuple(_language_data()["jd_boilerplate"])


@lru_cache(maxsize=1)
def stopwords() -> frozenset[str]:
    return frozenset(_language_data()["stopwords"])


@lru_cache(maxsize=1)
def section_headings() -> dict[str, tuple[str, ...]]:
    return {
        key: tuple(values)
        for key, values in _language_data()["section_headings"].items()
    }


@lru_cache(maxsize=1)
def required_cues() -> tuple[str, ...]:
    return tuple(_language_data()["required_cues"])


@lru_cache(maxsize=1)
def preferred_cues() -> tuple[str, ...]:
    return tuple(_language_data()["preferred_cues"])
