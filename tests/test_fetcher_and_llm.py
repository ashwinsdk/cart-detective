"""Unit tests for shared fetch layer and pluggable LLM provider."""

import time

import httpx
import pytest

from backend.services.fetcher import DiskCache, RateLimiter, SharedFetcher
from backend.services.llm import GroqProvider, HeuristicProvider


def test_disk_cache(tmp_path):
    cache = DiskCache(tmp_path)
    url = "https://example.com/test-product"

    # Miss
    assert cache.get(url) is None

    # Set
    cache.set(url, 200, "<html>product</html>")

    # Hit
    cached = cache.get(url, max_age_seconds=60)
    assert cached is not None
    assert cached.status_code == 200
    assert cached.text == "<html>product</html>"
    assert cached.from_cache is True

    # Expiry
    time.sleep(0.02)
    assert cache.get(url, max_age_seconds=0.01) is None


@pytest.mark.asyncio
async def test_rate_limiter():
    limiter = RateLimiter(default_delay=0.1)
    start = time.monotonic()
    await limiter.acquire("domain-a.com")
    await limiter.acquire("domain-a.com")
    elapsed = time.monotonic() - start
    assert elapsed >= 0.09


@pytest.mark.asyncio
async def test_heuristic_llm_provider():
    provider = HeuristicProvider()

    raw_query = {
        "product_type": "riding jacket under 12000 INR",
        "budget_min": 6000,
        "color_preferences": ["black", "grey"],
        "must_haves": "level 2 back protector",
        "deal_breakers": "no mesh",
    }
    spec = await provider.parse_query_spec(raw_query)
    assert spec.budget_max == 12000.0
    assert spec.budget_min == 6000.0
    assert "black" in spec.color_preferences
    assert any("CE Level 2" in s for s in spec.standards_and_certifications)
    assert "no mesh" in spec.red_flags

    # Review extraction
    review_text = (
        "This jacket is excellent and solid build. Very durable stitching. "
        "However it is quite heavy in summer. #ad sponsored by brand."
    )
    claims = await provider.extract_review_claims(review_text)
    assert claims.is_sponsored is True
    assert claims.sentiment_score > 0
    assert len(claims.pros) > 0


@pytest.mark.asyncio
async def test_groq_provider_fallback_without_key():
    provider = GroqProvider(api_key="")
    raw_query = {"product_type": "running shoes", "budget_max": 5000}
    spec = await provider.parse_query_spec(raw_query)
    assert spec.product_type == "running shoes"
    assert spec.budget_max == 5000


@pytest.mark.asyncio
async def test_shared_fetcher_with_mock_transport(tmp_path):
    def mock_handler(request: httpx.Request) -> httpx.Response:
        url_str = str(request.url)
        if "robots.txt" in url_str:
            return httpx.Response(200, text="User-agent: *\nDisallow: /private/\n")
        if "/private/" in url_str:
            return httpx.Response(403, text="Forbidden")
        if "/blocked" in url_str:
            return httpx.Response(403, text="Access denied")
        return httpx.Response(200, text="<html>sample content</html>")

    transport = httpx.MockTransport(mock_handler)
    fetcher = SharedFetcher(cache_dir=tmp_path, rate_limit_delay=0.01)

    # Replace httpx.AsyncClient call via monkeypatching or testing with direct mock
    # Testing robots.txt blocking
    async with httpx.AsyncClient(transport=transport) as client:
        allowed = await fetcher.robots.can_fetch("https://example.com/public/item", client)
        assert allowed is True

        disallowed = await fetcher.robots.can_fetch("https://example.com/private/item", client)
        assert disallowed is False
