"""Optional migration benchmark; PyMuPDF is NOT a runtime/CI dependency.

Run only in an existing review environment with PyMuPDF installed:
python -m scripts.compare_pdf_extractors
Generates synthetic PDFs in memory and prints aggregate extraction evidence.
"""

from __future__ import annotations

import io
import json
import re
import textwrap
from collections import Counter
from pathlib import Path

import reportlab
from pypdf import PdfReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from tests.fixtures.sample_documents import FICTIONAL_RESUME, WEAK_RESUME, build_pdf


def layouts() -> dict[str, tuple[bytes, str]]:
    result = {
        "single_column": (build_pdf(FICTIONAL_RESUME), FICTIONAL_RESUME),
        "multi_page": (build_pdf(FICTIONAL_RESUME * 4), FICTIONAL_RESUME * 4),
        "weak_resume": (build_pdf(WEAK_RESUME), WEAK_RESUME),
    }
    lines = [line for line in FICTIONAL_RESUME.splitlines() if line]
    stream = io.BytesIO()
    pdf = canvas.Canvas(stream)
    pdf.setFont("Helvetica", 8)
    for col, group in enumerate((lines[:14], lines[14:])):
        y = 800
        for line in group:
            for wrapped in textwrap.wrap(line, 52):
                pdf.drawString(30 + col * 285, y, wrapped)
                y -= 13
    pdf.save()
    result["two_columns"] = stream.getvalue(), FICTIONAL_RESUME
    text = "Renée Müller — Résumé\nSkills: Python, PostgreSQL\n• Built APIs reducing latency by 40%\n• Automated 25 tests for café reporting"
    font = Path(reportlab.__file__).parent / "fonts/Vera.ttf"
    pdfmetrics.registerFont(TTFont("BenchmarkVera", str(font)))
    stream = io.BytesIO()
    pdf = canvas.Canvas(stream)
    pdf.setFont("BenchmarkVera", 12)
    for i, line in enumerate(text.splitlines()):
        pdf.drawString(36, 800 - i * 20, line)
    pdf.save()
    result["unicode_bullets"] = stream.getvalue(), text
    return result


def tokens(text: str) -> Counter:
    return Counter(re.findall(r"\w+", text.lower()))


def main() -> None:
    import pymupdf

    rows = []
    for name, (data, expected) in layouts().items():
        with pymupdf.open(stream=data, filetype="pdf") as document:
            old = "\n".join(page.get_text() for page in document)
        new = "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(data)).pages)
        wanted = tokens(expected)
        rows.append(
            {
                "layout": name,
                "expected_tokens": wanted.total(),
                "pymupdf_tokens_recovered": (tokens(old) & wanted).total(),
                "pypdf_tokens_recovered": (tokens(new) & wanted).total(),
                "same_token_order": re.findall(r"\w+", old.lower())
                == re.findall(r"\w+", new.lower()),
            }
        )
    print(json.dumps({"pymupdf_version": pymupdf.VersionBind, "cases": rows}, indent=2))


if __name__ == "__main__":
    main()
