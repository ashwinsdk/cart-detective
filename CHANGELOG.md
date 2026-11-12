# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project adheres to Semantic Versioning.

## [Unreleased]

### Added
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
