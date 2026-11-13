"""Regression tests for product search relevance (offline, search stubbed)."""

import pytest

from backend.pipeline import relevance
from backend.pipeline.context import DiscoveredCandidate, PipelineContext
from backend.pipeline.stage2_discover import DiscoverStage
from backend.pipeline.stage6_verify import VerificationStage
from backend.services.llm import HeuristicProvider


async def _ctx(raw: dict) -> PipelineContext:
    spec = await HeuristicProvider().parse_query_spec(raw)
    return PipelineContext(run_id="r", search_id="s", raw_query=raw, spec=spec)


def _stub_search(monkeypatch, results_by_query=None, default=None):
    calls: list[str] = []

    async def fake(self, query, currency):
        calls.append(query)
        if results_by_query:
            for key, val in results_by_query.items():
                if key in query:
                    return val
        return default or []

    monkeypatch.setattr(DiscoverStage, "_search", fake)
    return calls


# ---------------------------------------------------------------- relevance


def test_core_terms_strip_budget_color_and_plurals():
    assert relevance.core_terms("riding jacket under 12K black") == ["riding", "jacket"]
    assert relevance.core_terms("Running Shoes under 5000 INR") == ["running", "shoe"]
    assert relevance.core_terms("mobile holder for bike") == ["mobile", "holder", "bike"]


@pytest.mark.parametrize(
    "title,ok",
    [
        ("Bike Phone Holder Anti Vibration", True),
        ("Mobile Holder for Motorcycle with Charger", True),
        ("Best 10 Mobile Holders for Bikes in 2025", False),
        ("Mobile Holder Review: is it worth it?", False),
        ("Mobile Holder vs Tripod", False),
        ("Silicone cover for Mobile Holder", False),
        ("Samsung Galaxy Mobile Charger", False),
    ],
)
def test_title_relevance_for_mobile_holder(title, ok):
    assert relevance.is_relevant_title(title, relevance.core_terms("mobile holder")) is ok


def test_accessory_allowed_when_requested_or_bundled():
    assert relevance.is_relevant_title("Phone case", relevance.core_terms("phone case"))
    assert relevance.is_relevant_title(
        "Wildcraft Laptop Backpack with rain cover", relevance.core_terms("laptop backpack")
    )


def test_blocked_domains():
    assert relevance.is_blocked_domain("https://www.youtube.com/watch?v=1")
    assert relevance.is_blocked_domain("https://old.reddit.com/r/x")
    assert not relevance.is_blocked_domain("https://www.amazon.in/dp/B0")
    assert not relevance.is_blocked_domain("https://box.com/x")


# --------------------------------------------------------- category matching


@pytest.mark.parametrize(
    "query,expected",
    [
        ("riding jacket under 12K black", "riding jacket"),
        ("motorcycle jacket", "riding jacket"),
        ("adventure helmet", "adventure helmet"),
        ("helmet", "helmet"),
        ("full face helmets", "helmet"),
        ("running shoes under 5000 INR", "running shoes"),
        ("laptop backpack", "laptop backpack"),
        ("jacket", None),
        ("shoes", None),
        ("laptop", None),
        ("running watch", None),
        ("mobile holder", None),
        ("bicycle helmet", None),
        ("kids helmet", None),
    ],
)
def test_registry_category_matching(query, expected):
    assert DiscoverStage().match_registry_category(relevance.core_terms(query)) == expected


# ----------------------------------------------------------------- discovery


async def test_unknown_product_without_results_returns_nothing(monkeypatch):
    """The reported bug: 'mobile holder' used to return a jacket and two helmets."""
    _stub_search(monkeypatch)
    ctx = await _ctx(
        {
            "product_type": "mobile holder",
            "budget_min": 2500,
            "budget_max": 3000,
            "must_haves": "anti-vibration",
        }
    )
    await DiscoverStage().execute(ctx)
    assert ctx.candidates == []


