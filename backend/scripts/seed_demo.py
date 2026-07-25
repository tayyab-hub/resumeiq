"""Seed a demonstration account.

All data created here is FICTIONAL. The resume describes an invented person at
invented companies. No real person's resume, email address, or employer appears
anywhere in this repository.

Usage (from the backend directory):

    python -m scripts.seed_demo

The account it creates is intended for screenshots and interview demos, so the
project can be shown without uploading anyone's real resume.
"""

from __future__ import annotations

import sys
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.analyzers.jd_parser import parse_job_description
from app.analyzers.resume_analyzer import build_resume_profile
from app.analyzers.scorer import compute_score
from app.database.session import SessionLocal
from app.repositories import user_repository as users
from app.security.password import hash_password
from app.services.analysis_service import persist_analysis

DEMO_EMAIL = "demo@resumeiq.example"
DEMO_PASSWORD = "demo account 2026"
DEMO_NAME = "Demo User"

# --- Fictional demonstration data -----------------------------------------

DEMO_RESUME = """\
Jordan Reyes
jordan.reyes@example.invalid | +44 7700 900123 | github.com/example-jordan

Professional Summary
Backend developer with hands-on experience building and maintaining Python web services.

Skills
Python, JavaScript, PostgreSQL, Docker, Git, REST APIs, pytest, Linux

Work Experience
Junior Backend Developer, Northwind Systems (fictional)
Jan 2023 - Present
- Built REST APIs in Python and Flask serving 12000 requests per day
- Reduced average query time by 40% by adding indexes to PostgreSQL tables
- Automated the deployment pipeline with Docker, cutting release time from 2 hours to 20 minutes
- Wrote unit tests with pytest, raising coverage from 34% to 81%

Software Support Assistant, Cobalt Retail (fictional)
Jun 2022 - Dec 2022
- Responsible for maintaining the company website
- Worked on internal reporting tools
- Helped with customer queries about the online ordering system

Education
BSc Computer Science, Riverbank University (fictional), 2022

Projects
Expense Tracker - a Flask and PostgreSQL application with JWT authentication

Certifications
AWS Certified Cloud Practitioner (fictional credential)

Languages
English, Spanish
"""

DEMO_JOBS = [
    (
        "Junior Backend Developer — Vertex Labs",
        """Junior Backend Developer

We are hiring a Junior Backend Developer to join our platform team.

Requirements:
- 2+ years of experience building backend web services
- Strong Python skills
- Experience with PostgreSQL and writing SQL queries
- Familiarity with Docker and containerised deployment
- Experience designing and consuming REST APIs
- Comfortable with Git and code review workflows
- Working knowledge of Linux
- Experience writing unit tests
- Bachelor's degree in Computer Science or equivalent practical experience

Nice to have:
- Exposure to Kubernetes
- Experience with Redis or another caching layer

You will collaborate with product and design stakeholders in an agile environment.""",
    ),
    (
        "Full Stack Engineer — Harbour Digital",
        """Full Stack Engineer

Requirements:
- 3+ years building web applications end to end
- Proficiency in TypeScript and React
- Backend experience with Node.js or Python
- Strong SQL and database design skills
- Familiarity with CI/CD pipelines and automated testing
- Experience with cloud platforms, ideally AWS
- Bachelor's degree or equivalent experience

Preferred:
- Experience with GraphQL
- Exposure to Kubernetes and infrastructure as code

You will work closely with designers on accessibility and responsive layouts, and take part
in code review and architecture discussions across the platform team.""",
    ),
    (
        "Data Analyst — Meridian Insights",
        """Data Analyst

Requirements:
- 2+ years in an analytical role
- Advanced SQL
- Strong Excel skills including pivot tables
- Experience with a visualisation tool such as Tableau or Power BI
- Python for data analysis, particularly pandas
- Excellent communication skills for presenting findings to stakeholders
- Bachelor's degree in a numerate discipline

Nice to have:
- Exposure to machine learning
- Experience building ETL pipelines""",
    ),
]


def seed(db: Session) -> None:
    existing = users.get_by_email(db, DEMO_EMAIL)
    if existing is not None:
        print(f"Demo account {DEMO_EMAIL} already exists. Nothing to do.")
        return

    user = users.create(
        db,
        email=DEMO_EMAIL,
        full_name=DEMO_NAME,
        password_hash=hash_password(DEMO_PASSWORD),
    )
    print(f"Created demo account: {DEMO_EMAIL} / {DEMO_PASSWORD}")

    resume = build_resume_profile(DEMO_RESUME, today=date(2026, 1, 1))

    for index, (title, job_text) in enumerate(DEMO_JOBS):
        job = parse_job_description(job_text)
        breakdown = compute_score(resume, job)

        analysis = persist_analysis(
            db,
            user_id=user.id,
            title=title,
            resume_filename="demonstration-resume.pdf",
            resume_text=DEMO_RESUME,
            store_resume_text=False,  # matches the product default
            resume=resume,
            job=job,
            breakdown=breakdown,
            job_title=job.job_title,
            company_name=title.split("—")[-1].strip(),
            raw_job_description=job_text,
        )

        # Spread the analyses over time so the dashboard trend chart has shape.
        analysis.created_at = analysis.created_at - timedelta(days=(len(DEMO_JOBS) - index) * 9)
        db.commit()

        print(f"  Seeded '{title}' — score {breakdown.overall_score}/100")

    print("\nDemonstration data seeded. Every record above describes a fictional person.")


def main() -> int:
    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
