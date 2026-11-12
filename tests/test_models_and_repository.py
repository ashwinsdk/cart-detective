"""Tests for data models and repository layer."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.database import Base
from backend.repository import Repository


@pytest.fixture
async def async_session() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_search_and_run_lifecycle(async_session: AsyncSession):
    repo = Repository(async_session)

    # 1. Create Search
    search = await repo.create_search(
        product_type="riding jacket",
        budget_min=5000,
        budget_max=12000,
        currency="INR",
        color_preferences=["black", "grey"],
        size_fit_gender="men XL",
        must_haves="CE level 2 armor",
        deal_breakers="mesh only",
        brands_included=["Rynox", "Royal Enfield"],
    )
    assert search.id is not None
    assert search.product_type == "riding jacket"
    assert search.currency == "INR"
    assert "black" in search.color_preferences

    # 2. Create Run
    run = await repo.create_run(search.id)
    assert run.id is not None
    assert run.status == "pending"
    assert run.current_stage == 1

    # 3. Update Run progress
    await repo.update_run_progress(
        run.id, stage=2, progress=35.0, log_message="Discovered candidates"
    )
    updated_run = await repo.get_run(run.id)
    assert updated_run is not None
    assert updated_run.current_stage == 2
    assert updated_run.stage_progress == 35.0
    assert len(updated_run.logs) == 1
    assert updated_run.logs[0]["message"] == "Discovered candidates"

    # 4. Create Product with children
    product = await repo.create_product(
        run_id=run.id,
        canonical_brand="Rynox",
        canonical_model="Stealth Evo 3",
        title="Rynox Stealth Evo 3 Riding Jacket",
        description="All weather touring jacket with CE level 2 protectors.",
        specs={"armor": "CE Level 2", "material": "Cordura 600D"},
        score=88.5,
        confidence=92.0,
        pros=["High impact protection", "Excellent ventilation"],
        cons=["Heavy for summer city commutes"],
        verdict="Top touring choice with certified impact armor.",
    )
    assert product.id is not None
    assert product.score == 88.5

    # 5. Add Offer, Review, Video, Evidence
    offer = await repo.add_offer(
        product_id=product.id,
        seller_name="Amazon.in",
        url="https://amazon.in/dp/B00EXAMPLE",
        price=10750.0,
        color_available=True,
        size_available=True,
    )
    assert offer.price == 10750.0

    review = await repo.add_review(
        product_id=product.id,
        source="reddit",
        author="moto_rider",
        content="Survived a 40 kmh slide with zero rash.",
        sentiment_score=0.9,
        is_verified_purchase=True,
    )
    assert review.sentiment_score == 0.9

    video = await repo.add_video(
        product_id=product.id,
        youtube_video_id="dQw4w9WgXcQ",
        title="Rynox Stealth Evo Long Term Review",
        url="https://youtube.com/watch?v=dQw4w9WgXcQ",
        transcript_summary="Reviewer praises construction and zipper durability.",
        is_sponsored=False,
    )
    assert video.is_sponsored is False

    evidence = await repo.add_evidence(
        product_id=product.id,
        claim="CE Level 2 armor for shoulders and elbows",
        source_url="https://rynoxgear.com/specs",
        source_title="Official Rynox Specifications",
        verification_status="verified",
    )
    assert evidence.verification_status == "verified"

    # 6. Verify product query with relations
    fetched_product = await repo.get_product(product.id)
    assert fetched_product is not None
    assert len(fetched_product.offers) == 1
    assert len(fetched_product.reviews) == 1
    assert len(fetched_product.videos) == 1
    assert len(fetched_product.evidence) == 1


@pytest.mark.asyncio
async def test_wishlist_and_purchases(async_session: AsyncSession):
    repo = Repository(async_session)

    search = await repo.create_search(product_type="running shoes")
    run = await repo.create_run(search.id)
    product = await repo.create_product(
        run_id=run.id,
        canonical_brand="Asics",
        canonical_model="Gel Kayano 30",
        title="Asics Gel Kayano 30 Running Shoes",
    )

    # Wishlist
    item = await repo.add_wishlist_item(product.id, notes="Wait for summer sale")
    assert item.id is not None
    wishlist = await repo.list_wishlist()
    assert len(wishlist) == 1
    assert wishlist[0].notes == "Wait for summer sale"

    # Purchase
    purchase = await repo.record_purchase(
        product_id=product.id,
        price_paid=11999.0,
        currency="INR",
        store="Asics Store Bangalore",
        notes="Purchased in store with discount",
    )
    assert purchase.id is not None
    assert purchase.price_paid == 11999.0

    purchases = await repo.list_purchases()
    assert len(purchases) == 1
    assert purchases[0].store == "Asics Store Bangalore"

    # Remove Wishlist
    removed = await repo.remove_wishlist_item(item.id)
    assert removed is True
    assert len(await repo.list_wishlist()) == 0


@pytest.mark.asyncio
async def test_settings_crud(async_session: AsyncSession):
    repo = Repository(async_session)

    weights = {
        "budget_fit": 0.2,
        "spec_match": 0.2,
        "review_sentiment": 0.2,
        "brand_reliability": 0.15,
        "youtube_consensus": 0.15,
        "stock_seller_trust": 0.1,
    }
    await repo.set_setting("scoring_weights", weights)
    saved_weights = await repo.get_setting("scoring_weights")
    assert saved_weights["budget_fit"] == 0.2

    # Update setting
    weights["budget_fit"] = 0.25
    await repo.set_setting("scoring_weights", weights)
    updated_weights = await repo.get_setting("scoring_weights")
    assert updated_weights["budget_fit"] == 0.25

    all_settings = await repo.get_all_settings()
    assert "scoring_weights" in all_settings
