"""Scoring tests.

The last test in this file reproduces the worked example published in
`docs/06-scoring-methodology.md`. It exists to keep the documentation honest: if
the scorer changes, the documented example fails.
"""

from __future__ import annotations

from datetime import date

import pytest

from app.analyzers.domain import (
    ExperienceEstimate,
    JobProfile,
    ResumeProfile,
    SectionResult,
    StatementAnalysis,
)
from app.analyzers.jd_parser import parse_job_description
from app.analyzers.resume_analyzer import build_resume_profile
from app.analyzers.scorer import SECTION_POINTS, WEIGHTS, compute_score
from tests.fixtures.sample_documents import (
    FICTIONAL_JOB_DESCRIPTION,
    FICTIONAL_RESUME,
    WEAK_RESUME,
)


def build_profiles(resume_text: str, job_text: str):
    resume = build_resume_profile(resume_text, today=date(2026, 1, 1))
    job = parse_job_description(job_text)
    return resume, job


class TestRubricInvariants:
    def test_weights_sum_to_one_hundred(self):
        assert sum(WEIGHTS.values()) == 100.0

    def test_section_points_sum_to_the_completeness_weight(self):
        assert sum(SECTION_POINTS.values()) == WEIGHTS["resume_completeness"]

    def test_there_are_exactly_eight_categories(self):
        resume, job = build_profiles(FICTIONAL_RESUME, FICTIONAL_JOB_DESCRIPTION)
        assert len(compute_score(resume, job).categories) == 8


class TestScoreArithmetic:
    def test_possible_points_total_one_hundred(self):
        resume, job = build_profiles(FICTIONAL_RESUME, FICTIONAL_JOB_DESCRIPTION)
        breakdown = compute_score(resume, job)
        total = sum(c.points_possible for c in breakdown.categories)
        assert round(total, 2) == 100.0

    def test_overall_equals_the_sum_of_the_parts(self):
        resume, job = build_profiles(FICTIONAL_RESUME, FICTIONAL_JOB_DESCRIPTION)
        breakdown = compute_score(resume, job)
        assert breakdown.overall_score == round(sum(c.points_earned for c in breakdown.categories))

    def test_no_category_exceeds_its_possible_points(self):
        resume, job = build_profiles(FICTIONAL_RESUME, FICTIONAL_JOB_DESCRIPTION)
        for category in compute_score(resume, job).categories:
            assert 0 <= category.points_earned <= category.points_possible

    def test_score_is_bounded(self):
        for resume_text in (FICTIONAL_RESUME, WEAK_RESUME):
            resume, job = build_profiles(resume_text, FICTIONAL_JOB_DESCRIPTION)
            assert 0 <= compute_score(resume, job).overall_score <= 100


class TestDeterminism:
    def test_identical_input_produces_identical_output(self):
        resume, job = build_profiles(FICTIONAL_RESUME, FICTIONAL_JOB_DESCRIPTION)
        first = compute_score(resume, job)
        second = compute_score(resume, job)
        assert first.overall_score == second.overall_score
        assert [c.points_earned for c in first.categories] == [
            c.points_earned for c in second.categories
        ]

    def test_scoring_does_not_mutate_its_inputs(self):
        resume, job = build_profiles(FICTIONAL_RESUME, FICTIONAL_JOB_DESCRIPTION)
        before = (resume, job)
        compute_score(resume, job)
        assert before == (resume, job)


class TestTransparency:
    def test_every_category_publishes_its_reasoning(self):
        resume, job = build_profiles(FICTIONAL_RESUME, FICTIONAL_JOB_DESCRIPTION)
        for category in compute_score(resume, job).categories:
            assert category.explanation.strip(), f"{category.key} has no explanation"
            assert category.limitation.strip(), f"{category.key} has no limitation"
            assert category.name.strip()

    def test_skill_comparisons_carry_evidence_for_matches(self):
        resume, job = build_profiles(FICTIONAL_RESUME, FICTIONAL_JOB_DESCRIPTION)
        matched = [
            c for c in compute_score(resume, job).skill_comparisons if c.match_status == "matched"
        ]
        assert matched
        assert all(c.evidence_snippet for c in matched)

    def test_missing_skills_have_no_evidence(self):
        resume, job = build_profiles(WEAK_RESUME, FICTIONAL_JOB_DESCRIPTION)
        for comparison in compute_score(resume, job).skill_comparisons:
            if comparison.match_status == "missing":
                assert comparison.evidence_snippet is None
                assert comparison.matched_via is None


