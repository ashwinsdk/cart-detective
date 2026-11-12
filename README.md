# Cart Detective

Autonomous product research and verification engine providing evidence-backed buying decisions.

Repository: https://github.com/ashwinsdk/cart-detective.git

## Overview

Cart Detective takes a structured product query (category, budget, size, color, dealbreakers, target marketplaces) and runs a multi-stage background pipeline to identify, crawl, verify, and score candidates. Output includes a verified shortlist with seller pricing snapshots, review sentiment analysis, YouTube consensus summaries, and transparent scoring breakdowns.

## Quick Start

Setup takes under 10 minutes using `uv` and `node`.

### 1. Clone the Repository

```bash
git clone https://github.com/ashwinsdk/cart-detective.git
cd cart-detective
```

### 2. Environment Configuration

Copy the example environment file:

```bash
cp .env.example .env
```

Cart Detective works out of the box in degraded mode without API keys. To enable high-accuracy extraction and video summaries, configure:
- `GROQ_API_KEY`: Groq free tier API key.
- `YOUTUBE_API_KEY`: Google Cloud YouTube Data API v3 key.
- `BRAVE_SEARCH_API_KEY`: Brave Search free tier API key (optional fallback).

### 3. Setup and Run

Install all dependencies and initialize the database:

```bash
make setup
```

Start the application services (Backend API on port 8000, Frontend on port 5173):

```bash
make dev
```

Alternatively, run with Docker Compose:

```bash
docker compose up --build
```

Access the web interface at `http://localhost:5173`. The FastAPI documentation is available at `http://localhost:8000/docs`.

## Architecture

- **Backend**: Python 3.12, FastAPI, SQLAlchemy async with SQLite (PostgreSQL ready), Pydantic v2, HTTPX, Selectolax, Playwright.
- **Frontend**: React 18/19, Vite, TypeScript, Tailwind CSS, shadcn/ui, TanStack Query, React Router.
- **Search and Discovery**: Pluggable provider routing (DuckDuckGo, SearXNG, Brave Search).
- **LLM Layer**: Pluggable provider system (Groq, Gemini, Ollama, deterministic fallback).
- **Verification Engine**: Multi-source spec corroboration, seller price cross-checking, and fake review heuristics.

## Testing and Quality

Run backend and frontend test suites:

```bash
make test
```

Run code formatting and static analysis:

```bash
make lint
```

Verify compliance rules (no emojis, no dashes, secret scanning):

```bash
make check-compliance
make check-secrets
```

## Documentation

Detailed specifications are maintained in the `docs/` directory:
- [docs/ARCHITECTURE.md](file:///Users/ashwinsudhakar/Documents/Projects/excited-projects/cart-detective/docs/ARCHITECTURE.md): System design and component interactions.
- [docs/PIPELINE.md](file:///Users/ashwinsudhakar/Documents/Projects/excited-projects/cart-detective/docs/PIPELINE.md): Pipeline stage contracts, timeouts, and fallbacks.
- [docs/DATA_SOURCES.md](file:///Users/ashwinsudhakar/Documents/Projects/excited-projects/cart-detective/docs/DATA_SOURCES.md): Source quotas, rate limits, and fallback strategies.
- [docs/SCRAPING_POLICY.md](file:///Users/ashwinsudhakar/Documents/Projects/excited-projects/cart-detective/docs/SCRAPING_POLICY.md): Ethical scraping rules and robots.txt compliance.
- [docs/SCORING.md](file:///Users/ashwinsudhakar/Documents/Projects/excited-projects/cart-detective/docs/SCORING.md): Mathematical scoring formulation.
- [docs/DATA_MODEL.md](file:///Users/ashwinsudhakar/Documents/Projects/excited-projects/cart-detective/docs/DATA_MODEL.md): Schema models and relationships.
- [docs/API.md](file:///Users/ashwinsudhakar/Documents/Projects/excited-projects/cart-detective/docs/API.md): REST endpoints and SSE event streaming specs.
- [docs/UI_GUIDELINES.md](file:///Users/ashwinsudhakar/Documents/Projects/excited-projects/cart-detective/docs/UI_GUIDELINES.md): Minimalist design system and tokens.
- [docs/TASKS.md](file:///Users/ashwinsudhakar/Documents/Projects/excited-projects/cart-detective/docs/TASKS.md): Phased roadmap and implementation checklist.
- [docs/DECISIONS.md](file:///Users/ashwinsudhakar/Documents/Projects/excited-projects/cart-detective/docs/DECISIONS.md): Architectural decision records.

## License

MIT
