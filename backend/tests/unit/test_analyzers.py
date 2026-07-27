"""Unit tests for the analysis engine.

These need no database and no fixtures beyond a string, which is the payoff for
keeping `analyzers/` pure.
"""

from __future__ import annotations

from datetime import date

import pytest

from app.analyzers.experience_parser import (
    detect_education_level,
    estimate_experience_months,
    extract_required_education,
    extract_required_years,
)
from app.analyzers.jd_parser import parse_job_description
from app.analyzers.pdf_extractor import extract_text, validate_pdf_bytes
from app.analyzers.resume_analyzer import build_resume_profile
from app.analyzers.section_detector import detect_sections
from app.analyzers.skill_extractor import extract_skill_names, extract_skills
from app.analyzers.statement_analyzer import analyse_statements
from app.analyzers.text_utils import extract_bullets, meaningful_character_count, normalise_text
from app.core.error_codes import (
    RESUME_CORRUPT,
    RESUME_EMPTY,
    RESUME_INVALID_TYPE,
    RESUME_NO_TEXT_LAYER,
)
from app.core.exceptions import ExtractionError
from tests.fixtures.sample_documents import (
    FICTIONAL_JOB_DESCRIPTION,
    FICTIONAL_RESUME,
    WEAK_RESUME,
    build_image_only_pdf,
    build_pdf,
)

# --- text_utils ------------------------------------------------------------


class TestTextNormalisation:
    def test_collapses_runs_of_whitespace(self):
        assert normalise_text("hello     world") == "hello world"

    def test_preserves_paragraph_boundaries(self):
        result = normalise_text("Skills\n\nPython and SQL")
        assert "\n\n" in result

    def test_rejoins_words_hyphenated_across_a_line_break(self):
        assert "development" in normalise_text("I enjoy develop-\nment work")

    def test_normalises_every_bullet_glyph_to_one_marker(self):
        result = normalise_text("• first item\n▪ second item\n‣ third item")
        assert result.count("- ") == 3

    def test_empty_input_is_safe(self):
        assert normalise_text("") == ""

    def test_meaningful_character_count_ignores_punctuation_and_space(self):
        assert meaningful_character_count("  ... --- \n ") == 0
        assert meaningful_character_count("abc123") == 6

    def test_extract_bullets_skips_headings(self):
        text = "Experience\n- Built a service that processed orders every day\nSkills"
        bullets = extract_bullets(text)
        assert len(bullets) == 1
        assert bullets[0].startswith("Built a service")


# --- pdf_extractor ---------------------------------------------------------


class TestPdfExtraction:
    def test_extracts_text_from_a_real_pdf(self):
        text = extract_text(build_pdf(FICTIONAL_RESUME))
        assert "Jordan Reyes" in text
        assert len(text) > 200

    def test_rejects_empty_input(self):
        with pytest.raises(ExtractionError) as exc:
            extract_text(b"")
        assert exc.value.code == RESUME_EMPTY.code

    def test_rejects_a_non_pdf_renamed_as_pdf(self):
        # The magic-byte check is what makes renaming an executable useless.
        with pytest.raises(ExtractionError) as exc:
            extract_text(b"MZ\x90\x00 this is a windows executable")
        assert exc.value.code == RESUME_INVALID_TYPE.code

    def test_rejects_a_truncated_pdf(self):
        with pytest.raises(ExtractionError) as exc:
            extract_text(b"%PDF-1.7\n truncated garbage that is not a document")
        assert exc.value.code == RESUME_CORRUPT.code

    def test_reports_a_scanned_pdf_specifically(self):
        with pytest.raises(ExtractionError) as exc:
            extract_text(build_image_only_pdf())
        assert exc.value.code == RESUME_NO_TEXT_LAYER.code

    def test_scanned_pdf_message_tells_the_user_what_to_do(self):
        with pytest.raises(ExtractionError) as exc:
            extract_text(build_image_only_pdf())
        assert "Word or Google Docs" in exc.value.spec.next_step

    def test_no_error_message_leaks_internals(self):
        for payload in (b"", b"MZ\x90", b"%PDF-1.7 broken"):
            with pytest.raises(ExtractionError) as exc:
                extract_text(payload)
            combined = " ".join(
                [exc.value.spec.what, exc.value.spec.why, exc.value.spec.next_step]
            )
            assert ".py" not in combined
            assert "Traceback" not in combined
            assert "fitz" not in combined.lower()

    def test_validate_accepts_a_pdf_header(self):
        validate_pdf_bytes(b"%PDF-1.4 rest of file")


