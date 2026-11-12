"""Integration tests for FastAPI REST endpoints and SSE streaming."""

import pytest
from httpx import ASGITransport, AsyncClient

from backend.database import Base, get_session_factory
from backend.main import app
from backend.pipeline.orchestrator import orchestrator


@pytest.fixture(autouse=True)
async def setup_test_db():
    session_factory = get_session_factory()
    async with session_factory() as session:
        engine = session.bind
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
    yield


@pytest.mark.asyncio
async def test_search_and_run_api():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Create Search
        res = await client.post(
            "/api/searches",
            json={
                "product_type": "riding jacket",
                "budget_min": 5000,
                "budget_max": 12000,
                "currency": "INR",
                "color_preferences": ["black"],
                "must_haves": "CE level 2 armor",
            },
        )
        assert res.status_code == 201
        data = res.json()
        assert "search_id" in data
        assert "run_id" in data
        run_id = data["run_id"]

        # 2. Get Run status
        res_run = await client.get(f"/api/runs/{run_id}")
        assert res_run.status_code == 200
        run_data = res_run.json()
        assert run_data["id"] == run_id

        # 3. List Searches
        res_list = await client.get("/api/searches")
        assert res_list.status_code == 200
        searches = res_list.json()
        assert len(searches) >= 1
        assert searches[0]["product_type"] == "riding jacket"


@pytest.mark.asyncio
async def test_settings_api():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/settings")
        assert res.status_code == 200
        data = res.json()
        assert "scoring_weights" in data
        assert "provider_status" in data

        # Update setting
        res_put = await client.put(
            "/api/settings",
            json={"settings": {"scoring_weights": {"budget_fit": 0.5, "spec_match": 0.5}}},
        )
        assert res_put.status_code == 200
        assert res_put.json()["status"] == "updated"


@pytest.mark.asyncio
async def test_wishlist_and_purchases_api():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create a search and wait briefly for background pipeline
        res_s = await client.post(
            "/api/searches",
            json={"product_type": "running shoes", "budget_max": 5000},
        )
        run_id = res_s.json()["run_id"]

        # Directly simulate product persistence for unit isolation
        session_factory = get_session_factory()
        from backend.repository import Repository

        async with session_factory() as session:
            repo = Repository(session)
            product = await repo.create_product(
                run_id=run_id,
                canonical_brand="Asics",
                canonical_model="Gel Kayano 30",
                title="Asics Gel Kayano 30",
            )
            await session.commit()
            product_id = product.id

        # Wishlist test
        res_w = await client.post(
            "/api/wishlist",
            json={"product_id": product_id, "notes": "Save for later"},
        )
        assert res_w.status_code == 201
        w_id = res_w.json()["id"]

        res_w_list = await client.get("/api/wishlist")
        assert res_w_list.status_code == 200
        assert len(res_w_list.json()) == 1

        # Delete wishlist
        res_del = await client.delete(f"/api/wishlist/{w_id}")
        assert res_del.status_code == 200

        # Purchase test
        res_p = await client.post(
            "/api/purchases",
            json={
                "product_id": product_id,
                "price_paid": 4999.0,
                "store": "Amazon.in",
            },
        )
        assert res_p.status_code == 201

        res_p_list = await client.get("/api/purchases")
        assert res_p_list.status_code == 200
        assert len(res_p_list.json()) == 1


@pytest.mark.asyncio
async def test_orchestrator_sse_broadcasting():
    run_id = "test-sse-run"
    queue = await orchestrator.register_listener(run_id)

    await orchestrator.broadcast_event(run_id, "stage_start", {"stage": 1, "name": "Understand"})
    event = await queue.get()
    assert event["event"] == "stage_start"
    assert event["stage"] == 1
    assert event["name"] == "Understand"

    await orchestrator.unregister_listener(run_id, queue)
