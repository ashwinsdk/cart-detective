#!/usr/bin/env python3
"""
Simple secret scanner for Cart Detective.
Scans repository files for committed API keys, private keys, and credentials.
"""

import os
import re
import sys
from pathlib import Path

SECRET_PATTERNS = [
    (re.compile(r"gsk_[a-zA-Z0-9]{20,}", re.IGNORECASE), "Groq API key"),
    (re.compile(r"AIza[0-9A-Za-z-_]{35}", re.IGNORECASE), "Google / YouTube API key"),
    (re.compile(r"sk-[a-zA-Z0-9]{20,}", re.IGNORECASE), "OpenAI / Generic secret key"),
    (re.compile(r"ghp_[a-zA-Z0-9]{20,}", re.IGNORECASE), "GitHub Personal Access Token"),
    (re.compile(r"-----BEGIN (?:RSA|OPENSSH|EC|DSA) PRIVATE KEY-----"), "Private Key"),
    (re.compile(r"xox[baprs]-[0-9]{10,13}-[0-9]{10,13}-[a-zA-Z0-9]{24,32}"), "Slack Token"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS Access Key ID"),
]

IGNORED_DIRS = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    ".cache",
    ".ruff_cache",
    ".pytest_cache",
    "dist",
    "build",
}

IGNORED_FILES = {
    ".env.example",
    "scan_secrets.py",
}


def check_file(path: Path) -> list[str]:
    violations = []
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return []

    lines = text.splitlines()
    for idx, line in enumerate(lines, start=1):
        for pattern, label in SECRET_PATTERNS:
            if pattern.search(line):
                violations.append(f"{path}:{idx}: potential secret detected ({label})")

    return violations


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    violations = []

    for path in root.rglob("*"):
        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        if not path.is_file():
            continue
        if path.name in IGNORED_FILES:
            continue

        violations.extend(check_file(path))

    if violations:
        print(f"Secret scan failed: {len(violations)} issue(s) detected:")
        for v in violations:
            print(f"  {v}")
        return 1

    print("Secret scan passed: no obvious secrets found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