async def test_web_results_are_filtered_and_unpriced(monkeypatch):
    _stub_search(
        monkeypatch,
        default=[
            {
                "title": "Ulanzi Bike Phone Holder Anti Vibration",
                "url": "https://shop.in/products/a",
            },
            {"title": "Best 10 Mobile Holders for Bikes", "url": "https://blog.in/x"},
            {"title": "Bike mobile holder install", "url": "https://www.youtube.com/watch?v=1"},
            {"title": "Mobile Holder Cover Replacement", "url": "https://shop.in/products/c"},
            {"title": "Axor Apex Full Face Helmet", "url": "https://shop.in/products/h"},
        ],
    )
    ctx = await _ctx({"product_type": "mobile holder"})
    await DiscoverStage().execute(ctx)
    assert [c.title for c in ctx.candidates] == ["Ulanzi Bike Phone Holder Anti Vibration"]
    cand = ctx.candidates[0]
    assert cand.source == "web"
    assert cand.canonical_brand == "Ulanzi"
    assert cand.estimated_price is None


async def test_generic_title_does_not_use_query_word_as_brand(monkeypatch):
    _stub_search(
        monkeypatch,
        default=[
            {"title": "Mobile Holder for Bike Handlebar", "url": "https://shop.in/products/a"}
        ],
    )
    ctx = await _ctx({"product_type": "mobile holder"})
    await DiscoverStage().execute(ctx)
    assert ctx.candidates[0].canonical_brand == "Generic"


async def test_registry_category_respects_budget(monkeypatch):
    _stub_search(monkeypatch)
    ctx = await _ctx({"product_type": "riding jacket", "budget_max": 3000})
    await DiscoverStage().execute(ctx)
    assert ctx.candidates == []

    ctx = await _ctx({"product_type": "riding jacket", "budget_max": 12000})
    await DiscoverStage().execute(ctx)
    assert ctx.candidates
    assert all(c.estimated_price <= 12000 * 1.10 for c in ctx.candidates)
    assert all(c.source == "registry" for c in ctx.candidates)


async def test_helmet_query_never_returns_other_categories(monkeypatch):
    _stub_search(monkeypatch)
    ctx = await _ctx({"product_type": "adventure helmet"})
    await DiscoverStage().execute(ctx)
    assert ctx.candidates
    assert all("helmet" in c.title.lower() for c in ctx.candidates)


async def test_user_brand_missing_from_registry_is_not_synthesized(monkeypatch):
    calls = _stub_search(monkeypatch)
    ctx = await _ctx({"product_type": "running shoes", "brands_included": ["Hoka"]})
    await DiscoverStage().execute(ctx)
    assert all("hoka" not in c.canonical_brand.lower() for c in ctx.candidates)
    assert any("Hoka" in q for q in calls)


async def test_user_brand_found_via_targeted_search(monkeypatch):
    _stub_search(
        monkeypatch,
        results_by_query={
            "Hoka": [
                {"title": "HOKA Clifton 9 Running Shoes", "url": "https://hoka.in/products/c9"}
            ]
        },
    )
    ctx = await _ctx({"product_type": "running shoes", "brands_included": ["Hoka"]})
    await DiscoverStage().execute(ctx)
    brands = [c.canonical_brand for c in ctx.candidates]
    assert "Hoka" in brands
    hoka = next(c for c in ctx.candidates if c.canonical_brand == "Hoka")
    assert hoka.source == "web" and hoka.estimated_price is None


async def test_excluded_brand_is_removed(monkeypatch):
    _stub_search(monkeypatch)
    ctx = await _ctx({"product_type": "helmet", "brands_excluded": ["Axor"]})
    await DiscoverStage().execute(ctx)
    assert ctx.candidates
    assert all("axor" not in c.canonical_brand.lower() for c in ctx.candidates)


# ---------------------------------------------------------------- heuristics


async def test_heuristic_uses_word_boundaries():
    for query in ["overwhelming pants", "baggy trousers", "audio interface"]:
        spec = await HeuristicProvider().parse_query_spec({"product_type": query})
        assert spec.brands_included == [], query
        assert spec.mandatory_specs == [], query


