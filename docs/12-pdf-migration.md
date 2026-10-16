# PDF extraction and licensing

Decision and executed comparison: 15 October 2026.

PyMuPDF offers AGPL/commercial licensing. MIT on surrounding code does not override third-party obligations; public source or portfolio intent is not a blanket licensing exemption. See [upstream licensing information](https://pymupdf.readthedocs.io/en/latest/about.html).

Runtime extraction now uses pypdf 6.20.1, BSD-3-Clause. PyMuPDF was removed from runtime/development requirements and used only from the pre-existing local review environment for this comparison. Preserve third-party notices in distributions. This is a technical dependency decision, not legal advice. [pypdf license](https://github.com/py-pdf/pypdf/blob/main/LICENSE) · [extraction limitations](https://pypdf.readthedocs.io/en/stable/user/extract-text.html)

`python -m scripts.compare_pdf_extractors` generated fictional PDFs with ReportLab and compared PyMuPDF 1.28.0 with pypdf 6.20.1. Recovery compares Unicode word-token counts against fixture text; order compares the two outputs.

| Layout | Expected tokens | PyMuPDF recovered | pypdf recovered | Same token order |
|---|---:|---:|---:|---|
| Single column | 157 | 157 | 157 | Yes |
| Multiple pages | 628 | 628 | 628 | Yes |
| Weak resume | 67 | 67 | 67 | Yes |
| Two columns | 157 | 157 | 157 | Yes |
| Unicode name/bullets | 18 | 18 | 18 | Yes |

No word loss occurred in this small controlled corpus. It is not a representative accuracy study. Complex reading order, ligatures, fonts, wrapping and unusual encodings remain limitations. No OCR is provided. Dedicated tests cover corrupt, encrypted, image-only, oversized, excessive-page/text and timeout behavior.

The parent bounds uploads and enforces one worker plus a 10-second timeout. The child gets a minimal environment without app credentials, limits pages/text, and on Linux applies 256 MB address-space/CPU limits before parsing. Windows has no Linux address-space enforcement. Multipart uploads may spool to temporary storage; no exclusively-in-memory handling claim is made.