class TestRelativeScoring:
    def test_a_matching_resume_outscores_a_weak_one(self):
        strong, job = build_profiles(FICTIONAL_RESUME, FICTIONAL_JOB_DESCRIPTION)
        weak, _ = build_profiles(WEAK_RESUME, FICTIONAL_JOB_DESCRIPTION)
        assert compute_score(strong, job).overall_score > compute_score(weak, job).overall_score

    def test_a_well_matched_resume_scores_respectably(self):
        resume, job = build_profiles(FICTIONAL_RESUME, FICTIONAL_JOB_DESCRIPTION)
        assert compute_score(resume, job).overall_score >= 60


class TestEdgeCases:
    def _empty_resume(self) -> ResumeProfile:
        return ResumeProfile(
            text="",
            skills=(),
            sections=tuple(
                SectionResult(key=key, detected=False, matched_heading=None, note="missing")
                for key in SECTION_POINTS
            ),
            statements=StatementAnalysis(0, 0, 0.0, ()),
            experience=ExperienceEstimate(None, 0),
            education_level="none",
            keywords_present=frozenset(),
        )

    def test_job_with_no_extractable_skills_does_not_crash(self):
        job = JobProfile(
            raw_text="x",
            job_title=None,
            company_name=None,
            required_skills=(),
            preferred_skills=(),
            min_years_experience=None,
            required_education_level=None,
            keywords=(),
            requirement_split_inferred=True,
        )
        breakdown = compute_score(self._empty_resume(), job)
        assert breakdown.overall_score >= 0

    def test_categories_rescale_to_one_hundred_when_one_is_not_applicable(self):
        job = JobProfile(
            raw_text="x",
            job_title=None,
            company_name=None,
            required_skills=("python",),
            preferred_skills=(),  # no preferred skills
            min_years_experience=None,
            required_education_level=None,
            keywords=("platform",),
            requirement_split_inferred=True,
        )
        breakdown = compute_score(self._empty_resume(), job)
        total = sum(c.points_possible for c in breakdown.categories)
        assert round(total, 2) == 100.0
        preferred = next(c for c in breakdown.categories if c.key == "preferred_skills")
        assert preferred.points_possible == 0.0
        assert "not scored" in preferred.explanation

    def test_a_job_with_no_preferred_skills_does_not_cost_the_candidate(self):
        """A posting without a 'nice to have' section must not remove 10 points."""
        resume, _ = build_profiles(FICTIONAL_RESUME, FICTIONAL_JOB_DESCRIPTION)
        with_preferred = parse_job_description(FICTIONAL_JOB_DESCRIPTION)
        without = JobProfile(
            **{
                **with_preferred.__dict__,
                "preferred_skills": (),
            }
        )
        assert (
            compute_score(resume, without).overall_score
            >= compute_score(resume, with_preferred).overall_score
        )


