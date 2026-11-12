# Ethical Scraping and Retrieval Policy: Cart Detective

This document defines the strict operational boundaries enforced by the Cart Detective data collection layer.

## 1. Guiding Principles

1. **API First**: Always prefer official APIs (SearXNG, Brave, YouTube) when accessible.
2. **Robots Compliance**: Respect `robots.txt` directives for every accessed domain.
3. **No Authentication Bypass**: Never bypass logins, paywalls, CAPTCHAs, or access control gates.
4. **No Personal Data**: Never collect, store, or process personal user information, addresses, or private credentials.
5. **Polite Footprint**: Rate limit requests per host, cache aggressively on disk, and handle backoff gracefully.

## 2. Technical Enforcement in the Shared Fetch Layer

All HTTP and browser-based retrieval must pass through `backend/services/fetcher.py`. Direct unmanaged socket or HTTP calls are prohibited.

### 2.1 Identification
Every outgoing request must present a descriptive User-Agent header:
```
CartDetective/0.1.0 (Autonomous Research Agent; +https://github.com/ashwinsdk/cart-detective)
```

### 2.2 Rate Limiting
- Default rate limit: Minimum 1.0 second delay between requests to the same origin domain.
- Throttling: If an origin returns HTTP 429 (Too Many Requests), exponential backoff begins immediately with delays of 2s, 4s, and 8s.

### 2.3 Access Denied Handling
- If a server responds with HTTP 403 (Forbidden) or redirects to a CAPTCHA challenge:
  - Do not attempt browser spoofing or evasion.
  - Immediately log the domain as blocked.
  - Mark the source offer or specification as "unavailable".
  - Continue pipeline execution with remaining sources.

### 2.4 Caching Policy
- All successful GET responses are cached to disk under `data/cache/http/` using the SHA-256 hash of the canonical URL.
- Default TTL: 24 hours for product detail pages, 6 hours for search result listings.
- Identical queries within the TTL window are served from disk without hitting the remote host.

### 2.5 Dynamic Page Rendering
- Playwright is used only when static HTML parsers (`httpx` + `selectolax`) cannot extract essential structured data.
- Headless browser sessions must disable image and font loading to minimize bandwidth consumption.
