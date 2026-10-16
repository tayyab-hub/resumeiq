"""Fictional test documents.

Every fixture here describes an invented person. No real resume, no real email
address, and no real company's proprietary text appears anywhere in this
repository.
"""

from __future__ import annotations

FICTIONAL_RESUME = """\
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

# Deliberately weak: no metrics, no action verbs, generic phrasing throughout.
WEAK_RESUME = """\
Sam Carter
sam.carter@example.invalid

Experience
Assistant, Example Company
- Responsible for maintaining the company website and its content
- Worked on various tasks assigned by the manager each week
- Helped with the reporting process and other duties as required
- Was involved in the migration project that was managed by the senior team
- Duties included answering questions from staff about the internal system

Education
Diploma in Information Technology
"""

FICTIONAL_JOB_DESCRIPTION = """\
Junior Backend Developer

We are hiring a Junior Backend Developer to join our platform team. You will build and
maintain services that power our customer-facing products.

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

You will collaborate with product and design stakeholders in an agile environment,
contribute to architecture discussions, and take part in incident response rotations.
"""

MINIMAL_JOB_DESCRIPTION = (
    "We need a developer who can write Python and SQL, work with Docker containers, "
    "and build REST APIs for our platform team. You will collaborate with stakeholders "
    "and contribute to code review. Experience with Linux is expected for this role, "
    "and you should be comfortable in an agile environment with regular deployments."
)


def build_pdf(text: str) -> bytes:
    """Generate a real, text-layer PDF from a string.

    Generated rather than committed as a binary so the fixtures are readable in
    a diff and contain no hidden metadata.
    """
    import io
    import textwrap

    from reportlab.pdfgen.canvas import Canvas

    stream = io.BytesIO()
    canvas = Canvas(stream, pagesize=(595, 842), invariant=1)
    canvas.setFont("Helvetica", 9)
    y = 800
    for line in text.splitlines():
        for wrapped in textwrap.wrap(line, width=105) or [""]:
            if y < 45:
                canvas.showPage()
                canvas.setFont("Helvetica", 9)
                y = 800
            canvas.drawString(40, y, wrapped)
            y -= 12
    canvas.save()
    return stream.getvalue()


def build_image_only_pdf() -> bytes:
    import io

    from pypdf import PdfWriter

    writer = PdfWriter()
    writer.add_blank_page(595, 842)
    stream = io.BytesIO()
    writer.write(stream)
    return stream.getvalue()
