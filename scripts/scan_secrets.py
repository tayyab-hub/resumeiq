"""Targeted secret-pattern scan. Reports locations, never matched values.

Complements dependency audits; this cannot prove that all possible secrets are absent.
"""
from __future__ import annotations
import re
import subprocess
import sys

PATTERNS = {
    "Anthropic key": r"sk-ant-[A-Za-z0-9_-]{20,}",
    "OpenAI key": r"sk-(?:proj-)?[A-Za-z0-9_-]{40,}",
    "AWS key": r"AKIA[0-9A-Z]{16}",
    "GitHub token": r"(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})",
    "Private key": r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
    "Database URL": r"postgres(?:ql)?(?:\+psycopg)?://[^\s/:]+:(?!resumeiq@|example@|test@|password@|PASSWORD@|PASS@|pass@)[^\s@]+@",
}

def main():
    tracked = subprocess.check_output(["git", "ls-files", "-z"]).decode().split("\0")
    findings = []
    for name in filter(None, tracked):
        if name.rsplit("/", 1)[-1] == ".env":
            findings.append((name, "committed .env"))
        try:
            with open(name, encoding="utf-8") as stream:
                data = stream.read()
        except (UnicodeError, OSError):
            continue
        for label, pattern in PATTERNS.items():
            if re.search(pattern, data):
                findings.append((name, label))
    if "--history" in sys.argv:
        history = subprocess.check_output(["git", "log", "-p", "--all", "--format=%H"]).decode("utf-8", errors="replace")
        for label, pattern in PATTERNS.items():
            if re.search(pattern, history):
                findings.append(("git history", label))
    for location, label in findings:
        print(f"FAIL: {label} pattern in {location}; inspect privately and rotate if genuine.")
    if findings:
        raise SystemExit(1)
    print("PASS: no configured secret patterns or tracked .env files found.")

if __name__ == "__main__":
    main()
