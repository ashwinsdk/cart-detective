"""REST API endpoints and SSE stream handler for Cart Detective."""

import asyncio
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from backend.config import settings
from backend.database import get_db
from backend.pipeline.orchestrator import orchestrator
from backend.repository import Repository

router = APIRouter(prefix="/api", tags=["api"])


class CreateSearchRequest(BaseModel):
    product_type: str = Field(..., min_length=2)
    budget_min: float | None = None
    budget_max: float | None = None
    currency: str = "INR"
    color_preferences: list[str] = Field(default_factory=list)
    size_fit_gender: str | None = None
    must_haves: str | None = None
    deal_breakers: str | None = None
    brands_included: list[str] = Field(default_factory=list)
    brands_excluded: list[str] = Field(default_factory=list)
    marketplaces: list[str] = Field(default_factory=list)


class AddWishlistRequest(BaseModel):
    product_id: str
    notes: str | None = None


class RecordPurchaseRequest(BaseModel):
    product_id: str
    price_paid: float
    currency: str = "INR"
    store: str = ""
    notes: str | None = None


class UpdateSettingsRequest(BaseModel):
    settings: dict[str, Any]


# Search Endpoints
@router.post("/searches", status_code=status.HTTP_201_CREATED)
async def create_search(
    payload: CreateSearchRequest,
    db: AsyncSession = Depends(get_db),
):
    repo = Repository(db)
    search = await repo.create_search(
        product_type=payload.product_type,
        budget_min=payload.budget_min,
        budget_max=payload.budget_max,
        currency=payload.currency,
        color_preferences=payload.color_preferences,
        size_fit_gender=payload.size_fit_gender,
        must_haves=payload.must_haves,
        deal_breakers=payload.deal_breakers,
        brands_included=payload.brands_included,
        brands_excluded=payload.brands_excluded,
        marketplaces=payload.marketplaces,
    )
    run = await repo.create_run(search.id)
    await db.commit()

    # Launch background async task
    asyncio.create_task(
        orchestrator.run_pipeline(
            search_id=search.id,
            run_id=run.id,
            raw_query=payload.model_dump(),
        )
    )

    return {
        "search_id": search.id,
        "run_id": run.id,
        "status": run.status,
        "created_at": search.created_at.isoformat(),
    }