# --- section_detector ------------------------------------------------------


class TestSectionDetection:
    def test_reports_all_nine_sections_always(self):
        sections = detect_sections("nothing useful here")
        assert len(sections) == 9

    def test_detects_standard_sections_in_a_full_resume(self):
        sections = {s.key: s for s in detect_sections(FICTIONAL_RESUME)}
        for key in ("summary", "skills", "experience", "education", "projects", "languages"):
            assert sections[key].detected, f"{key} should have been detected"

    def test_records_absence_explicitly_rather_than_omitting_it(self):
        sections = {s.key: s for s in detect_sections("Experience\n- did a thing for a while")}
        assert sections["projects"].detected is False
        assert sections["projects"].note

    def test_detects_contact_from_content_without_a_heading(self):
        sections = {s.key: s for s in detect_sections("Ada Lovelace\nada@example.invalid")}
        assert sections["contact"].detected is True

    def test_returns_the_heading_that_triggered_detection(self):
        sections = {s.key: s for s in detect_sections("Employment History\n- built things daily")}
        assert sections["experience"].matched_heading == "Employment History"

    @pytest.mark.parametrize("heading", ["SKILLS", "Technical Skills", "Core Competencies"])
    def test_tolerates_case_and_synonyms(self, heading):
        sections = {s.key: s for s in detect_sections(f"{heading}\nPython, SQL")}
        assert sections["skills"].detected is True

    def test_a_sentence_containing_a_section_word_is_not_a_heading(self):
        text = "I have a great deal of experience in building maintainable software systems."
        sections = {s.key: s for s in detect_sections(text)}
        assert sections["experience"].detected is False


# --- skill_extractor -------------------------------------------------------


class TestSkillExtraction:
    def test_finds_skills_across_the_whole_document(self):
        names = extract_skill_names(FICTIONAL_RESUME)
        assert {"python", "postgresql", "docker", "git", "rest api"} <= set(names)

    @pytest.mark.parametrize("variant", ["PostgreSQL", "Postgres", "postgres", "psql"])
    def test_aliases_resolve_to_one_canonical_skill(self, variant):
        assert "postgresql" in extract_skill_names(f"Worked with {variant} databases")

    def test_single_letter_skill_does_not_match_inside_a_word(self):
        # Without word boundaries, "R" matches "Requirements" everywhere.
        assert "r" not in extract_skill_names("Requirements gathering and reporting")

    def test_go_does_not_match_google(self):
        assert "go" not in extract_skill_names("Used Google Analytics daily")

    def test_c_does_not_match_cpp(self):
        names = extract_skill_names("Experienced in C++ development")
        assert "c++" in names
        assert "c" not in names

    def test_records_whether_a_skill_appears_in_the_experience_section(self):
        skills = extract_skills("Python and Redis", experience_text="Python only")
        by_name = {s.name: s for s in skills}
        assert by_name["python"].in_experience is True
        assert by_name["redis"].in_experience is False

    def test_evidence_snippet_is_returned_for_every_match(self):
        for skill in extract_skills(FICTIONAL_RESUME):
            assert skill.snippet


# --- experience_parser -----------------------------------------------------


