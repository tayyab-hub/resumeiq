"""Request and response models for the analysis endpoints.

These mirror `docs/05-api-contract.md`. The TypeScript types in
`frontend/src/types/index.ts` mirror these in turn.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

DISCLAIMER = (
    "This score is an internal estimate produced by ResumeIQ's published rubric. "
    "It is not a simulation of any specific employer's applicant tracking system, "
    "and a high or low score does not predict whether you will be shortlisted."
)

MatchStatus = Literal["matched", "partial", "missing"]
RequirementLevel = Literal["required", "preferred"]
Priority = Literal["high", "medium", "low"]
RecommendationSource = Literal["rule", "ai"]


class SkillMatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    skill_name: str
    match_status: MatchStatus
    requirement_level: RequirementLevel
    matched_via: str | None = None
    evidence_snippet: str | None = None


class ScoreCategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    category_key: str
    category_name: str
    weight: float
    points_earned: float
    points_possible: float
    explanation: str
    evidence: list[dict[str, Any]]
    recommendation: str | None = None
    limitation: str


class ResumeSectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    section_key: str
    detected: bool
    matched_heading: str | None = None
    note: str


class StatementFindingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    statement_text: str
    issue_codes: list[str]
    word_count: int
    has_measurable_result: bool
    suggestion: str | None = None


class StatementSummaryOut(BaseModel):
    total_bullets: int
    with_measurable_result: int
    action_verb_rate: float
    findings: list[StatementFindingOut]


class RecommendationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    priority: Priority
    source: RecommendationSource
    category: str
    title: str
    detail: str


class JobAnalysisOut(BaseModel):
    job_title: str | None = None
    company_name: str | None = None
    min_years_experience: int | None = None
    required_education_level: str | None = None
    requirement_split_inferred: bool
    required_skills: list[str]
    preferred_skills: list[str]


class SkillGroupsOut(BaseModel):
    matched: list[SkillMatchOut]
    partial: list[SkillMatchOut]
    missing: list[SkillMatchOut]


class AnalysisSummaryOut(BaseModel):
    """The list-view shape. Deliberately narrow: the history endpoint must not
    ship every full analysis payload."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    job_title: str | None = None
    overall_score: int
    created_at: datetime


class AnalysisDetailOut(BaseModel):
    id: uuid.UUID
    title: str
    resume_filename: str
    created_at: datetime

    overall_score: int
    disclaimer: str = DISCLAIMER
    evidence_warnings: list[str] = Field(default_factory=list)

    score_breakdown: list[ScoreCategoryOut]
    skills: SkillGroupsOut
    sections: list[ResumeSectionOut]
    statements: StatementSummaryOut
    job_analysis: JobAnalysisOut
    recommendations: list[RecommendationOut]

    ai_status: Literal["available", "unavailable"]
    ai_reason_code: str | None = None
    ai_message: str


class AnalysisListOut(BaseModel):
    items: list[AnalysisSummaryOut]
    total: int
    page: int
    page_size: int
    has_next: bool


class RenameAnalysisRequest(BaseModel):
    title: str = Field(min_length=1, max_length=120)


class ScoreTrendPoint(BaseModel):
    date: str
    score: int


class MissingSkillCount(BaseModel):
    skill: str
    occurrences: int


class DashboardStatsOut(BaseModel):
    total_analyses: int
    average_score: float | None
    best_score: int | None
    analyses_this_month: int
    score_trend: list[ScoreTrendPoint]
    common_missing_skills: list[MissingSkillCount]
