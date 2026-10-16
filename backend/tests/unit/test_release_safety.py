from __future__ import annotations

import copy
import io
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from types import SimpleNamespace

import pytest
from pypdf import PdfReader, PdfWriter

from app.analyzers.jd_parser import parse_job_description
from app.analyzers.pdf_extractor import extract_text
from app.analyzers.resume_analyzer import build_resume_profile
from app.analyzers.scorer import compute_score
from app.core.config import Settings, settings
from app.core.exceptions import ExtractionError
from app.security.password import hash_password, verify_password
from app.security.rate_limit import RateLimiter
from app.services import ai_service
from tests.fixtures.sample_documents import FICTIONAL_JOB_DESCRIPTION, FICTIONAL_RESUME, build_pdf

VALID_AI = {
    "summary_suggestion": "Use your own evidence.",
    "statement_rewrites": [],
    "skill_guidance": [],
    "interview_points": [],
    "priority_actions": [],
}


def test_password_suffix_never_ignored():
    digest = hash_password("a1" + "x" * 70)
    assert not verify_password("a1" + "x" * 70 + "different", digest)
    with pytest.raises(ValueError, match="72 UTF-8 bytes"):
        hash_password("a1" + "é" * 36)


def test_rate_limit_reserves_concurrent_attempts_atomically():
    limiter = RateLimiter()
    with ThreadPoolExecutor(max_workers=12) as pool:
        results = list(pool.map(lambda _: limiter.consume("key", 5, 60), range(40)))
    assert results.count(None) == 5


def test_rate_limit_fails_closed_at_key_capacity():
    limiter = RateLimiter()
    limiter.max_keys = 2
    assert limiter.consume("one", 2, 60) is None
    assert limiter.consume("two", 2, 60) is None
    assert limiter.consume("three", 2, 60) == 60


@pytest.mark.parametrize(
    "overrides",
    [
        {"database_url": "sqlite:///bad.db"},
        {"database_url": "postgresql+psycopg://user:example@db/resumeiq"},
        {"cors_origins": "*"},
        {"cors_origins": "http://insecure.example"},
        {"debug": True},
        {"bcrypt_rounds": 4},
    ],
)
def test_production_configuration_fails_closed(overrides):
    values = {
        "environment": "production",
        "debug": False,
        "bcrypt_rounds": 12,
        "jwt_secret": "fictional-production-test-secret-1234567890",
        "database_url": "postgresql+psycopg://user:example@db/resumeiq?sslmode=require",
        "cors_origins": "https://resumeiq.example",
    }
    values.update(overrides)
    with pytest.raises(RuntimeError):
        Settings(_env_file=None, **values).assert_production_ready()


def test_ai_requires_explicit_opt_in():
    assert not Settings(_env_file=None, ai_api_key="fictional", ai_model="fictional").ai_enabled


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("statement_rewrites", [{"original": 123, "improved": "x", "why": "x"}]),
        ("statement_rewrites", [{"improved": "x"}]),
        ("skill_guidance", [{"skill": "Python", "advice": ["x"]}]),
        ("skill_guidance", ["not an object"]),
        ("interview_points", [42]),
        ("interview_points", ["x"] * 6),
        ("summary_suggestion", "x" * 2001),
        ("priority_actions", [{"priority": "urgent", "title": "x", "detail": "x"}]),
        ("unexpected", "value"),
    ],
)
def test_ai_rejects_malformed_nested_output(key, value):
    payload = copy.deepcopy(VALID_AI)
    payload[key] = value
    assert not ai_service._validate(payload)


def test_ai_strict_schema_accepts_bounded_output():
    assert ai_service._validate(VALID_AI)
    assert ai_service.to_recommendation_rows(VALID_AI, 0)


def test_ai_response_size_is_bounded():
    response = SimpleNamespace(content=[SimpleNamespace(type="text", text="x" * 65537)])
    assert ai_service._extract_json(response) is None


