"""Private child-process entrypoint. No database, network, credentials or logging."""

from __future__ import annotations

import io
import json
import logging
import sys


def main() -> None:
    max_pages, max_chars, memory_mb, cpu_seconds = map(int, sys.argv[1:])
    if sys.platform == "linux":
        import resource

        ceiling = memory_mb * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (ceiling, ceiling))
        resource.setrlimit(resource.RLIMIT_CPU, (cpu_seconds, cpu_seconds))
    logging.disable(logging.CRITICAL)
    try:
        from pypdf import PdfReader

        document = PdfReader(io.BytesIO(sys.stdin.buffer.read()), strict=True)
        if document.is_encrypted:
            result = {"error": "encrypted"}
        elif not 0 < len(document.pages) <= max_pages:
            result = {"error": "limit"}
        else:
            pages: list[str] = []
            total = 0
            for page in document.pages:
                page_text = page.extract_text() or ""
                total += len(page_text)
                if total > max_chars:
                    raise MemoryError
                pages.append(page_text)
            result = {"text": "\n".join(pages)}
    except MemoryError:
        result = {"error": "limit"}
    except Exception:
        result = {"error": "corrupt"}
    sys.stdout.write(json.dumps(result, ensure_ascii=True))


if __name__ == "__main__":
    main()
