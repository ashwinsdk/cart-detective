"""Tests for scoring engine and Stage 7 ranking."""

import pytest

from backend.pipeline.context import PipelineContext
from backend.pipeline.stage1_understand import UnderstandStage
from backend.pipeline.stage2_discover import DiscoverStage
from backend.pipeline.stage3_brand import BrandResearchStage
from backend.pipeline.stage4_scrape import ScrapeStage
from backend.pipeline.stage5_reviews import ReviewMiningStage
from backend.pipeline.stage6_verify import VerificationStage
from backend.pipeline.stage7_score import ScoringStage
from backend.scoring import ScoringEngine


def test_budget_scoring():
    engine = ScoringEngine()

    # Within budget
    score_within = engine.compute_budget_score(price=9000.0, budget_min=5000.0, budget_max=12000.0)
    assert 80.0 <= score_within <= 100.0

    # Overshoot max budget
    score_over = engine.compute_budget_score(price=16000.0, budget_min=5000.0, budget_max=12000.0)
    assert score_over < score_within
    assert score_over >= 0.0


def test_spec_scoring_and_deal_breaker():
    engine = ScoringEngine()

    # Met specs
    verified = {
        "CE Level 2": {"status": "verified"},
        "Waterproofing": {"status": "unverified"},
    }
    score, pros, cons = engine.compute_spec_score(
        verified, mandatory_specs=["CE Level 2", "Waterproofing"], red_flags=[]
    )
    assert score == 75.0  # 1 verified (1.0) + 1 unverified (0.5) out of 2 = 75%
    assert len(pros) == 1
    assert len(cons) == 1

    # Deal breaker triggers 0 score
    score_flag, _, cons_flag = engine.compute_spec_score(
        verified, mandatory_specs=["CE Level 2"], red_flags=["CE Level 2"]
    )
    assert score_flag == 0.0
    assert any("Deal breaker" in c for c in cons_flag)


def test_custom_weights_override():
    custom_weights = {
        "budget_fit": 0.8,
        "spec_match": 0.1,
        "review_sentiment": 0.05,
        "brand_reliability": 0.05,
        "youtube_consensus": 0.0,
        "stock_seller_trust": 0.0,
    }
    engine = ScoringEngine(weights=custom_weights)
    assert engine.weights["budget_fit"] == 0.8


@pytest.mark.asyncio
async def test_stage_7_scoring_and_ranking_flow():
    ctx = PipelineContext(
        run_id="test-run-score",
        search_id="test-search-score",
        raw_query={
            "product_type": "riding jacket",
            "budget_max": 12000,
            "currency": "INR",
            "must_haves": "CE Level 2 armor",
        },
    )

    # Run stages 1 to 6
    await UnderstandStage().execute(ctx)
    await DiscoverStage().execute(ctx)
    await BrandResearchStage().execute(ctx)
    await ScrapeStage().execute(ctx)
    await ReviewMiningStage().execute(ctx)
    await VerificationStage().execute(ctx)

    # Run Stage 7
    stage7 = ScoringStage()
    await stage7.execute(ctx)

    assert ctx.telemetry.stage_status["stage7_score"] == "completed"
    active_candidates = [c for c in ctx.candidates if not c.is_dropped]
    assert len(active_candidates) >= 2

    # Check candidates are sorted in descending score order
    scores = [c.scraped_specs.get("score", 0.0) for c in active_candidates]
    assert scores == sorted(scores, reverse=True)

    # Check comparison table
    assert len(ctx.comparison_table) > 0
    assert "brand" in ctx.comparison_table[0]
    assert "score" in ctx.comparison_table[0]

    # Check verdict formatting
    top_cand = active_candidates[0]
    verdict = top_cand.scraped_specs.get("verdict", "")
    assert len(verdict) > 10
    assert "\u2014" not in verdict
    assert "\u2013" not in verdict
    assert not any(
        banned in verdict.lower() for banned in ["seamless", "supercharge", "unleash", "elevate"]
    )
