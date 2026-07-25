"""Importing this package registers every table on the shared metadata."""

from app.models.analysis import (
    Analysis,
    JobDescription,
    Recommendation,
    ResumeSection,
    ScoreCategory,
    SkillMatch,
    StatementFinding,
)
from app.models.user import RefreshToken, User

__all__ = [
    "Analysis",
    "JobDescription",
    "Recommendation",
    "RefreshToken",
    "ResumeSection",
    "ScoreCategory",
    "SkillMatch",
    "StatementFinding",
    "User",
]
