# Workflow: Adding a Marketplace Scraper

This workflow outlines the standard procedure for adding a new ecommerce marketplace or specialist retailer scraper.

## Steps

1. **Investigate Markup Structure**:
   - Inspect target product pages for Schema.org JSON-LD microdata (`<script type="application/ld+json">`).
   - Identify static CSS selectors for price, seller name, stock, size options, and color options.
2. **Implement Parser**:
   - Write a dedicated parser inheriting from `BaseMarketplaceParser`.
   - Prefer fast static extraction using `selectolax.parser.HTMLParser`.
   - Fall back to Playwright only if content requires client-side JavaScript execution.
3. **Handle Degradation**:
   - If the marketplace blocks requests (HTTP 403 or anti-bot prompt), set product offer status to `unavailable`.
   - Never attempt login bypass or CAPTCHA solving.
4. **Register Marketplace**:
   - Add the marketplace key to settings and configuration defaults.
5. **Verify with Fixtures**:
   - Add an offline HTML fixture to `tests/fixtures/marketplaces/` and write a regression test verifying price and spec extraction.
