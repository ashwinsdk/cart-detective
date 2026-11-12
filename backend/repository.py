"""Repository layer providing async CRUD operations for Cart Detective."""

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models import (
    Evidence,
    Offer,
    Product,
    Purchase,
    Review,
    Run,
    Search,
    Setting,
    Video,
    WishlistItem,
)


class Repository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # Searches
    async def create_search(
        self,
        product_type: str,
        budget_min: float | None = None,
        budget_max: float | None = None,
        currency: str = "INR",
        color_preferences: list[str] | None = None,
        size_fit_gender: str | None = None,
        must_haves: str | None = None,
        deal_breakers: str | None = None,
        brands_included: list[str] | None = None,
        brands_excluded: list[str] | None = None,
        marketplaces: list[str] | None = None,
    ) -> Search:
        search = Search(
            product_type=product_type,
            budget_min=budget_min,
            budget_max=budget_max,
            currency=currency,
            color_preferences=color_preferences or [],
            size_fit_gender=size_fit_gender,
            must_haves=must_haves,
            deal_breakers=deal_breakers,
            brands_included=brands_included or [],
            brands_excluded=brands_excluded or [],
            marketplaces=marketplaces or [],
        )
        self.session.add(search)
        await self.session.flush()
        return search

    async def get_search(self, search_id: str) -> Search | None:
        stmt = select(Search).options(selectinload(Search.runs)).where(Search.id == search_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_searches(self, limit: int = 20, offset: int = 0) -> Sequence[Search]:
        stmt = (
            select(Search)
            .options(selectinload(Search.runs))
            .order_by(desc(Search.created_at))
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    # Runs
    async def create_run(self, search_id: str) -> Run:
        run = Run(search_id=search_id, status="pending", current_stage=1, stage_progress=0.0)
        self.session.add(run)
        await self.session.flush()
        return run

    async def get_run(self, run_id: str) -> Run | None:
        stmt = (
            select(Run)
            .options(
                selectinload(Run.search),
                selectinload(Run.products).selectinload(Product.offers),
                selectinload(Run.products).selectinload(Product.reviews),
                selectinload(Run.products).selectinload(Product.videos),
                selectinload(Run.products).selectinload(Product.evidence),
            )
            .where(Run.id == run_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_run_progress(
        self,
        run_id: str,
        stage: int,
        progress: float,
        log_message: str | None = None,
        log_level: str = "INFO",
    ) -> None:
        run = await self.session.get(Run, run_id)
        if run:
            run.current_stage = stage
            run.stage_progress = progress
            if log_message:
                current_logs = list(run.logs or [])
                current_logs.append(
                    {
                        "timestamp": datetime.now(UTC).isoformat(),
                        "level": log_level,
                        "stage": stage,
                        "message": log_message,
                    }
                )
                run.logs = current_logs
            await self.session.flush()

    async def update_run_status(
        self,
        run_id: str,
        status: str,
        error_message: str | None = None,
    ) -> None:
        run = await self.session.get(Run, run_id)
        if run:
            run.status = status
            if error_message:
                run.error_message = error_message
            if status in ("completed", "failed", "cancelled"):
                run.completed_at = datetime.now(UTC)
            await self.session.flush()

    # Products
    async def create_product(
        self,
        run_id: str,
        canonical_brand: str,
        canonical_model: str,
        title: str,
        description: str = "",
        primary_category: str = "",
        specs: dict[str, Any] | None = None,
        score: float = 0.0,
        confidence: float = 0.0,
        pros: list[str] | None = None,
        cons: list[str] | None = None,
        verdict: str = "",
    ) -> Product:
        product = Product(
            run_id=run_id,
            canonical_brand=canonical_brand,
            canonical_model=canonical_model,
            title=title,
            description=description,
            primary_category=primary_category,
            specs=specs or {},
            score=score,
            confidence=confidence,
            pros=pros or [],
            cons=cons or [],
            verdict=verdict,
        )
        self.session.add(product)
        await self.session.flush()
        return product

    async def get_product(self, product_id: str) -> Product | None:
        stmt = (
            select(Product)
            .options(
                selectinload(Product.offers),
                selectinload(Product.reviews),
                selectinload(Product.videos),
                selectinload(Product.evidence),
                selectinload(Product.wishlist_items),
                selectinload(Product.purchases),
            )
            .where(Product.id == product_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_products_for_run(self, run_id: str) -> Sequence[Product]:
        stmt = (
            select(Product)
            .options(
                selectinload(Product.offers),
                selectinload(Product.reviews),
                selectinload(Product.videos),
                selectinload(Product.evidence),
            )
            .where(Product.run_id == run_id)
            .order_by(desc(Product.score))
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    # Child entities
    async def add_offer(
        self,
        product_id: str,
        seller_name: str,
        url: str,
        price: float,
        currency: str = "INR",
        in_stock: bool = True,
        color_available: bool = True,
        size_available: bool = True,
        status: str = "verified",
    ) -> Offer:
        offer = Offer(
            product_id=product_id,
            seller_name=seller_name,
            url=url,
            price=price,
            currency=currency,
            in_stock=in_stock,
            color_available=color_available,
            size_available=size_available,
            status=status,
        )
        self.session.add(offer)
        await self.session.flush()
        return offer

    async def add_review(
        self,
        product_id: str,
        source: str,
        url: str = "",
        author: str = "",
        rating: float | None = None,
        content: str = "",
        sentiment_score: float = 0.0,
        is_verified_purchase: bool = False,
        fake_probability: float = 0.0,
    ) -> Review:
        review = Review(
            product_id=product_id,
            source=source,
            url=url,
            author=author,
            rating=rating,
            content=content,
            sentiment_score=sentiment_score,
            is_verified_purchase=is_verified_purchase,
            fake_probability=fake_probability,
        )
        self.session.add(review)
        await self.session.flush()
        return review

    async def add_video(
        self,
        product_id: str,
        youtube_video_id: str,
        title: str,
        channel_title: str = "",
        url: str = "",
        transcript_summary: str = "",
        is_sponsored: bool = False,
        view_count: int = 0,
    ) -> Video:
        video = Video(
            product_id=product_id,
            youtube_video_id=youtube_video_id,
            title=title,
            channel_title=channel_title,
            url=url,
            transcript_summary=transcript_summary,
            is_sponsored=is_sponsored,
            view_count=view_count,
        )
        self.session.add(video)
        await self.session.flush()
        return video

    async def add_evidence(
        self,
        product_id: str,
        claim: str,
        source_url: str,
        source_title: str = "",
        verification_status: str = "verified",
    ) -> Evidence:
        evidence = Evidence(
            product_id=product_id,
            claim=claim,
            source_url=source_url,
            source_title=source_title,
            verification_status=verification_status,
        )
        self.session.add(evidence)
        await self.session.flush()
        return evidence

    # Wishlist
    async def add_wishlist_item(self, product_id: str, notes: str | None = None) -> WishlistItem:
        item = WishlistItem(product_id=product_id, notes=notes)
        self.session.add(item)
        await self.session.flush()
        return item

    async def list_wishlist(self) -> Sequence[WishlistItem]:
        stmt = (
            select(WishlistItem)
            .options(
                selectinload(WishlistItem.product).selectinload(Product.offers),
            )
            .order_by(desc(WishlistItem.added_at))
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def remove_wishlist_item(self, item_id: str) -> bool:
        item = await self.session.get(WishlistItem, item_id)
        if item:
            await self.session.delete(item)
            await self.session.flush()
            return True
        return False

    # Purchases
    async def record_purchase(
        self,
        product_id: str,
        price_paid: float,
        currency: str = "INR",
        store: str = "",
        notes: str | None = None,
    ) -> Purchase:
        purchase = Purchase(
            product_id=product_id,
            price_paid=price_paid,
            currency=currency,
            store=store,
            notes=notes,
        )
        self.session.add(purchase)
        await self.session.flush()
        return purchase

    async def list_purchases(self) -> Sequence[Purchase]:
        stmt = (
            select(Purchase)
            .options(
                selectinload(Purchase.product),
            )
            .order_by(desc(Purchase.created_at))
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    # Settings
    async def get_setting(self, key: str, default: Any = None) -> Any:
        setting = await self.session.get(Setting, key)
        if setting:
            return setting.value
        return default

    async def set_setting(self, key: str, value: Any) -> None:
        setting = await self.session.get(Setting, key)
        if setting:
            setting.value = value
        else:
            setting = Setting(key=key, value=value)
            self.session.add(setting)
        await self.session.flush()

    async def get_all_settings(self) -> dict[str, Any]:
        stmt = select(Setting)
        result = await self.session.execute(stmt)
        settings = result.scalars().all()
        return {s.key: s.value for s in settings}
