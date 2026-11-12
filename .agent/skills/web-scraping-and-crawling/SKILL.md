# Skill: Web Scraping and Crawling

- **Name**: web-scraping-and-crawling
- **Description**: Robust, ethical, rate-limited extraction of product details, specifications, and prices using HTTPX, Selectolax, and Playwright with disk caching.

## When to Use
Use this skill when fetching external product listing pages, competitor prices, brand specifications, or forum discussions.

## Step by Step Procedure
1. Verify the target URL complies with domain `robots.txt` rules using `urllib.robotparser`.
2. Check local disk cache (`data/cache/http/`) for a non-expired response. If found, return cached HTML.
3. Apply token-bucket delay to ensure at least 1.0 second between requests to the same origin.
4. Issue an asynchronous GET request via `httpx.AsyncClient` with a transparent User-Agent.
5. If the server responds with HTTP 429, apply exponential backoff (2s, 4s, 8s).
6. If the server responds with HTTP 403 or a CAPTCHA challenge, immediately abort, log the domain block, and mark the source as unavailable. Do not attempt evasion.
7. Parse response with `selectolax.parser.HTMLParser` or extract `<script type="application/ld+json">`.
8. If essential data cannot be found statically and client-side rendering is verified to be required, dispatch Playwright headless with disabled image and font downloads.
9. Write the response to disk cache.

## Code Patterns
```python
from selectolax.parser import HTMLParser
import json

def extract_json_ld(html: str) -> dict | None:
    parser = HTMLParser(html)
    for node in parser.css('script[type="application/ld+json"]'):
        try:
            data = json.loads(node.text())
            if isinstance(data, dict) and data.get("@type") in ("Product", "IndividualProduct"):
                return data
        except (json.JSONDecodeError, TypeError):
            continue
    return None
```

## Pitfalls
- Storing uncompressed HTML can fill disk space: clean old cache files periodically.
- Treating HTTP 403 as a retryable error leads to IP blocks: stop on 403 immediately.
- Forgetting to extract color or size variants leads to inaccurate availability flags.

## Done Checklist
- [ ] Robots.txt check passed or mocked in test.
- [ ] Token-bucket rate limiter enforced.
- [ ] Disk cache key generated using SHA-256 of canonical URL.
- [ ] Error status codes handled without infinite retries.
- [ ] Source marked unavailable if access is blocked.
