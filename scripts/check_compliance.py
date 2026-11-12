#!/usr/bin/env python3
"""
Compliance checker for Cart Detective.
Verifies that no emojis, em dashes, or en dashes exist in tracked source code, docs, rules, and scripts.
Uses escape codes exclusively to reference banned characters so this file itself remains clean.
"""

import os
import re
import sys
from pathlib import Path

# Banned characters represented strictly as unicode escapes
EM_DASH = "\u2014"
EN_DASH = "\u2013"

# Common emoji ranges in unicode escapes
EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # Emoticons
    "\U0001F300-\U0001F5FF"  # Misc symbols and pictographs
    "\U0001F680-\U0001F6FF"  # Transport and map
    "\U0001F700-\U0001F77F"  # Alchemical symbols
    "\U0001F780-\U0001F7FF"  # Geometric shapes extended
    "\U0001F800-\U0001F8FF"  # Supplemental arrows-C
    "\U0001F900-\U0001F9FF"  # Supplemental symbols and pictographs
    "\U0001FA00-\U0001FA6F"  # Chess symbols, symbols and pictographs extended-A
    "\U0001FA70-\U0001FAFF"  # Symbols and pictographs extended-A
    "\U00002702-\U000027B0"  # Dingbats
    "\U000024C2-\U0001F251"  # Enclosed alphanumerics
    "\U00002600-\U000026FF"  # Misc symbols
    "]",
    flags=re.UNICODE,
)

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
    "playwright-report",
    "test-results",
}

IGNORED_FILES = {
    "package-lock.json",
    "uv.lock",
    "pnpm-lock.yaml",
    "yarn.lock",
    "check_compliance.py",
}

BINARY_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".ico",
    ".sqlite",
    ".db",
    ".pyc",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".zip",
    ".tar",
    ".gz",
}


def is_binary(path: Path) -> bool:
    if path.suffix.lower() in BINARY_EXTENSIONS:
        return True
    try:
        with open(path, "rb") as f:
            chunk = f.read(1024)
            if b"\x00" in chunk:
                return True
    except OSError:
        return True
    return False


def check_file(path: Path) -> list[str]:
    violations = []
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return []
    except Exception as exc:
        return [f"Could not read {path}: {exc}"]

    lines = text.splitlines()
    for idx, line in enumerate(lines, start=1):
        if EM_DASH in line:
            violations.append(
                f"{path}:{idx}: contains forbidden em dash (replace with comma, period, or colon)"
            )
        if EN_DASH in line:
            violations.append(
                f"{path}:{idx}: contains forbidden en dash (replace with comma, period, or colon)"
            )
        match = EMOJI_PATTERN.search(line)
        if match:
            violations.append(
                f"{path}:{idx}: contains forbidden emoji at position {match.start()}"
            )

    return violations


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    all_violations = []

    for path in root.rglob("*"):
        if path.is_dir():
            if path.name in IGNORED_DIRS:
                continue
        if not path.is_file():
            continue

        # Skip ignored directories if present in parent paths
        if any(part in IGNORED_DIRS for part in path.parts):
            continue

        if path.name in IGNORED_FILES:
            continue

        if is_binary(path):
            continue

        violations = check_file(path)
        all_violations.extend(violations)

    if all_violations:
        print(f"Compliance check failed: {len(all_violations)} violation(s) found:")
        for v in all_violations:
            print(f"  {v}")
        return 1

    print("Compliance check passed: no emojis, em dashes, or en dashes found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
