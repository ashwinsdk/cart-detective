# Data Sources and Provider Quotas: Cart Detective

This document tracks all external data sources, official APIs, scraping endpoints, rate limits, quotas, and legal parameters.

## 1. Large Language Model Providers

### Groq API
- **Endpoint**: `https://api.groq.com/openai/v1`
- **Model**: Configured via `LLM_MODEL` (default: `llama-3.3-70b-versatile`).
- **Quota**: Free Tier offers 30 requests per minute and 14,400 requests per day.
- **Usage**: Stage 1 query understanding and Stage 5 claim synthesis.
- **Fallback**: Google Gemini free tier, local Ollama, or deterministic regex parser.
- **Legal and Terms**: Standard Groq developer terms. No personal data transmitted.

### Google Gemini API
- **Endpoint**: `https://generativelanguage.googleapis.com/v1beta`
- **Model**: Configured via `GEMINI_MODEL` (default: `gemini-1.5-flash`).
- **Quota**: Free Tier offers 15 requests per minute and 1,500 requests per day.
- **Usage**: Secondary LLM provider.
- **Fallback**: Local Ollama or deterministic regex parser.

### Local Ollama
- **Endpoint**: Configurable via `OLLAMA_BASE_URL` (default: `http://localhost:11434`).
- **Model**: `llama3.2` or user-specified model.
- **Quota**: Unlimited (hardware dependent).
- **Usage**: Fully offline, private operation.

---

## 2. Search and Discovery Providers

### SearXNG (Self-Hosted)
- **Endpoint**: `http://searxng:8080` (via Docker Compose) or local instance.
- **Quota**: Unlimited, subject to upstream engine blocks.
- **Engines Aggregated**: Google, Bing, DuckDuckGo, Reddit, Wikipedia.
- **Usage**: Primary discovery tool for product candidate seeds.
- **Fallback**: Direct DuckDuckGo HTML scraping or Brave Search API.

### Brave Search API
- **Endpoint**: `https://api.search.brave.com/res/v1/web/search`
- **Quota**: Free tier allows 2,000 queries per month and 1 request per second.
- **Usage**: Backup discovery engine when SearXNG or DDG is throttled.
- **Fallback**: DuckDuckGo search library.

### DuckDuckGo Search
- **Protocol**: Direct HTTPS queries with search parameter formatting.
- **Rate Limit**: Maximum 1 request every 2 seconds to avoid rate limiting.
- **Usage**: Candidate seed queries and Reddit thread discovery.

---

## 3. Video and Community Review Sources

### YouTube Data API v3
- **Endpoint**: `https://www.googleapis.com/youtube/v3/search` and `videos`
- **Quota**: 10,000 units per day. Search calls consume 100 units; video details consume 1 unit.
- **Usage**: Retrieving top relevant review videos, titles, and descriptions.
- **Fallback**: Web scrape of YouTube search results or `youtube-transcript-api`.

### YouTube Transcript API
- **Protocol**: Extraction of automated or manual video captions via `youtube-transcript-api`.
- **Quota**: No formal rate limit, but backoff is applied on HTTP 429.
- **Usage**: Pulling spoken transcripts for pros, cons, and sponsorship disclosures.
- **Fallback**: Video title, description, and top viewer comments.

### Reddit Public JSON API
- **Endpoint**: `https://www.reddit.com/r/{subreddit}/search.json`
- **Rate Limit**: 1 request per second with a unique User-Agent header.
- **Usage**: Finding real user experience threads, long-term durability feedback, and issues.
- **Fallback**: Forum and specialist review site queries.

---

## 4. Marketplaces and Retailers

### Amazon.in, Flipkart, Brand Webstores, Specialist Retailers
- **Approach**: Best effort extraction using JSON-LD metadata, microdata, and public product markup.
- **Access Rule**: Strictly obey `robots.txt`. Do not bypass anti-bot mechanisms, solve CAPTCHAs, or log into user accounts.
- **Fallback**: Search snippet cache and specialist retailer catalogs. If a seller page returns HTTP 403 or blocks, record the seller as "unavailable" and continue pipeline execution.