class TestExperienceParsing:
    def test_reads_a_month_year_range(self):
        result = estimate_experience_months("Jan 2022 - Jan 2023", today=date(2026, 1, 1))
        assert result.total_months == 12

    def test_reads_an_open_ended_range_against_the_injected_date(self):
        result = estimate_experience_months("Jan 2025 - Present", today=date(2026, 1, 1))
        assert result.total_months == 12

    def test_reads_a_numeric_range(self):
        result = estimate_experience_months("03/2022 - 03/2024", today=date(2026, 1, 1))
        assert result.total_months == 24

    def test_reads_a_bare_year_range_without_inflating_it(self):
        # Ambiguous data must understate, never overstate, a candidate's
        # experience: "2021 - 2023" is 24 months, not 35.
        result = estimate_experience_months("2021 - 2023", today=date(2026, 1, 1))
        assert result.total_months == 24

    def test_overlapping_roles_are_not_double_counted(self):
        text = "Jan 2022 - Jan 2023\nJun 2022 - Jan 2023"
        assert estimate_experience_months(text, today=date(2026, 1, 1)).total_months == 12

    def test_absent_dates_return_none_rather_than_zero(self):
        result = estimate_experience_months("No dates anywhere in this resume")
        assert result.total_months is None
        assert result.date_ranges_found == 0

    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("PhD in Computer Science", "doctorate"),
            ("MSc Data Science", "master"),
            ("Bachelor of Science", "bachelor"),
            ("BSc Computer Science", "bachelor"),
            ("Diploma in IT", "diploma"),
            ("AWS Certified Practitioner", "certificate"),
            ("No qualifications listed", "none"),
        ],
    )
    def test_detects_education_level(self, text, expected):
        assert detect_education_level(text) == expected

    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("3+ years of experience required", 3),
            ("at least 5 years in a similar role", 5),
            ("minimum of 2 years", 2),
            ("two years of experience", 2),
            ("no experience requirement stated", None),
        ],
    )
    def test_extracts_required_years(self, text, expected):
        assert extract_required_years(text) == expected

    def test_takes_the_lowest_stated_requirement(self):
        assert extract_required_years("3+ years required, 5+ years preferred") == 3

    def test_extract_required_education_returns_none_when_unstated(self):
        assert extract_required_education("We want a great developer") is None


# --- statement_analyzer ----------------------------------------------------


class TestStatementAnalysis:
    def test_flags_a_generic_duty_statement(self):
        result = analyse_statements("- Responsible for maintaining the company website")
        codes = result.findings[0].issue_codes
        assert "GENERIC_PHRASING" in codes
        assert "NO_ACTION_VERB" in codes
        assert "NO_METRIC" in codes

    def test_does_not_flag_a_strong_quantified_statement(self):
        text = "- Reduced page load time by 40% by adding image lazy-loading"
        result = analyse_statements(text)
        assert result.findings == ()
        assert result.with_measurable_result == 1

    def test_flags_an_over_long_statement_with_its_word_count(self):
        long_bullet = "- Built " + " ".join(["a really important system component"] * 8)
        result = analyse_statements(long_bullet)
        finding = result.findings[0]
        assert "TOO_LONG" in finding.issue_codes
        assert finding.word_count > 35

    def test_flags_passive_voice(self):
        result = analyse_statements("- The migration was managed by the senior engineering team")
        assert "PASSIVE_VOICE" in result.findings[0].issue_codes

    def test_flags_a_phrase_repeated_three_times(self):
        text = "\n".join(["- Worked on the reporting system for the team"] * 3)
        result = analyse_statements(text)
        assert result.repeated_phrases
        assert any("REPETITION" in f.issue_codes for f in result.findings)

    def test_computes_the_action_verb_rate(self):
        text = (
            "- Built a reporting service used by the finance team\n"
            "- Responsible for the weekly data export process\n"
        )
        assert analyse_statements(text).action_verb_rate == 0.5

    def test_a_year_is_not_counted_as_a_measurable_achievement(self):
        result = analyse_statements("- Joined the engineering team in 2023 and stayed there")
        assert result.with_measurable_result == 0

    def test_suggestions_never_invent_a_number(self):
        """The anti-fabrication guarantee, asserted directly."""
        result = analyse_statements(WEAK_RESUME)
        assert result.findings
        for finding in result.findings:
            if finding.suggestion:
                assert not any(char.isdigit() for char in finding.suggestion.replace("35", "")), (
                    f"suggestion introduced a figure: {finding.suggestion}"
                )

    def test_empty_input_is_safe(self):
        result = analyse_statements("")
        assert result.total_bullets == 0
        assert result.findings == ()


