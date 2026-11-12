# Skill: Testing and Quality Assurance

- **Name**: testing-and-quality
- **Description**: Comprehensive testing protocols covering backend unit and integration tests, frontend Vitest component tests, Playwright smoke tests, accessibility audits, and compliance checks.

## When to Use
Use this skill continuously during each phase development cycle and prior to merging any branch into main.

## Step by Step Procedure
1. Write isolated unit tests for backend business logic using recorded fixtures in `tests/fixtures/`.
2. Write integration tests for API endpoints with `httpx.AsyncClient` and FastAPI `TestClient`.
3. Write frontend unit tests with Vitest and React Testing Library for core UI components.
4. Run Playwright end-to-end smoke test to verify full search submission and SSE progress display.
5. Run axe-core accessibility audit to guarantee WCAG AA compliance.
6. Run `python3 scripts/check_compliance.py` to ensure zero emojis, em dashes, or en dashes.
7. Run `python3 scripts/scan_secrets.py` to confirm no keys or credentials are committed.
8. Ensure code is formatted and linted with `ruff` and `eslint`.

## Code Patterns
```python
import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app

@pytest.mark.asyncio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
```

## Pitfalls
- Mocking external services unrealistically: use realistic HTML fixtures extracted from actual pages.
- Skipping frontend accessibility checks.
- Leaving temporary debug print statements or secret keys in test scripts.

## Done Checklist
- [ ] Pytest passes: `uv run pytest tests/ -v`.
- [ ] Ruff checks pass: `uv run ruff check` and `uv run ruff format --check`.
- [ ] Vitest passes: `npm run test`.
- [ ] Compliance script passes: `python3 scripts/check_compliance.py`.
- [ ] Secret scan passes: `python3 scripts/scan_secrets.py`.