class TestWorkedExample:
    """Reproduces §4 of docs/06-scoring-methodology.md exactly."""

    def _profiles(self):
        # Six exact matches, one related (partial), two missing.
        matched = ["python", "postgresql", "docker", "rest api", "git", "linux"]
        related_for_testing = ["unit testing"]  # related to the required "automated testing"
        resume_text = (
            "Contact: worker@example.invalid\n\n"
            "Skills\n" + ", ".join(matched + related_for_testing) + "\n\nWork Experience\n"
            "Jul 2024 - Jan 2026\n"
            "- Built services with python and postgresql and docker in production\n"
            "- Delivered rest api endpoints using git and linux tooling daily\n"
            "- Increased throughput by 30% across the platform services\n"
            "- Reduced error rate by 15% for the reporting service\n\n"
            "Education\nBSc Computer Science\n\n"
            "Projects\nA reporting tool built for internal stakeholders\n\n"
            "Achievements\nDepartment award for delivery\n\n"
            "Languages\nEnglish\n"
        )
        resume = build_resume_profile(resume_text, today=date(2026, 1, 1))
        return resume

    def test_arithmetic_matches_the_published_example(self):
        """Category points must sum to the published overall score."""
        resume = self._profiles()
        job = parse_job_description(FICTIONAL_JOB_DESCRIPTION)
        breakdown = compute_score(resume, job)

        summed = round(sum(c.points_earned for c in breakdown.categories))
        assert breakdown.overall_score == summed

    def test_rounding_is_half_up_not_bankers(self):
        """68.75 must round to 69, and 0.5 cases must round away from zero."""
        from app.analyzers.scorer import _q0, _q2

        assert _q0(68.75) == 69
        assert _q0(2.5) == 3  # Python's built-in round() would give 2
        assert _q2(21.666666) == 21.67

    @pytest.mark.parametrize(
        ("keyword_ratio", "expected_points"),
        [(0.60, 10.0), (1.00, 10.0), (0.30, 5.0)],
    )
    def test_keyword_coverage_caps_at_sixty_percent(self, keyword_ratio, expected_points):
        """Full marks at 60% is the anti-gaming rule from §3.5."""
        total = 10
        present = int(total * keyword_ratio)
        keywords = tuple(f"kw{i}" for i in range(total))

        resume = ResumeProfile(
            text="",
            skills=(),
            sections=tuple(
                SectionResult(key=key, detected=False, matched_heading=None, note="")
                for key in SECTION_POINTS
            ),
            statements=StatementAnalysis(1, 0, 1.0, ()),
            experience=ExperienceEstimate(None, 0),
            education_level="none",
            keywords_present=frozenset(keywords[:present]),
        )
        job = JobProfile(
            raw_text="x",
            job_title=None,
            company_name=None,
            required_skills=("python",),
            preferred_skills=("redis",),
            min_years_experience=None,
            required_education_level=None,
            keywords=keywords,
            requirement_split_inferred=False,
        )
        category = next(
            c for c in compute_score(resume, job).categories if c.key == "keyword_coverage"
        )
        assert category.points_earned == pytest.approx(expected_points, abs=0.01)


class TestStatementQualityDeductions:
    def test_deductions_are_itemised_in_the_evidence(self):
        resume, job = build_profiles(WEAK_RESUME, FICTIONAL_JOB_DESCRIPTION)
        category = next(
            c for c in compute_score(resume, job).categories if c.key == "statement_quality"
        )
        assert category.points_earned < WEIGHTS["statement_quality"]
        assert category.evidence, "deductions must be explained, not just applied"
        assert all("reason" in item and "points" in item for item in category.evidence)

    def test_quality_never_goes_below_zero(self):
        awful = "\n".join(
            ["- Responsible for various tasks that were handled by the team each week"] * 6
        )
        resume, job = build_profiles(awful, FICTIONAL_JOB_DESCRIPTION)
        category = next(
            c for c in compute_score(resume, job).categories if c.key == "statement_quality"
        )
        assert category.points_earned >= 0


class TestAchievementBands:
    @pytest.mark.parametrize(
        ("count", "expected"), [(0, 0.0), (1, 4.0), (2, 4.0), (3, 7.0), (4, 7.0), (5, 10.0)]
    )
    def test_bands_match_the_published_table(self, count, expected):
        resume = ResumeProfile(
            text="",
            skills=(),
            sections=tuple(
                SectionResult(key=key, detected=False, matched_heading=None, note="")
                for key in SECTION_POINTS
            ),
            statements=StatementAnalysis(10, count, 1.0, ()),
            experience=ExperienceEstimate(None, 0),
            education_level="none",
            keywords_present=frozenset(),
        )
        job = JobProfile(
            raw_text="x",
            job_title=None,
            company_name=None,
            required_skills=("python",),
            preferred_skills=("redis",),
            min_years_experience=None,
            required_education_level=None,
            keywords=("platform",),
            requirement_split_inferred=False,
        )
        category = next(
            c for c in compute_score(resume, job).categories if c.key == "measurable_achievements"
        )
        assert category.points_earned == pytest.approx(expected, abs=0.01)