# ------------------------------------------------------------------- stage 6


async def test_stage6_drops_irrelevant_web_candidate_but_keeps_registry():
    ctx = await _ctx({"product_type": "mobile holder"})
    offer = {"url": "https://s.in/a", "price": 500.0, "status": "verified"}
    ctx.candidates = [
        DiscoveredCandidate(
            "Ulanzi",
            "Bike Holder",
            "Ulanzi Bike Mobile Holder",
            source="web",
            scraped_offers=[dict(offer)],
        ),
        DiscoveredCandidate(
            "Axor", "Apex", "Axor Apex Helmet", source="web", scraped_offers=[dict(offer)]
        ),
        DiscoveredCandidate(
            "Rynox",
            "Stealth",
            "Rynox Stealth Jacket",
            source="registry",
            scraped_offers=[dict(offer)],
        ),
    ]
    await VerificationStage().execute(ctx)
    dropped = {c.canonical_brand: c.is_dropped for c in ctx.candidates}
    assert dropped == {"Ulanzi": False, "Axor": True, "Rynox": False}


async def test_stage6_drops_web_candidate_over_budget_and_without_page():
    ctx = await _ctx({"product_type": "mobile holder", "budget_max": 3000})
    ctx.candidates = [
        DiscoveredCandidate(
            "A",
            "Holder One",
            "A Mobile Holder",
            source="web",
            scraped_offers=[{"url": "https://s.in/1", "price": 9000.0, "status": "verified"}],
        ),
        DiscoveredCandidate("B", "Holder Two", "B Mobile Holder", source="web"),
    ]
    await VerificationStage().execute(ctx)
    assert all(c.is_dropped for c in ctx.candidates)


async def test_stage6_keeps_unavailable_status_and_handles_certs_without_specs():
    ctx = await _ctx({"product_type": "mobile holder"})
    ctx.spec.mandatory_specs = []
    ctx.spec.standards_and_certifications = ["ISI"]
    ctx.candidates = [
        DiscoveredCandidate(
            "Ulanzi",
            "Holder",
            "Ulanzi Mobile Holder",
            source="web",
            seed_urls=["https://s.in/a"],
            scraped_offers=[{"url": "https://s.in/a", "price": 500.0, "status": "unavailable"}],
        )
    ]
    await VerificationStage().execute(ctx)
    cand = ctx.candidates[0]
    assert cand.scraped_offers[0]["status"] == "unavailable"
    assert cand.claims_evidence[0]["source_url"] == "https://s.in/a"


# ------------------------------------------------- category pages / fetcher


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://www.amazon.in/s?k=riding+jacket", True),
        ("https://www.flipkart.com/search?q=jacket", True),
        ("https://store.in/collections/jackets", True),
        ("https://store.in/category/jackets/", True),
        ("https://store.in/collections/jackets/products/rynox-stealth", False),
        ("https://www.amazon.in/dp/B0ABC12345", False),
        ("https://rynoxgear.com/products/stealth-evo-3-jacket", False),
    ],
)
def test_category_page_detection(url, expected):
    assert relevance.is_category_page(url) is expected


def test_retailer_prefix_is_removed_from_titles():
    assert relevance.strip_retailer_prefix("Amazon.in: Riding Jacket") == "Riding Jacket"
    assert relevance.strip_retailer_prefix("Rynox Stealth Jacket") == "Rynox Stealth Jacket"


async def test_category_page_result_is_not_a_candidate(monkeypatch):
    _stub_search(
        monkeypatch,
        default=[
            {"title": "Amazon.in: Mobile Holder", "url": "https://www.amazon.in/s?k=mobile+holder"},
        ],
    )
    ctx = await _ctx({"product_type": "mobile holder"})
    await DiscoverStage().execute(ctx)
    assert ctx.candidates == []


