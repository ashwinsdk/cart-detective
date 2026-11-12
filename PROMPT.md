# Cart Detective: Specification and Requirements

Repository: https://github.com/ashwinsdk/cart-detective.git

You are the lead engineer. Build a COMPLETE, working project called "Cart Detective".

Work in two stages:

STAGE 1: Set up the repo, then generate the starter files (docs, rules, skills, workflows) and show the tree. Continue without waiting.
STAGE 2: Build the full application phase by phase, following the docs created. After each phase, run tests, fix failures, tick the phase in docs/TASKS.md, commit, push, and continue.

## Git and Repository Rules

- If the workspace is empty, clone https://github.com/ashwinsdk/cart-detective.git . If the repo already has files, read them first and adapt to what exists instead of overwriting.
- The repo root is the project root. Do not create a nested "cart-detective" folder.
- Default branch: main. Work on one branch per phase named `phase/<number>-<short-name>`, then merge into main when the phase passes tests (fast forward or squash, keep history clean).
- Conventional commits (feat, fix, docs, chore, test, refactor), plain imperative text, small and frequent. No emojis, no em dashes or en dashes in commit messages, code comments, or docs.
- Push to origin after every phase. If push fails because of auth, stop and tell the user exactly what credential or command is needed instead of guessing.
- `.gitignore` must exist before the first commit: .env, node_modules, __pycache__, .venv, *.db, cache directories, build output, Playwright browsers, logs.
- Never commit secrets. Only `.env.example` is committed. Add a simple secret scan step.
- Add GitHub Actions CI: backend lint and tests, frontend lint, typecheck and build, on every push and pull request, covering main and phase/* branches.
- README must show the repo URL, clone command, and setup steps.

## Product Idea

A tool that takes a product request and returns a verified shortlist of the best products to buy, with evidence.

Input form fields:
- Product type (example: riding jacket)
- Budget range (min, max, currency: default INR, example: up to 12K)
- Color preference (multi select, optional)
- Size, fit, gender or use case (optional)
- Must have features and deal breakers (free text, optional)
- Brands to include or exclude (optional)
- Country or marketplaces to search (default India: Amazon.in, Flipkart, brand sites, specialist retailers)

Output: a ranked list of suggested products. Each item shows name, brand, price (with seller and date checked), score with confidence, pros, cons, review summary, YouTube review summary, evidence links, and a verdict line. Also show a short "how we decided" panel and a comparison table for the top 3 to 5.

## Pipeline Architecture

1. Understand: convert the form input into a structured spec using an LLM (Groq free tier first, with a pluggable provider interface so Gemini free tier or local Ollama can replace it). Model names must be configurable and not hardcoded. Derive search keywords, must have specs, standards or certifications that matter for this product category, and red flags.
2. Discover candidates: use official APIs and search first. Options: SearXNG (self hosted via Docker), DuckDuckGo search lib, Brave Search API free tier if a key is present, marketplace listing pages, brand sites, Reddit search, specialist forums and review sites. Deduplicate by brand plus model.
3. Brand research: for each brand, collect reputation signals (Reddit threads, forum posts, expert reviews, return and warranty policy, service presence in the target country). Drop weak brands early and log why.
4. Crawl and scrape: Python is the primary stack. Use httpx plus selectolax or BeautifulSoup for static pages, Playwright for JavaScript pages, trafilatura for article text, and youtube-transcript-api plus YouTube Data API v3 for video data. Marketplace scraping is best effort: prefer JSON-LD, structured data, search snippets, brand sites and specialist retailers. If a page blocks, mark source "unavailable" without attempting bypasses or logins.
5. Reviews: collect marketplace reviews, Reddit discussions, expert reviews, and YouTube reviews (search videos, take top relevant ones, pull transcripts and top comments; if transcripts fail, fall back to titles, descriptions, and comments; summarize claims, extract pros and cons, note sponsorship disclosures).
6. Verify and validate:
   - Cross check specs across at least two independent sources.
   - Cross check price across sellers: flag stale or suspicious prices.
   - Verify color and size availability at the listed price.
   - Fake review heuristics: rating distribution shape, verified purchase ratio, review bursts, repeated phrases, incentivized review mentions.
   - Prefer sources with real usage evidence over affiliate listicles.
   - Check seller trust, return window, warranty.
   - Every claim shown in the UI must carry a source URL. If something cannot be verified, show "unverified". Never invent prices, specs or reviews.
7. Score: transparent weighted score (budget fit, quality evidence, review sentiment weighted by source trust, spec match, brand reliability, warranty, availability, YouTube consensus). Weights editable in settings. Output confidence based on amount and agreement of evidence.
8. Present: persist results and render in the UI with a thin end to end slice created by Phase 6.

Every pipeline stage has explicit timeouts, retry counts, disk caching, and partial result tolerance when a source fails.

## Scraping Rules

Respect robots.txt and site terms, prefer official APIs, rate limit per domain, identify with a clear user agent, cache responses on disk, back off on 429 and 403, never bypass logins or paywalls, never collect personal data.

## Stack

- Backend: Python 3.12, FastAPI, SQLAlchemy plus SQLite (Postgres ready), Pydantic v2, httpx, Playwright, APScheduler or asyncio tasks, pytest, ruff, uv for dependencies.
- Frontend: React, Vite, TypeScript, Tailwind CSS, shadcn/ui, TanStack Query, React Router, Vitest.
- Dev: Docker Compose (api, web, searxng), Makefile with setup, dev, test, lint, build targets, .env.example with every key documented. App must still run in degraded mode with no keys.
- Free tiers only: document each quota and mitigation.

## Web UI

Pages: Search, Run (live SSE pipeline progress), Results, History, Wishlist, Bought, Settings.
Visual rules: Minimalistic, professional, black and white with neutral grays only. Full dark mode and light mode, zero flash on load, WCAG AA contrast. No emojis. No em dashes or en dashes. No AI slop or marketing buzzwords. Inter or Geist typography. Lucide icons.
