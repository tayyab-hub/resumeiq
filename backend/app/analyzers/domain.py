"""Plain data structures passed between the analyzers.

These are frozen dataclasses rather than Pydantic models on purpose: the
analyzers are pure functions with no serialisation concerns, and immutability
makes accidental mutation between stages impossible.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

MatchStatus = Literal["matched", "partial", "missing"]
RequirementLevel = Literal["required", "preferred"]
MatchedVia = Literal["exact", "alias", "related"]

EDUCATION_LEVELS: dict[str, int] = {
    "none": 0,
    "certificate": 1,
    "diploma": 2,
    "bachelor": 3,
    "master": 4,
    "doctorate": 5,
}

SECTION_ORDER: tuple[str, ...] = (
    "contact",
    "summary",
    "skills",
    "experience",
    "education",
    "projects",
    "certifications",
    "achievements",
    "languages",
)


@dataclass(frozen=True)
class DetectedSkill:
    name: str
    display: str
    matched_via: MatchedVia
    snippet: str
    in_experience: bool = False


@dataclass(frozen=True)
class SectionResult:
    key: str
    detected: bool
    matched_heading: str | None
    note: str
    start_index: int | None = None
    end_index: int | None = None


@dataclass(frozen=True)
class StatementFinding:
    text: str
    issue_codes: tuple[str, ...]
    word_count: int
    has_measurable_result: bool
    suggestion: str | None


@dataclass(frozen=True)
class StatementAnalysis:
    total_bullets: int
    with_measurable_result: int
    action_verb_rate: float
    findings: tuple[StatementFinding, ...]
    repeated_phrases: tuple[str, ...] = ()


@dataclass(frozen=True)
class ExperienceEstimate:
    total_months: int | None
    date_ranges_found: int


@dataclass(frozen=True)
class ResumeProfile:
    """Everything the scorer knows about the resume."""

    text: str
    skills: tuple[DetectedSkill, ...]
    sections: tuple[SectionResult, ...]
    statements: StatementAnalysis
    experience: ExperienceEstimate
    education_level: str
    keywords_present: frozenset[str]

    def skill_names(self) -> frozenset[str]:
        return frozenset(skill.name for skill in self.skills)

    def skill_by_name(self, name: str) -> DetectedSkill | None:
        for skill in self.skills:
            if skill.name == name:
                return skill
        return None

    def section(self, key: str) -> SectionResult | None:
        for section in self.sections:
            if section.key == key:
                return section
        return None


@dataclass(frozen=True)
class JobProfile:
    """Everything the scorer knows about the job description."""

    raw_text: str
    job_title: str | None
    company_name: str | None
    required_skills: tuple[str, ...]
    preferred_skills: tuple[str, ...]
    min_years_experience: int | None
    required_education_level: str | None
    keywords: tuple[str, ...]
    requirement_split_inferred: bool


@dataclass(frozen=True)
class SkillComparison:
    skill_name: str
    display: str
    match_status: MatchStatus
    requirement_level: RequirementLevel
    matched_via: MatchedVia | None
    evidence_snippet: str | None


@dataclass(frozen=True)
class ScoredCategory:
    key: str
    name: str
    weight: float
    points_earned: float
    points_possible: float
    explanation: str
    evidence: list[dict] = field(default_factory=list)
    recommendation: str | None = None
    limitation: str = ""


@dataclass(frozen=True)
class ScoreBreakdown:
    overall_score: int
    categories: tuple[ScoredCategory, ...]
    skill_comparisons: tuple[SkillComparison, ...]