def test_fetcher_accepts_per_request_timeout():
    import inspect

    from backend.services.fetcher import SharedFetcher

    assert "timeout" in inspect.signature(SharedFetcher.fetch).parameters


# --------------------------------------------- store pages, offers, budgets


async def test_storefront_headlines_are_not_candidates(monkeypatch):
    _stub_search(
        monkeypatch,
        default=[
            {
                "title": "Running Shoes: Buy Mens Running Shoes Online in India",
                "url": "https://a.in/x",
            },
            {
                "title": "Running Shoes at Affordable Prices in India | Flipkart",
                "url": "https://b.in/y",
            },
            {"title": "Buy Nike Pegasus 40 Running Shoes Online", "url": "https://c.in/products/z"},
        ],
    )
    ctx = await _ctx({"product_type": "running shoes"})
    await DiscoverStage().execute(ctx)
    web = [c for c in ctx.candidates if c.source == "web"]
    assert [(c.canonical_brand, c.title) for c in web] == [
        ("Nike", "Buy Nike Pegasus 40 Running Shoes Online")
    ]


async def test_stage6_sorts_offers_best_first_and_keeps_catalog_prices_unverified():
    ctx = await _ctx({"product_type": "running shoes"})
    ctx.candidates = [
        DiscoveredCandidate(
            "Puma",
            "Velocity",
            "Puma Velocity Running Shoes",
            scraped_offers=[
                {
                    "url": "https://a",
                    "price": 4999.0,
                    "status": "unverified",
                    "price_source": "catalog",
                },
                {"url": "https://b", "price": 0.0, "status": "unavailable"},
                {"url": "https://c", "price": 8999.0, "status": "verified"},
                {"url": "https://d", "price": 8499.0, "status": "verified"},
            ],
        )
    ]
    await VerificationStage().execute(ctx)
    offers = ctx.candidates[0].scraped_offers
    assert [o["url"] for o in offers] == ["https://d", "https://c", "https://a", "https://b"]
    assert offers[2]["status"] == "unverified"


async def test_stage6_budget_gate_uses_scraped_price_not_catalog_price():
    ctx = await _ctx({"product_type": "running shoes", "budget_max": 5000})
    over = DiscoveredCandidate(
        "Puma",
        "Velocity",
        "Puma Velocity Running Shoes",
        source="registry",
        scraped_offers=[{"url": "https://c", "price": 8999.0, "status": "verified"}],
    )
    catalog_only = DiscoveredCandidate(
        "Nike",
        "Pegasus",
        "Nike Pegasus Running Shoes",
        source="registry",
        scraped_offers=[
            {"url": "https://a", "price": 8495.0, "status": "unverified", "price_source": "catalog"}
        ],
    )
    ctx.candidates = [over, catalog_only]
    await VerificationStage().execute(ctx)
    assert over.is_dropped and "exceeds" in over.drop_reason
    assert not catalog_only.is_dropped


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://www.amazon.in/Nike-Pegasus/dp/B0CABCDEFG", True),
        ("https://www.flipkart.com/nike-shoes/p/itm1234abcd", True),
        ("https://store.in/products/ulanzi-holder", True),
        ("https://store.in/ulanzi-holder-p-4521", True),
        ("https://www.nykaafashion.com/dp/jackets", False),
        ("https://www.amazon.in/running-shoes/b?node=123", False),
        ("https://www.myntra.com/running-shoes", False),
        ("https://store.in/", False),
        ("", False),
    ],
)
def test_product_url_shape(url, expected):
    assert relevance.looks_like_product_url(url) is expected


async def test_web_result_without_product_url_is_rejected(monkeypatch):
    _stub_search(
        monkeypatch,
        default=[
            {"title": "Ulanzi Bike Mobile Holder", "url": "https://www.myntra.com/mobile-holder"},
            {"title": "Ulanzi Bike Mobile Holder", "url": ""},
        ],
    )
    ctx = await _ctx({"product_type": "mobile holder"})
    await DiscoverStage().execute(ctx)
    assert ctx.candidates == []
