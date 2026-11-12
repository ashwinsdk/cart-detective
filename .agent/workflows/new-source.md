# Workflow: Onboarding a New Data Source

This workflow defines the procedure for adding a new search, review, or video source to Cart Detective.

## Steps

1. **Review Terms and Robots Policy**:
   - Check `robots.txt` and terms of service for the target platform.
   - Ensure the source does not require authentication or CAPTCHA solving.
2. **Update Documentation**:
   - Add source details, rate limits, quotas, and fallback paths to `docs/DATA_SOURCES.md`.
3. **Implement Adapter**:
   - Create a dedicated adapter in `backend/scrapers/` or `backend/services/`.
   - Route all requests through the shared fetcher (`backend/services/fetcher.py`).
   - Implement exponential backoff for HTTP 429 and error isolation for HTTP 403.
4. **Add Unit Tests**:
   - Add test fixtures in `tests/fixtures/` and corresponding unit tests in `tests/test_sources.py`.
5. **Run Compliance**:
   - Verify zero emojis, zero dashes, and no committed credentials.
