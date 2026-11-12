"""Tests for pipeline stages 1 to 3 (Understand, Discover, Brand Research)."""

import pytest

from backend.pipeline.context import PipelineContext
from backend.pipeline.stage1_understand import UnderstandStage
from backend.pipeline.stage2_discover import DiscoverStage
from backend.pipeline.stage3_brand import BrandResearchStage


@pytest.mark.asyncio
async def test_pipeline_stages_1_to_3_riding_jacket():
    ctx = PipelineContext(
        run_id="test-run-001",
        search_id="test-search-001",
        raw_query={
            "product_type": "riding jacket under 12000 INR",
            "budget_min": 4000,
            "budget_max": 12000,
            "currency": "INR",
            "color_preferences": ["black"],
            "must_haves": "CE Level 2 armor",
            "deal_breakers": "no thermal liner",
            "brands_excluded": ["Alpinestars"],  # Exclude Alpinestars (above budget anyway)
        },
    )

    # 1. Stage 1: Understand
    stage1 = UnderstandStage()
    await stage1.execute(ctx)
    assert ctx.spec is not None
    assert ctx.spec.budget_max == 12000.0
    assert "stage1_understand" in ctx.telemetry.stage_durations_ms
    assert ctx.telemetry.stage_status["stage1_understand"] == "completed"

    # 2. Stage 2: Discover Candidates
    stage2 = DiscoverStage()
    await stage2.execute(ctx)
    assert len(ctx.candidates) > 0
    # Verify excluded brand was not included
    for candidate in ctx.candidates:
        assert candidate.canonical_brand.lower() != "alpinestars"
    assert any(c.canonical_brand == "Rynox" for c in ctx.candidates)

    # 3. Stage 3: Brand Research
    stage3 = BrandResearchStage()
    await stage3.execute(ctx)

    active_candidates = [c for c in ctx.candidates if not c.is_dropped]
    assert len(active_candidates) > 0
    for cand in active_candidates:
        assert cand.brand_signal is not None
        assert cand.brand_signal.reputation_score >= 50.0

    rynox = next(c for c in active_candidates if c.canonical_brand == "Rynox")
    assert rynox.brand_signal.reputation_score == 90.0
    assert "warranty" in rynox.brand_signal.warranty_summary.lower()


@pytest.mark.asyncio
async def test_pipeline_stages_running_shoes():
    ctx = PipelineContext(
        run_id="test-run-002",
        search_id="test-search-002",
        raw_query={
            "product_type": "running shoes",
            "budget_max": 6000,
            "currency": "INR",
        },
    )

    stage1 = UnderstandStage()
    await stage1.execute(ctx)

    stage2 = DiscoverStage()
    await stage2.execute(ctx)
    assert len(ctx.candidates) > 0

    stage3 = BrandResearchStage()
    await stage3.execute(ctx)
    assert all(c.brand_signal is not None for c in ctx.candidates)
