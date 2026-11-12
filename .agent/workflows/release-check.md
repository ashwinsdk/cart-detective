# Workflow: Pre-Release Verification Checklist

This workflow defines the mandatory release gate checks prior to cutting a version tag or deploying.

## Steps

1. **Clean Workspace**:
   - Ensure working tree is clean (`git status` reports nothing to commit).
2. **Automated Test Suite**:
   - Run backend tests: `uv run pytest tests/ -v`.
   - Run frontend tests: `cd frontend && npm run test`.
   - Run type checking: `cd frontend && npm run typecheck`.
3. **Static Analysis and Linting**:
   - Run ruff: `uv run ruff check backend/ tests/`.
   - Run eslint: `cd frontend && npm run lint`.
4. **Compliance and Security Audit**:
   - Run compliance checker: `python3 scripts/check_compliance.py`.
   - Run secret scanner: `python3 scripts/scan_secrets.py`.
5. **UI and Accessibility Audit**:
   - Run automated axe-core accessibility audit.
   - Verify dark and light modes render with WCAG AA contrast.
   - Verify zero emojis, zero dashes, and no banned AI slop in the UI.
6. **Tag and Changelog**:
   - Update `CHANGELOG.md` with release notes.
   - Tag the release commit (for example, `git tag -a v0.1.0 -m "Release v0.1.0"`).
   - Push tag to origin.