def test_ai_payload_excludes_free_form_document_text():
    text = (
        FICTIONAL_RESUME + "\n- Responsible for emailing secret@example.com about privateproject\n"
    )
    resume = build_resume_profile(text, today=date(2026, 10, 15))
    job = parse_job_description(FICTIONAL_JOB_DESCRIPTION)
    payload = json.dumps(ai_service.build_prompt_payload(resume, job, compute_score(resume, job)))
    for private in ["secret@example.com", "privateproject", "Jordan", "Northwind", "jordan.reyes"]:
        assert private not in payload


@pytest.mark.parametrize("failure", [TimeoutError, RuntimeError])
def test_ai_provider_error_is_graceful_without_real_calls(monkeypatch, failure):
    import anthropic

    monkeypatch.setattr(settings, "ai_enabled_opt_in", True)
    monkeypatch.setattr(settings, "ai_api_key", "fictional-key")
    monkeypatch.setattr(settings, "ai_model", "fictional-model")

    def unavailable(**_):
        raise failure("private data must not be logged")

    monkeypatch.setattr(anthropic, "Anthropic", unavailable)
    resume = build_resume_profile(FICTIONAL_RESUME)
    job = parse_job_description(FICTIONAL_JOB_DESCRIPTION)
    payload, reason = ai_service.generate_recommendations(resume, job, compute_score(resume, job))
    assert payload is None
    assert reason == ("timeout" if failure is TimeoutError else "provider_error")


def test_pdf_page_limit_and_encryption():
    writer = PdfWriter()
    for _ in range(11):
        writer.add_blank_page(595, 842)
    stream = io.BytesIO()
    writer.write(stream)
    with pytest.raises(ExtractionError) as exc:
        extract_text(stream.getvalue())
    assert exc.value.code == "RESUME_RESOURCE_LIMIT"
    writer = PdfWriter()
    writer.add_page(PdfReader(io.BytesIO(build_pdf(FICTIONAL_RESUME))).pages[0])
    writer.encrypt("fictional")
    stream = io.BytesIO()
    writer.write(stream)
    with pytest.raises(ExtractionError) as exc:
        extract_text(stream.getvalue())
    assert exc.value.code == "RESUME_ENCRYPTED"


def test_pdf_text_limit(monkeypatch):
    monkeypatch.setattr(settings, "pdf_max_text_chars", 200)
    with pytest.raises(ExtractionError) as exc:
        extract_text(build_pdf(FICTIONAL_RESUME))
    assert exc.value.code == "RESUME_RESOURCE_LIMIT"


def test_pdf_timeout_is_safe_and_releases_slot(monkeypatch):
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired("pdf worker", 10)

    monkeypatch.setattr(subprocess, "run", timeout)
    for _ in range(2):
        with pytest.raises(ExtractionError) as exc:
            extract_text(b"%PDF-1.7")
        assert exc.value.code == "RESUME_RESOURCE_LIMIT"


def test_no_bullets_do_not_earn_perfect_statement_quality():
    resume = build_resume_profile("Skills\nPython\nEducation\nDiploma")
    breakdown = compute_score(resume, parse_job_description(FICTIONAL_JOB_DESCRIPTION))
    category = next(c for c in breakdown.categories if c.key == "statement_quality")
    assert category.points_earned == category.points_possible == 0


def test_contacts_and_skill_lists_are_not_achievement_statements():
    from app.analyzers.statement_analyzer import analyse_statements

    result = analyse_statements(FICTIONAL_RESUME)
    assert result.total_bullets == 7
    assert result.with_measurable_result == 4
    assert all("@" not in item.text for item in result.findings)


def test_unmarked_action_statements_are_still_recognised():
    from app.analyzers.statement_analyzer import analyse_statements

    result = analyse_statements("Built Python services supporting 12000 requests per day")
    assert result.total_bullets == result.with_measurable_result == 1


def test_preferred_only_and_duplicate_synonyms_are_consistent():
    resume = build_resume_profile(FICTIONAL_RESUME, today=date(2026, 10, 15))
    job = parse_job_description("Nice to have:\nPython, Python, PostgreSQL, Postgres")
    result = compute_score(resume, job)
    assert not job.required_skills
    assert len(job.preferred_skills) == 2
    assert result == compute_score(resume, job)
    assert abs(sum(c.points_possible for c in result.categories) - 100) < 0.05
