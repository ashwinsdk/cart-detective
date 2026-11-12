# Architecture Specification: Cart Detective

## 1. System Overview

Cart Detective is an autonomous product evaluation platform. It accepts high-level buyer constraints, retrieves candidate items across multiple ecommerce and specialist sources, analyzes community reviews and video breakdowns, validates claims against multi-source evidence, and produces a scored shortlist.

```
+-------------------------------------------------------------------------+
|                               Web Frontend                              |
|   (React 18/19 + Vite + TypeScript + Tailwind CSS + shadcn/ui + Lucide) |
+-------------------------------------------------------------------------+
                                    |
                           REST / SSE (HTTP/1.1)
                                    v
+-------------------------------------------------------------------------+
|                              FastAPI Core                               |
|   - Search and Run Management                                           |
|   - SSE Real-time Event Streaming                                       |
|   - User Collections (Wishlist, Purchases, Search History)              |
|   - Configuration and Weight Settings                                   |
+-------------------------------------------------------------------------+
                                    |
                              Async Workers
                                    v
+-------------------------------------------------------------------------+
|                          Pipeline Orchestrator                          |
|   +-----------------------------------------------------------------+   |
|   | Stage 1: Query Understanding (LLM / Rule Heuristic)             |   |
|   +-----------------------------------------------------------------+   |
|   | Stage 2: Candidate Discovery (SearXNG / DDG / Brave / Brand)    |   |
|   +-----------------------------------------------------------------+   |
|   | Stage 3: Brand Research (Reputation, Warranties, Signals)       |   |
|   +-----------------------------------------------------------------+   |
|   | Stage 4: Crawl and Scrape (HTTPX, Selectolax, Playwright)       |   |
|   +-----------------------------------------------------------------+   |
|   | Stage 5: Reviews and Video Mining (YouTube, Reddit, Forums)     |   |
|   +-----------------------------------------------------------------+   |
|   | Stage 6: Cross-Verification (Specs, Price, Fake Reviews)        |   |
|   +-----------------------------------------------------------------+   |
|   | Stage 7: Transparent Multi-Factor Scoring                       |   |
|   +-----------------------------------------------------------------+   |
|   | Stage 8: Presentation and Persistence                           |   |
|   +-----------------------------------------------------------------+   |
+-------------------------------------------------------------------------+
         |                                                 |
         v                                                 v
+-------------------+                             +-------------------+
|  SQLite / Postgres|                             |    Disk Cache     |
|   (SQLAlchemy)    |                             | (HTTP Responses)  |
+-------------------+                             +-------------------+
```

## 2. Core Subsystems

### 2.1 Backend API Layer
- **Framework**: FastAPI (async ASGI).
- **Concurrency**: `asyncio` background task worker per search execution.
- **Progress Delivery**: Server-Sent Events (SSE) streaming updates at `/api/runs/{id}/stream`.
- **Persistence**: SQLAlchemy 2.0 with `asyncpg` or `aiosqlite`.

### 2.2 Shared Fetch Layer
- **Client**: `httpx.AsyncClient` wrapped with token bucket rate limiting.
- **Robots.txt Engine**: Evaluates `urllib.robotparser` rules per origin domain.
- **Disk Cache**: Hashes URL, query params, and headers to disk with TTL enforcement.
- **Dynamic Scraper**: Playwright Python headless browser for JavaScript-heavy rendering.

### 2.3 LLM Provider Abstraction
- Provider interface defining `parse_query_spec()` and `extract_review_claims()`.
- Implementations:
  - `GroqProvider`: Default provider using Llama-3.3-70b-versatile.
  - `GeminiProvider`: Google GenAI API fallback.
  - `OllamaProvider`: Local self-hosted LLM fallback.
  - `HeuristicProvider`: Deterministic regex and rule parser for fully offline and unkeyed operations.

### 2.4 Verification Engine
- Corroborates specifications across at least two independent domains.
- Verifies size and color options exist at the stated price.
- Computes source trust score and tags unverified claims explicitly as "unverified".

### 2.5 Storage Model
- Relational schema storing searches, runs, products, seller offers, reviews, video transcripts, evidence citations, wishlists, and purchase records.
- Supports lightweight SQLite out of the box with zero external dependencies.
