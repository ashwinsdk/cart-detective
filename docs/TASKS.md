# Project Tasks and Phased Checklist: Cart Detective

This checklist tracks progress across Stage 1 and Stage 2. Update this file as each phase passes tests and is merged to `main`.

## Stage 1: Starter Files and Repository Foundation

- [x] Create project repository structure and documentation files.
- [x] Configure `.gitignore` with all required exclusions before first commit.
- [x] Create compliance script `scripts/check_compliance.py` for banned emojis and dashes.
- [x] Create secret scanner script `scripts/scan_secrets.py`.
- [x] Create root configuration: `Makefile`, `docker-compose.yml`, `.env.example`.
- [x] Create GitHub Actions CI workflow in `.github/workflows/ci.yml`.
- [x] Create `.agent/rules/`, `.agent/workflows/`, and `.agent/skills/`.
- [x] Show directory tree to user, commit to `main`, and push to origin.

---

## Stage 2: Phased Implementation Roadmap

### Phase 0: Scaffold, Tooling, Docker, and CI
- [x] Branch: `phase/0-scaffold`
- [x] Initialize Python 3.12 backend with `uv` (`pyproject.toml`, FastAPI, SQLAlchemy, Pydantic v2, Ruff, pytest, Playwright).
- [x] Initialize React Vite TypeScript frontend (`package.json`, Tailwind CSS, shadcn/ui, React Router, Vitest).
- [x] Verify Docker Compose setup for api, web, and searxng.
- [x] Acceptance Criteria: `make test` and `make lint` execute and pass on both backend and frontend.

### Phase 1: Data Model, Migrations, and Repository Layer
- [x] Branch: `phase/1-data-model`
- [x] Implement SQLAlchemy declarative async models: Search, Run, Product, Offer, Review, Video, Evidence, WishlistItem, Purchase, Setting.
- [x] Implement repository pattern for all core entities with async session management.
- [x] Unit tests for database models, constraints, and cascades.
- [x] Acceptance Criteria: Database migrations run, CRUD integration tests pass without errors.

### Phase 2: Shared Fetch Layer and LLM Provider Interface
- [ ] Branch: `phase/2-fetch-llm`
- [ ] Build shared HTTP fetcher with token-bucket rate limiter, RFC 7234 disk cache, robots.txt validator, and backoff logic.
- [ ] Implement pluggable LLM provider interface (`BaseLLMProvider`) with Groq, Gemini, Ollama, and Heuristic fallback.
- [ ] Ensure LLM model names are configurable via environment variables and not hardcoded.
- [ ] Unit tests with recorded mock HTTP responses and fixture payloads.
- [ ] Acceptance Criteria: Fetcher respects rate limits and cache TTL; LLM interface parses test prompts cleanly.

### Phase 3: Pipeline Stages 1 to 3
- [ ] Branch: `phase/3-pipeline-early`
- [ ] Stage 1 (Understand): Convert raw query input to `StructuredQuerySpec` using LLM with heuristic fallback.
- [ ] Stage 2 (Discover Candidates): Query SearXNG, DuckDuckGo, and Brave Search; deduplicate by canonical brand and model.
- [ ] Stage 3 (Brand Research): Scrape warranty, forum reputation, and support footprint; filter disqualified brands.
- [ ] Acceptance Criteria: Pipeline executes stages 1 to 3, emitting candidates with brand reputation metrics.

### Phase 4: Pipeline Stages 4 to 6
- [ ] Branch: `phase/4-pipeline-core`
- [ ] Stage 4 (Crawl and Scrape): Extract structured attributes, prices, and availability using selectolax and Playwright. Mark blocked pages as "unavailable".
- [ ] Stage 5 (Reviews and YouTube): Collect marketplace reviews and YouTube video transcripts (fallback to titles, descriptions, top comments).
- [ ] Stage 6 (Verify and Validate): Cross-check specs across independent sources; verify color and size availability at listed price; tag unconfirmed specs as "unverified"; calculate fake review indicators.
- [ ] Acceptance Criteria: Structured specs extracted and validated; verified source URLs assigned to all claims.

### Phase 5: Scoring Engine and Explanations
- [ ] Branch: `phase/5-scoring`
- [ ] Implement transparent weighted scoring algorithm (budget fit, spec match, review sentiment, brand reliability, YouTube consensus, stock trust).
- [ ] Compute evidence confidence score based on source quantity, consensus, and completeness.
- [ ] Generate objective decision explanations and side-by-side comparison matrix.
- [ ] Acceptance Criteria: Unit tests verify mathematical consistency of scores and weight overrides.

### Phase 6: API Layer, SSE Progress, and Thin End-to-End Slice
- [ ] Branch: `phase/6-api-sse`
- [ ] Implement FastAPI endpoints for searches, runs, products, wishlist, purchases, and settings.
- [ ] Implement Server-Sent Events (`/api/runs/{id}/stream`) for real-time stage progress and logs.
- [ ] Wire up thin end-to-end slice connecting mock fixture pipeline to API and minimal frontend verification.
- [ ] Acceptance Criteria: SSE stream emits stage progress from start to completion; frontend receives and renders live updates.

### Phase 7: Frontend Core, Design System, Search, and Live Run
- [ ] Branch: `phase/7-frontend-search`
- [ ] Implement monochrome design tokens, dark and light theme toggle with zero flash.
- [ ] Build shared shadcn/ui components adhering to `docs/UI_GUIDELINES.md`.
- [ ] Build Search input form with comprehensive validation.
- [ ] Build Live Run progress view with real-time SSE stage indicators and log console.
- [ ] Acceptance Criteria: Search form dispatches run, displays live progress without console errors.

### Phase 8: Frontend Results, Comparison, Workspace, and Settings
- [ ] Branch: `phase/8-frontend-views`
- [ ] Build Results view with ranked product cards, price snapshots, pros and cons, and evidence links.
- [ ] Build side-by-side product comparison table for top 3 to 5 products.
- [ ] Build History, Wishlist, and Bought tracking pages with local persistence.
- [ ] Build Settings page with scoring weight sliders and API key status indicators.
- [ ] Implement CSV and JSON export functionality.
- [ ] Acceptance Criteria: All user journeys operate cleanly; data persists across page reloads.

### Phase 9: End-to-End Reference Queries and Pipeline Refinement
- [ ] Branch: `phase/9-e2e-testing`
- [ ] Execute reference test query 1: Riding jacket under 12,000 INR (black).
- [ ] Execute reference test query 2: Running shoes under 5,000 INR.
- [ ] Execute reference test query 3: Laptop backpack under 3,000 INR.
- [ ] Fix broken scrapers or edge cases; update `docs/PIPELINE.md` and `CHANGELOG.md` with findings.
- [ ] Acceptance Criteria: All 3 reference queries return verified, sourced shortlists in degraded or online mode.

### Phase 10: Hardening, Accessibility, and Release
- [ ] Branch: `phase/10-hardening`
- [ ] Audit all empty states, loading skeletons, and error screens.
- [ ] Execute automated accessibility check (axe-core) for WCAG AA compliance.
- [ ] Execute Playwright browser smoke test and Vitest component test suite.
- [ ] Verify clean setup under 10 minutes on fresh clone.
- [ ] Tag release `v0.1.0`.
- [ ] Acceptance Criteria: 100% passing tests, green CI on all branches, zero compliance violations.
