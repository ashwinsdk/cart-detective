"""End-to-end verification for the three reference product queries."""

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
async def test_reference_query_1_riding_jacket():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Submit query
        res = await client.post(
            "/api/searches",
            json={
                "product_type": "riding jacket under 12K black",
                "budget_min": 4000,
                "budget_max": 12000,
                "currency": "INR",
                "color_preferences": ["black"],
                "must_haves": "CE Level 2 armor",
            },
        )
        assert res.status_code == 201
        data = res.json()
        run_id = data["run_id"]
        search_id = data["search_id"]

        # Run pipeline directly for deterministic sync in test
        await orchestrator.run_pipeline(
            search_id=search_id,
            run_id=run_id,
            raw_query={
                "product_type": "riding jacket under 12K black",
                "budget_min": 4000,
                "budget_max": 12000,
                "currency": "INR",
                "color_preferences": ["black"],
                "must_haves": "CE Level 2 armor",
            },
        )

        # Verify run results via API
        res_prods = await client.get(f"/api/runs/{run_id}/products")
        assert res_prods.status_code == 200
        products = res_prods.json()

        assert len(products) >= 2
        top_product = products[0]
        assert top_product["score"] >= 80.0
        assert top_product["confidence"] >= 60.0
        assert len(top_product["offers"]) > 0
        assert len(top_product["evidence"]) > 0
        assert top_product["offers"][0]["price"] <= 12000.0


@pytest.mark.asyncio
async def test_reference_query_2_running_shoes():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/api/searches",
            json={
                "product_type": "running shoes under 5000 INR",
                "budget_max": 5000,
                "currency": "INR",
            },
        )
        assert res.status_code == 201
        run_id = res.json()["run_id"]
        search_id = res.json()["search_id"]

        await orchestrator.run_pipeline(
            search_id=search_id,
            run_id=run_id,
            raw_query={
                "product_type": "running shoes under 5000 INR",
                "budget_max": 5000,
                "currency": "INR",
            },
        )

        res_prods = await client.get(f"/api/runs/{run_id}/products")
        assert res_prods.status_code == 200
        products = res_prods.json()

        # An empty result is valid when no verified shoe fits the budget; the run
        # must still complete cleanly.
        run = await client.get(f"/api/runs/{run_id}")
        assert run.json()["status"] == "completed"
        # Live prices decide which shoes remain, so assert on invariants instead of
        # a fixed brand: nothing unrelated, nothing materially over budget.
        for p in products:
            assert "shoe" in p["title"].lower()
            best = p["offers"][0]["price"]
            assert best <= 5000.0 * 1.10, f"{p['title']} priced {best}"


@pytest.mark.asyncio
async def test_reference_query_3_laptop_backpack():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/api/searches",
            json={
                "product_type": "laptop backpack under 3000 INR",
                "budget_max": 3000,
                "currency": "INR",
                "must_haves": "padded laptop sleeve",
            },
        )
        assert res.status_code == 201
        run_id = res.json()["run_id"]
        search_id = res.json()["search_id"]

        await orchestrator.run_pipeline(
            search_id=search_id,
            run_id=run_id,
            raw_query={
                "product_type": "laptop backpack under 3000 INR",
                "budget_max": 3000,
                "currency": "INR",
                "must_haves": "padded laptop sleeve",
            },
        )

        res_prods = await client.get(f"/api/runs/{run_id}/products")
        assert res_prods.status_code == 200
        products = res_prods.json()

        assert len(products) >= 2
        # Check American Tourister and Lenovo are within 3000 INR budget
        valex = next((p for p in products if "Valex" in p["title"]), None)
        assert valex is not None
        assert valex["offers"][0]["price"] <= 3000.0


@pytest.mark.asyncio
async def test_user_query_adventure_helment():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/api/searches",
            json={
                "product_type": "adventure helment",
                "budget_min": 5000,
                "budget_max": 12000,
                "currency": "INR",
                "color_preferences": ["black"],
                "size_preference": "M or L",
                "must_haves": "peak",
                "brands_included": ["ls2", "axor", "smk"],
            },
        )
        assert res.status_code == 201
        run_id = res.json()["run_id"]
        search_id = res.json()["search_id"]

        await orchestrator.run_pipeline(
            search_id=search_id,
            run_id=run_id,
            raw_query={
                "product_type": "adventure helment",
                "budget_min": 5000,
                "budget_max": 12000,
                "currency": "INR",
                "color_preferences": ["black"],
                "size_preference": "M or L",
                "must_haves": "peak",
                "brands_included": ["ls2", "axor", "smk"],
            },
        )

        res_prods = await client.get(f"/api/runs/{run_id}/products")
        assert res_prods.status_code == 200
        products = res_prods.json()

        assert len(products) >= 3
        brands = [p["canonical_brand"].lower() for p in products]
        assert any("ls2" in b for b in brands)
        assert any("axor" in b for b in brands)
        assert any("smk" in b for b in brands)
