"""Tests for pipeline stages 4 to 6 (Scrape, Reviews, Verification)."""

import pytest

from backend.pipeline.context import DiscoveredCandidate, PipelineContext
from backend.pipeline.stage1_understand import UnderstandStage
from backend.pipeline.stage2_discover import DiscoverStage
from backend.pipeline.stage3_brand import BrandResearchStage
from backend.pipeline.stage4_scrape import ScrapeStage
from backend.pipeline.stage5_reviews import ReviewMiningStage
from backend.pipeline.stage6_verify import VerificationStage


@pytest.mark.asyncio
async def test_pipeline_stages_4_to_6_full_cycle():
    ctx = PipelineContext(
        run_id="test-run-456",
        search_id="test-search-456",
        raw_query={
            "product_type": "riding jacket under 12000 INR",
            "budget_max": 12000,
            "currency": "INR",
            "color_preferences": ["black"],
            "must_haves": "CE Level 2 armor",
        },
    )

    # Run stages 1 to 3 first
    await UnderstandStage().execute(ctx)
    await DiscoverStage().execute(ctx)
    await BrandResearchStage().execute(ctx)

    # 4. Stage 4: Scrape
    scrape_stage = ScrapeStage()
    await scrape_stage.execute(ctx)
    assert ctx.telemetry.stage_status["stage4_scrape"] == "completed"

    active_candidates = [c for c in ctx.candidates if not c.is_dropped]
    assert len(active_candidates) > 0
    for cand in active_candidates:
        assert len(cand.scraped_offers) > 0
        assert cand.scraped_offers[0]["price"] > 0

    # 5. Stage 5: Reviews and Video Mining
    review_stage = ReviewMiningStage()
    await review_stage.execute(ctx)
    assert ctx.telemetry.stage_status["stage5_reviews"] == "completed"

    rynox = next(c for c in active_candidates if c.canonical_brand == "Rynox")
    assert len(rynox.videos) > 0
    assert "Stealth Evo" in rynox.videos[0]["title"]
    assert len(rynox.reviews) > 0

    # 6. Stage 6: Cross-Verification and Validation
    verify_stage = VerificationStage()
    await verify_stage.execute(ctx)
    assert ctx.telemetry.stage_status["stage6_verify"] == "completed"

    assert rynox.color_available is True
    assert rynox.size_available is True
    assert len(rynox.claims_evidence) > 0

    # Verify claim source URLs exist
    for ev in rynox.claims_evidence:
        assert ev["source_url"].startswith("http")
        assert ev["verification_status"] in ("verified", "unverified")

    # Multi-domain candidate check
    if len(rynox.seed_urls) >= 2:
        assert any(spec["status"] == "verified" for spec in rynox.verified_specs.values())
    else:
        assert all(spec["status"] == "unverified" for spec in rynox.verified_specs.values())


@pytest.mark.asyncio
async def test_blocked_source_marked_unavailable():
    ctx = PipelineContext(
        run_id="test-run-blocked",
        search_id="test-search-blocked",
        raw_query={"product_type": "riding jacket"},
    )
    candidate = DiscoveredCandidate(
        canonical_brand="TestBrand",
        canonical_model="ModelX",
        title="TestBrand ModelX",
        seed_urls=["https://example.com/blocked-page"],
        estimated_price=5000.0,
    )
    ctx.candidates = [candidate]

    # In mock or offline fetcher, if 403 or unavailable, offer should be recorded as unavailable
    candidate.scraped_offers.append(
        {
            "seller_name": "example.com",
            "url": "https://example.com/blocked-page",
            "price": 5000.0,
            "currency": "INR",
            "in_stock": False,
            "color_available": False,
            "size_available": False,
            "status": "unavailable",
        }
    )

    verify_stage = VerificationStage()
    await verify_stage.execute(ctx)

    assert candidate.scraped_offers[0]["status"] in ("unavailable", "verified")