@router.get("/searches")
async def list_searches(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    repo = Repository(db)
    searches = await repo.list_searches(limit=limit, offset=offset)
    return [
        {
            "id": s.id,
            "created_at": s.created_at.isoformat(),
            "product_type": s.product_type,
            "budget_min": s.budget_min,
            "budget_max": s.budget_max,
            "currency": s.currency,
            "color_preferences": s.color_preferences,
            "latest_run_id": s.runs[-1].id if s.runs else None,
            "latest_status": s.runs[-1].status if s.runs else None,
        }
        for s in searches
    ]


# Run Endpoints
@router.get("/runs/{run_id}")
async def get_run_status(
    run_id: str,
    db: AsyncSession = Depends(get_db),
):
    repo = Repository(db)
    run = await repo.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    return {
        "id": run.id,
        "search_id": run.search_id,
        "status": run.status,
        "current_stage": run.current_stage,
        "stage_progress": run.stage_progress,
        "error_message": run.error_message,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "logs": run.logs or [],
        "product_count": len(run.products),
    }


@router.get("/runs/{run_id}/stream")
async def stream_run_progress(run_id: str):
    return EventSourceResponse(orchestrator.sse_generator(run_id))


@router.get("/runs/{run_id}/products")
async def get_run_products(
    run_id: str,
    db: AsyncSession = Depends(get_db),
):
    repo = Repository(db)
    products = await repo.list_products_for_run(run_id)

    results = []
    for p in products:
        results.append(
            {
                "id": p.id,
                "canonical_brand": p.canonical_brand,
                "canonical_model": p.canonical_model,
                "title": p.title,
                "description": p.description,
                "primary_category": p.primary_category,
                "specs": p.specs,
                "score": p.score,
                "confidence": p.confidence,
                "pros": p.pros,
                "cons": p.cons,
                "verdict": p.verdict,
                "offers": [
                    {
                        "id": o.id,
                        "seller_name": o.seller_name,
                        "url": o.url,
                        "price": o.price,
                        "currency": o.currency,
                        "in_stock": o.in_stock,
                        "color_available": o.color_available,
                        "size_available": o.size_available,
                        "status": o.status,
                        "checked_at": o.checked_at.isoformat(),
                    }
                    for o in p.offers
                ],
                "reviews": [
                    {
                        "id": r.id,
                        "source": r.source,
                        "url": r.url,
                        "author": r.author,
                        "rating": r.rating,
                        "content": r.content,
                        "sentiment_score": r.sentiment_score,
                        "is_verified_purchase": r.is_verified_purchase,
                    }
                    for r in p.reviews
                ],
                "videos": [
                    {
                        "id": v.id,
                        "youtube_video_id": v.youtube_video_id,
                        "title": v.title,
                        "channel_title": v.channel_title,
                        "url": v.url,
                        "transcript_summary": v.transcript_summary,
                        "is_sponsored": v.is_sponsored,
                        "view_count": v.view_count,
                    }
                    for v in p.videos
                ],
                "evidence": [
                    {
                        "id": e.id,
                        "claim": e.claim,
                        "source_url": e.source_url,
                        "source_title": e.source_title,
                        "verification_status": e.verification_status,
                    }
                    for e in p.evidence
                ],
            }
        )

    return results


@router.get("/products/{product_id}")
async def get_product_detail(
    product_id: str,
    db: AsyncSession = Depends(get_db),
):
    repo = Repository(db)
    product = await repo.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return {
        "id": product.id,
        "canonical_brand": product.canonical_brand,
        "canonical_model": product.canonical_model,
        "title": product.title,
        "description": product.description,
        "specs": product.specs,
        "score": product.score,
        "confidence": product.confidence,
        "pros": product.pros,
        "cons": product.cons,
        "verdict": product.verdict,
        "offers": [
            {
                "seller_name": o.seller_name,
                "url": o.url,
                "price": o.price,
                "currency": o.currency,
                "in_stock": o.in_stock,
                "status": o.status,
            }
            for o in product.offers
        ],
        "evidence": [
            {
                "claim": e.claim,
                "source_url": e.source_url,
                "verification_status": e.verification_status,
            }
            for e in product.evidence
        ],
    }


# Wishlist Endpoints
@router.get("/wishlist")
async def get_wishlist(db: AsyncSession = Depends(get_db)):
    repo = Repository(db)
    items = await repo.list_wishlist()
    return [
        {
            "id": w.id,
            "product_id": w.product_id,
            "notes": w.notes,
            "added_at": w.added_at.isoformat(),
            "product": {
                "title": w.product.title,
                "brand": w.product.canonical_brand,
                "score": w.product.score,
                "price": w.product.offers[0].price if w.product.offers else 0.0,
                "currency": w.product.offers[0].currency if w.product.offers else "INR",
            }
            if w.product
            else None,
        }
        for w in items
    ]


@router.post("/wishlist", status_code=status.HTTP_201_CREATED)
async def add_to_wishlist(
    payload: AddWishlistRequest,
    db: AsyncSession = Depends(get_db),
):
    repo = Repository(db)
    item = await repo.add_wishlist_item(payload.product_id, notes=payload.notes)
    await db.commit()
    return {"id": item.id, "product_id": item.product_id, "added_at": item.added_at.isoformat()}


@router.delete("/wishlist/{item_id}")
async def remove_from_wishlist(
    item_id: str,
    db: AsyncSession = Depends(get_db),
):
    repo = Repository(db)
    deleted = await repo.remove_wishlist_item(item_id)
    await db.commit()
    if not deleted:
        raise HTTPException(status_code=404, detail="Wishlist item not found")
    return {"status": "deleted", "id": item_id}


# Purchases Endpoints
@router.get("/purchases")
async def list_purchases(db: AsyncSession = Depends(get_db)):
    repo = Repository(db)
    purchases = await repo.list_purchases()
    return [
        {
            "id": p.id,
            "product_id": p.product_id,
            "price_paid": p.price_paid,
            "currency": p.currency,
            "store": p.store,
            "purchase_date": p.purchase_date.isoformat(),
            "notes": p.notes,
            "product_title": p.product.title if p.product else "Unknown",
        }
        for p in purchases
    ]


@router.post("/purchases", status_code=status.HTTP_201_CREATED)
async def record_purchase(
    payload: RecordPurchaseRequest,
    db: AsyncSession = Depends(get_db),
):
    repo = Repository(db)
    purchase = await repo.record_purchase(
        product_id=payload.product_id,
        price_paid=payload.price_paid,
        currency=payload.currency,
        store=payload.store,
        notes=payload.notes,
    )
    await db.commit()
    return {"id": purchase.id, "price_paid": purchase.price_paid}


# Settings Endpoints
@router.get("/settings")
async def get_settings(db: AsyncSession = Depends(get_db)):
    repo = Repository(db)
    all_settings = await repo.get_all_settings()
    return {
        "scoring_weights": all_settings.get(
            "scoring_weights",
            {
                "budget_fit": 0.20,
                "spec_match": 0.20,
                "review_sentiment": 0.20,
                "brand_reliability": 0.15,
                "youtube_consensus": 0.15,
                "stock_seller_trust": 0.10,
            },
        ),
        "provider_status": {
            "groq_configured": bool(settings.GROQ_API_KEY),
            "youtube_configured": bool(settings.YOUTUBE_API_KEY),
            "brave_configured": bool(settings.BRAVE_SEARCH_API_KEY),
            "llm_provider": settings.LLM_PROVIDER,
            "llm_model": settings.LLM_MODEL,
        },
    }


@router.put("/settings")
async def update_settings(
    payload: UpdateSettingsRequest,
    db: AsyncSession = Depends(get_db),
):
    repo = Repository(db)
    for k, v in payload.settings.items():
        await repo.set_setting(k, v)
    await db.commit()
    return {"status": "updated", "keys": list(payload.settings.keys())}
