"""Generate the public read-only sample from the real engine, using fictional fixtures.

Run from backend: python -m scripts.export_sample [--check]
No configured database or external AI provider is used.
"""

from __future__ import annotations

import json
import sys
import uuid
from datetime import UTC, date, datetime
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database.base import Base
from app.models.user import User
from app.services.analysis_service import persist_analysis, run_analysis
from app.services.response_builder import to_detail
from tests.fixtures.sample_documents import FICTIONAL_JOB_DESCRIPTION, FICTIONAL_RESUME, build_pdf


def sample_report() -> dict:
    pdf = build_pdf(FICTIONAL_RESUME)
    resume, job, breakdown, text = run_analysis(
        pdf, FICTIONAL_JOB_DESCRIPTION, today=date(2026, 10, 15)
    )
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        user = User(
            full_name="Fictional sample",
            email="sample@example.com",
            password_hash="login-disabled",
            is_active=False,
        )
        db.add(user)
        db.flush()
        report = persist_analysis(
            db,
            user_id=user.id,
            title="Jordan Reyes · Junior Backend Developer",
            resume_filename="fictional-resume.pdf",
            resume_text=text,
            store_resume_text=False,
            resume=resume,
            job=job,
            breakdown=breakdown,
            job_title=job.job_title,
            company_name="Fictional employer",
            raw_job_description=FICTIONAL_JOB_DESCRIPTION,
        )
        report.ai_reason_code = "not_configured"
        result = to_detail(report).model_dump(mode="json")
        result["id"] = str(uuid.UUID("00000000-0000-4000-8000-000000000001"))
        result["created_at"] = datetime(2026, 10, 15, tzinfo=UTC).isoformat()
    engine.dispose()
    return result


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    target = root / "frontend/src/data/sample-analysis.json"
    rendered = json.dumps(sample_report(), indent=2, ensure_ascii=False) + "\n"
    if "--check" in sys.argv:
        if target.read_text(encoding="utf-8") != rendered:
            raise SystemExit("Public sample differs from the deterministic engine; regenerate it.")
        print("Public sample matches the deterministic engine.")
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(rendered, encoding="utf-8")
    samples = root / "docs/samples"
    samples.mkdir(parents=True, exist_ok=True)
    (samples / "fictional-resume.pdf").write_bytes(build_pdf(FICTIONAL_RESUME))
    (samples / "fictional-job.txt").write_text(FICTIONAL_JOB_DESCRIPTION, encoding="utf-8")
    print("Generated public sample and fictional demonstration documents.")


if __name__ == "__main__":
    main()
