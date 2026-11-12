# Agent Operating Instructions: Cart Detective

This document defines standard operating practices for automated coding agents and contributors working in this repository.

## 1. Repository Rules

- Repo root is the project root. Never create a nested cart-detective directory.
- The default branch is `main`.
- All development follows phase branches formatted as `phase/<number>-<short-name>` (for example, `phase/0-scaffold`, `phase/1-data-model`).
- When a phase passes all tests and lint checks, fast-forward or squash merge into `main`.
- Push to origin after every phase. If authentication fails, output the exact command or token needed without guessing.

## 2. Commit and Message Standards

- Format commits using Conventional Commits: `feat:`, `fix:`, `docs:`, `chore:`, `test:`, `refactor:`.
- Use concise imperative mood: "add search candidate deduplication", not "added search candidate deduplication".
- Zero emojis anywhere: never use emoji characters or shortcodes in commit messages, code comments, strings, or docs.
- Zero em dashes or en dashes anywhere: strictly use commas, periods, or colons. Never use unicode `\u2014` or `\u2013`.
- Run `python3 scripts/check_compliance.py` and `python3 scripts/scan_secrets.py` prior to committing.

## 3. Data Integrity and Verification

- Zero fabricated data: never invent prices, specifications, reviews, or seller availability.
- Every claim presented to the user must link to an empirical source URL.
- If data cannot be verified or a source blocks scraping, explicitly mark the item as "unverified" or "unavailable".
- Scraped third-party text containing emojis or dashes may be stored as raw input, but must be sanitized or safely displayed without violating application rendering rules.

## 4. UI Guidelines

- Visual palette: strictly black, white, and neutral grays.
- Functional states (success, warning, error) must use muted monochrome or subtle functional tones without bright saturated colors.
- Both dark mode and light mode must be supported with zero flash on initial load.
- Typography: Inter or Geist font family.
- Line icons: Lucide icons only. Never use decorative or floating icon badges.
- Ban all AI slop: no gradients, no glows, no glassmorphism, no blobs, and no marketing buzzwords (such as "seamless", "unleash", "supercharge", "elevate", "revolutionary").

## 5. Development Workflow

- Backend package management: use `uv`.
- Backend testing: use `pytest`.
- Backend linting and formatting: use `ruff`.
- Frontend tooling: use Vite, TypeScript, Vitest, and Playwright.
- Pipeline stages: respect timeout parameters, implement exponential backoff on retries, and ensure resilient partial results when upstream services fail.
- Always update `docs/TASKS.md` after completing each phase.
