# Rule: Test Before Marking Complete

## Scope
Applies to all pull requests, phase completions, and code submissions.

## Requirements
1. **Automated Verification**:
   - Backend: All pytest suites must pass (`uv run pytest tests/ -v`).
   - Backend linting: Ruff checks and format checks must pass (`uv run ruff check` and `uv run ruff format --check`).
   - Frontend: Vitest and TypeScript checks must pass (`npm run test`, `npm run typecheck`, `npm run lint`).
2. **Quality Gates**:
   - Compliance script must pass: `python3 scripts/check_compliance.py`.
   - Secret scan script must pass: `python3 scripts/scan_secrets.py`.
3. **No Phase Hand-off Without Green Status**:
   - A phase checklist item in `docs/TASKS.md` may only be ticked when all automated verification steps succeed.