# --- jd_parser -------------------------------------------------------------


class TestJobDescriptionParsing:
    def test_splits_required_from_preferred(self):
        job = parse_job_description(FICTIONAL_JOB_DESCRIPTION)
        assert "python" in job.required_skills
        assert "kubernetes" in job.preferred_skills
        assert job.requirement_split_inferred is False

    def test_falls_back_to_all_required_and_discloses_it(self):
        job = parse_job_description(
            "We need someone who knows Python and Docker to build our platform services "
            "and work with the wider engineering team on delivery."
        )
        assert job.requirement_split_inferred is True
        assert job.preferred_skills == ()

    def test_extracts_experience_and_education_requirements(self):
        job = parse_job_description(FICTIONAL_JOB_DESCRIPTION)
        assert job.min_years_experience == 2
        assert job.required_education_level == "bachelor"

    def test_excludes_boilerplate_from_keywords(self):
        job = parse_job_description(
            FICTIONAL_JOB_DESCRIPTION + "\nWe are an equal opportunity employer."
        )
        assert "opportunity" not in job.keywords

    def test_keywords_exclude_skills_to_avoid_double_counting(self):
        job = parse_job_description(FICTIONAL_JOB_DESCRIPTION)
        assert not set(job.keywords) & set(job.required_skills)

    def test_captures_meaningful_domain_keywords(self):
        job = parse_job_description(FICTIONAL_JOB_DESCRIPTION)
        assert "platform" in job.keywords

    def test_is_deterministic(self):
        first = parse_job_description(FICTIONAL_JOB_DESCRIPTION)
        second = parse_job_description(FICTIONAL_JOB_DESCRIPTION)
        assert first == second

    @pytest.mark.parametrize(
        "first_line",
        [
            "## Backend Developer",
            "# Backend Developer",
            "**Backend Developer**",
            "- Backend Developer",
            "=== Backend Developer ===",
            "  Backend Developer  ",
        ],
    )
    def test_strips_markdown_decoration_from_the_detected_title(self, first_line):
        """Postings pasted from Markdown must not keep their heading markers.

        Regression: a posting beginning "## Backend Developer" was stored and
        displayed with the hashes intact.
        """
        job = parse_job_description(
            f"{first_line}\n\n"
            "Requirements:\n"
            "- Strong Python skills and experience with PostgreSQL databases\n"
            "- Familiarity with Docker, REST APIs, Git and Linux environments\n"
            "- Experience writing unit tests for backend services in production\n"
        )
        assert job.job_title == "Backend Developer"

    def test_strips_decoration_from_an_explicit_title(self):
        job = parse_job_description(
            "Some posting body that is long enough to satisfy the parser and "
            "mentions Python, Docker and PostgreSQL for the platform team.",
            job_title="## Senior Engineer",
        )
        assert job.job_title == "Senior Engineer"


# --- resume_analyzer -------------------------------------------------------


class TestResumeProfile:
    def test_builds_a_complete_profile(self):
        profile = build_resume_profile(FICTIONAL_RESUME, today=date(2026, 1, 1))
        assert profile.skills
        assert len(profile.sections) == 9
        assert profile.education_level == "bachelor"
        assert profile.statements.total_bullets > 0
        assert profile.keywords_present
