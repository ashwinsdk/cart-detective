# Pipeline Specification: Cart Detective

This document defines the 8-stage execution pipeline, stage contracts, timeouts, retry policies, and degradation behavior.

## 1. Stage Overview and Execution Flow

```
User Query Form
      |
      v
[Stage 1: Understand]           Timeout: 10s | Retries: 2 | Fallback: Heuristic Parser
      |
      v
[Stage 2: Discover Candidates]  Timeout: 20s | Retries: 2 | Fallback: Curated Seed Directory
      |
      v
[Stage 3: Brand Research]       Timeout: 15s | Retries: 1 | Fallback: Neutral Score Default
      |
      v
[Stage 4: Crawl and Scrape]     Timeout: 25s | Retries: 2 | Fallback: Structured Snippets / Cache
      |
      v
[Stage 5: Review and Video]     Timeout: 30s | Retries: 2 | Fallback: Video Metadata / Comments
      |
      v
[Stage 6: Verify and Validate]  Timeout: 15s | Retries: 1 | Fallback: Mark "unverified"
      |
      v
[Stage 7: Score and Rank]       Timeout: 5s  | Retries: 0 | Fallback: Deterministic Scoring
      |
      v
[Stage 8: Present and Persist]  Timeout: 5s  | Retries: 1 | Output: SSE + DB Record
```

## 2. Detailed Stage Contracts

### Stage 1: Understand
- **Input**: Raw query fields (product_type, budget_min, budget_max, currency, colors, size_gender, must_haves, deal_breakers, brands_included, brands_excluded, country_marketplaces).
- **Output**: `StructuredQuerySpec` containing normalized keywords, required specifications, mandatory safety ratings or standards, and disqualifying red flags.
- **Timeout**: 10 seconds total.
- **Retries**: 2 attempts with exponential backoff (1s, 2s).
- **Failure Handling**: If the configured LLM fails or no API key is provided, the stage switches to the deterministic `HeuristicProvider`, which parses integers, currency symbols, and keyword patterns.

### Stage 2: Discover Candidates
- **Input**: `StructuredQuerySpec`.
- **Output**: List of deduplicated candidate products (canonical brand, model name, primary seed URLs).
- **Timeout**: 20 seconds total.
- **Retries**: 2 attempts per search backend.
- **Failure Handling**: If SearXNG or Brave Search times out or returns HTTP 429, fall back to DuckDuckGo search or marketplace listing page queries. If all fail, return candidates extracted from cached discovery entries or specialist seed directories.

### Stage 3: Brand Research
- **Input**: Discovered candidate brands.
- **Output**: Brand reputation signal dict (reputation score 0 to 100, warranty track record, known customer support posture, drop flag).
- **Timeout**: 15 seconds total.
- **Retries**: 1 attempt per brand.
- **Failure Handling**: If forum searches or brand websites cannot be reached, assign a neutral default reputation score (50/100) and log the failure. Brands are dropped only when hard negative signals are verified.

### Stage 4: Crawl and Scrape
- **Input**: Candidate product URLs.
- **Output**: Normalized product attributes, listed price, seller name, stock status, exact color/size availability, and raw specs.
- **Timeout**: 25 seconds per domain batch.
- **Retries**: 2 attempts with jittered backoff.
- **Failure Handling**: Best-effort extraction. Inspect JSON-LD, OpenGraph tags, and search result snippets first. If a target page blocks with 403 or CAPTCHA, mark the source as "unavailable". Never attempt CAPTCHA solving or login bypass. Return partial product data.

### Stage 5: Reviews and Video Mining
- **Input**: Product name, brand, model.
- **Output**: User sentiment score, verified review summary, pros, cons, YouTube video reviews, transcript summary, and sponsor disclosures.
- **Timeout**: 30 seconds total.
- **Retries**: 2 attempts.
- **Failure Handling**: If YouTube transcript download fails, fall back to video title, description, and top comments. If YouTube API quota is exhausted, fall back to Reddit and marketplace review text. If all external reviews fail, mark review status as "no community data".

### Stage 6: Verify and Validate
- **Input**: Scraped specifications, multiple seller prices, review distributions.
- **Output**: Verification matrix: cross-checked specs (minimum 2 independent sources), price stability check, color/size existence verification, fake review anomaly score, source citations.
- **Timeout**: 15 seconds total.
- **Retries**: 1 attempt.
- **Failure Handling**: Any specification or claim that cannot be confirmed across independent sources is explicitly marked "unverified". No claims are fabricated or assumed.

### Stage 7: Score and Rank
- **Input**: Verified specifications, review scores, price compliance, brand trust, YouTube consensus.
- **Output**: Final numerical score (0 to 100), confidence percentage (0 to 100%), ranked product list, and comparison table.
- **Timeout**: 5 seconds.
- **Retries**: 0 (deterministic in-memory calculation).
- **Failure Handling**: If certain signals are missing, redistribute weights proportionally across available signals and downscale the overall confidence score.

### Stage 8: Present and Persist
- **Input**: Ranked products, decision rationale, stage execution telemetry.
- **Output**: Database storage commit, final SSE `complete` event with payload.
- **Timeout**: 5 seconds.
- **Retries**: 1 retry on database lock.
- **Failure Handling**: Return results directly in SSE response stream even if database write fails, logging an error.

## 3. Pipeline Version History

- **v0.1.0-dev** (Initial Pipeline Design):
  - Defined 8 stages with isolated error domains.
  - Added strict timeouts and retry caps per stage.
  - Added fallback degradation paths for keyless environments.
  - Enforced "unverified" tagging for uncorroborated specs.
