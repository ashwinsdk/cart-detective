# Architecture Decision Records (ADRs): Cart Detective

This document tracks significant design, technical, and architectural decisions made throughout the Cart Detective project.

---

## ADR 001: Monochrome Minimalist UI Design System

- **Context**: Consumer shopping interfaces frequently feature cluttered layouts, vibrant marketing banners, floating badges, and AI promotional elements.
- **Decision**: Adopt a strict black-and-white minimalist design system with neutral grays, thin 1px borders, small border radii, and no gradients, glows, or decorative icons.
- **Consequences**: Ensures high information density, rapid comprehension, and zero distraction. Demands rigorous contrast enforcement (WCAG AA).

---

## ADR 002: Pluggable Free-Tier LLM Provider with Deterministic Heuristic Fallback

- **Context**: External API quotas (Groq, Gemini) can be exhausted, and users may not provide API keys when self-hosting.
- **Decision**: Implement a pluggable `BaseLLMProvider` interface with Groq as default, optional Gemini and local Ollama, and a robust deterministic regex-based rule parser fallback (`HeuristicProvider`). Configurable model names are loaded from environment variables and never hardcoded.
- **Consequences**: Enables the entire discovery and verification pipeline to function reliably in a zero-key offline environment.

---

## ADR 003: Handling and Displaying Scraped Third-Party Text

- **Context**: External websites, marketplace reviews, Reddit threads, and YouTube comments often contain emojis, em dashes, en dashes, and informal formatting. The codebase strictly bans emojis and unicode dashes from its source, documentation, and application-authored copy.
- **Decision**:
  1. **Storage**: Raw third-party text is stored unmodified in the database (`reviews.content`, `videos.transcript_summary`) to maintain empirical fidelity with source data.
  2. **Display Sanitization**: When rendering user reviews, video summaries, or seller snippets in the UI, client-side rendering components execute a lightweight sanitizer:
     - Unicode em dashes (`\u2014`) and en dashes (`\u2013`) are converted to standard ASCII commas or hyphens.
     - Emojis are stripped or replaced with clean text markers during presentation.
  3. **Application Copy Isolation**: Generated verdicts, explanation panels, scoring summaries, and system messages are authored strictly according to compliance rules without emojis or unicode dashes.
- **Consequences**: Preserves audit integrity of external evidence while ensuring the rendered UI remains 100% compliant with the minimalist typography standard.

---

## ADR 004: Ethical Scraping and Source Degradation

- **Context**: Commercial ecommerce platforms enforce anti-bot controls, rate limits, and CAPTCHA challenges.
- **Decision**: Adhere strictly to ethical scraping principles: obey `robots.txt`, set honest User-Agent headers, enforce token-bucket rate limits, cache responses to disk, and gracefully mark blocked sources as "unavailable". Never attempt login bypasses, proxy rotation for evasion, or CAPTCHA solving.
- **Consequences**: Guarantees legal compliance and long-term stability. Requires the verification and scoring engine to handle partial or missing source data smoothly.

---

## ADR 005: Server-Sent Events (SSE) for Real-Time Execution Progress

- **Context**: Multi-stage research pipelines take 15 to 45 seconds to gather external data, which would cause standard synchronous HTTP requests to time out.
- **Decision**: Background pipeline execution is decoupled using `asyncio` tasks. The frontend subscribes to an SSE endpoint (`/api/runs/{id}/stream`), receiving granular stage events, logs, and candidate updates in real time.
- **Consequences**: Provides users with immediate feedback and transparency without requiring complex message broker infrastructure (such as Redis or Celery) for single-node deployments.
