# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project adheres to Semantic Versioning.

## [Unreleased]

### Fixed
- Fixed irrelevant search results: discovery no longer falls back to unrelated registry products, matches categories only when every category word is present, and no longer synthesizes brand products or invents prices. Web results must be relevant, non-listing, non-accessory pages with a product-shaped URL. Queries with no relevant match now return an explained empty result.
- Fixed Stage 4 and SearXNG never fetching pages because `fetcher.fetch` rejected the `timeout` argument. Catalog prices are now marked unverified, offers are sorted best first, and verification applies relevance and budget checks to real scraped prices.
- Fixed a NameError in verification when certifications were requested without mandatory specs, and made brand and category keyword checks in `HeuristicProvider` match whole words.
- Fixed duplicate product generation in investigation runs by adding pipeline task concurrency guards in the orchestrator, candidate deduplication in scoring, and idempotent product persistence in the database layer.
- Fixed broken and 404 URLs by implementing live HTTP status probing, discarding dead links, dynamically searching for accessible replacement product URLs, and verifying all seed registry URLs against live stores.
- Fixed product miscategorization by adopting specificity-based category matching in candidate discovery and strict category relevance validation in the verification stage, ensuring street and track helmets are excluded from adventure helmet searches.
- Fixed candidate discovery terminating with zero products when categories had typos or when user specified brands outside the default registry.
- Added query typo correction in `HeuristicProvider` (for example, normalizing `helment` to `helmet`, `jaket` to `jacket`, `shooes` to `shoes`).
- Added motorcycle helmet and adventure helmet specifications, certifications (ECE 22.06, DOT, ISI), and mandatory features (peak visor, impact shell).
- Expanded curated candidate registry to include dual sport and adventure helmets from LS2, Axor, SMK, and MT Helmets.
- Added brand reputation profiles for LS2, Axor, SMK, and MT Helmets to prevent false-positive brand disqualification.
- Added seeded YouTube video review benchmarks for LS2 Pioneer II, Axor X-Cross, SMK Allterra, and MT Synchrony SV.
- Added dynamic brand candidate synthesis when users specify brands not present in seed registry.
- Integrated `ddgs` as an automated live web search fallback when SearXNG is unavailable.
- Fixed GitHub CI module resolution errors by unignoring `frontend/src/lib/` in `.gitignore` and tracking `utils.ts` and `export.ts`.
- Configured Vite development and preview proxy for `/api` routes pointing to FastAPI port 8000, resolving Failed to create search: Not Found error.
- Configured root environment directory resolution in Vite (`envDir: "../"`).
- Enhanced API client error parsing to extract FastAPI `detail` messages.
- Updated `make setup` to automatically initialize `.env` from `.env.example`.
- Updated secret scanner to ignore local uncommitted `.env` files.

### Added
- Removed default placeholder values from Search form, ensuring clean user-driven inputs and meaningful empty states.
- Implemented comprehensive mobile, tablet, and desktop responsiveness across header navigation, run telemetry, comparison tables, and list cards.
- Added edit and reuse capability in search history, creating a new investigation entry without overwriting past searches.
- Implemented automatic brand and marketplace discovery in query understanding stage when unspecified by user.
- Repository initialization with Stage 1 starter files.
- Agent operational rules and compliance tooling.
- Core technical documentation covering architecture, pipeline, data sources, scraping policy, scoring, data models, API contracts, and UI guidelines.
- Docker Compose configuration for API, frontend web, and SearXNG.
- GitHub Actions continuous integration workflow.
- Pre-commit and verification scripts for secret scanning and character compliance.
- Phase 0: Project scaffolding, tooling setup (Ruff, pytest, Vite, React, Vitest, Playwright).
- Phase 1: SQLAlchemy 2.0 asynchronous models and data repository layer.
- Phase 2: Shared fetcher with RFC 7234 cache, rate limiting, and pluggable LLM interface (Groq, Gemini, Ollama, Heuristic).
- Phase 3: Pipeline Stages 1 to 3 (Understand, Discover, and Brand Research).
- Phase 4: Pipeline Stages 4 to 6 (Scrape with Lexbor parser, Review Mining with YouTube transcripts, and Verification).
- Phase 5: Mathematical scoring engine, confidence metrics, and comparison matrix generation.
- Phase 6: FastAPI REST endpoints and SSE real-time pipeline event streaming.
- Phase 7: Frontend monochrome design system, theme switching, search input form, and live pipeline monitor.
- Phase 8: Results display, side-by-side comparison matrix, History, Wishlist, Bought pages, Settings, and CSV/JSON export.
- Phase 9: End-to-end reference queries covering riding gear, footwear, and electronics backpacks; Lexbor parser refinement, bimodal fake review detection, and empirical verification reporting.
- Phase 10: System hardening, empty state audits, accessibility compliance via axe-core WCAG AA test suite, form label associations, and release 0.1.0 preparation.

## [0.1.0] - 2026-11-12

### Added
- Complete initial release of Cart Detective autonomous buying research engine.
- Multi-stage background pipeline with Server-Sent Events live streaming.
- Corroborated evidence verification with multi-source consensus.
- Minimalist monochrome black and white interface supporting light and dark themes.
