"""Stage 2: Discover product candidates using search providers with deduplication."""

import asyncio
import json
import logging
import re
import time
from urllib.parse import quote_plus

from backend.config import settings
from backend.pipeline import relevance
from backend.pipeline.context import DiscoveredCandidate, PipelineContext
from backend.services.fetcher import fetcher

logger = logging.getLogger(__name__)

CURATED_CANDIDATE_REGISTRY = {
    "riding jacket": [
        {
            "brand": "Rynox",
            "model": "Stealth Evo 3",
            "title": "Rynox Stealth Evo 3 Riding Jacket",
            "price": 10750.0,
            "urls": [
                "https://rynoxgear.com/products/stealth-evo-3-jacket",
                "https://amazon.in/dp/B08XYZ1234",
            ],
        },
        {
            "brand": "Royal Enfield",
            "model": "Streetwind V3",
            "title": "Royal Enfield Streetwind V3 Riding Jacket",
            "price": 4950.0,
            "urls": [
                "https://store.royalenfield.com/streetwind-v3",
                "https://flipkart.com/re-streetwind-v3",
            ],
        },
        {
            "brand": "Viaterra",
            "model": "Spencer",
            "title": "Viaterra Spencer All-Weather Mesh Jacket",
            "price": 8999.0,
            "urls": ["https://viaterragear.com/spencer-jacket", "https://amazon.in/dp/B07ABC9876"],
        },
        {
            "brand": "Alpinestars",
            "model": "T-SPS Air",
            "title": "Alpinestars T-SPS Air Waterproof Jacket",
            "price": 14999.0,
            "urls": ["https://alpinestars.com/t-sps-air", "https://amazon.in/dp/B09MNP4567"],
        },
    ],
    "adventure helmet": [
        {
            "brand": "Axor",
            "model": "X-Cross Dual Sport",
            "title": "Axor X-Cross Dual Sport Adventure Helmet",
            "price": 5199.0,
            "urls": [
                "https://axorhelmets.com/collections/axor-x-cross",
                "https://www.flipkart.com/axor-x-cross-motorbike-helmet/p/itm785cbf0482862",
            ],
        },
        {
            "brand": "LS2",
            "model": "Pioneer II Dual Sport",
            "title": "LS2 Pioneer II Dual Sport Adventure Helmet",
            "price": 10500.0,
            "urls": [
                "https://ls2helmetsindia.com/products/mx436-pioneer-ii-solid-matt-black-06",
                "https://motocentral.in/collections/ls2-helmets-india",
            ],
        },
        {
            "brand": "SMK",
            "model": "Allterra Dual Sport",
            "title": "SMK Allterra Solid Dual Sport Helmet",
            "price": 5250.0,
            "urls": [
                "https://www.store4riders.com/motorcycle-helmets/off-road-helmets/smk-allterra-helmets.html",
                "https://ridersjunction.com/collections/smk-allterra?page=1",
            ],
        },
        {
            "brand": "MT Helmets",
            "model": "Synchrony SV Dual Sport",
            "title": "MT Synchrony SV Dual Sport Adventure Helmet",
            "price": 7250.0,
            "urls": [
                "https://motocentral.in/collections/mt-helmets",
                "https://www.tradeinn.com/motardinn/en/mt-helmets-synchrony-sv-duo-sport-full-face-helmet/1234139/p",
            ],
        },
    ],
    "helmet": [
        {
            "brand": "Axor",
            "model": "Apex Solid",
            "title": "Axor Apex Solid Full Face Helmet",
            "price": 4650.0,
            "urls": [
                "https://www.flipkart.com/axor-apex-solid-motorbike-helmet/p/itm55b1eb1245fa7",
                "https://axorhelmets.com/collections/helmets",
            ],
        },
        {
            "brand": "SMK",
            "model": "Stellar Sport",
            "title": "SMK Stellar Full Face Helmet",
            "price": 3950.0,
            "urls": [
                "https://www.flipkart.com/smk-stellar-solid-full-face-helmet/p/itmfbzh2wgy8ff7x",
                "https://smkhelmets.com",
            ],
        },
        {
            "brand": "MT Helmets",
            "model": "Thunder 4 SV",
            "title": "MT Thunder 4 SV ECE 22.06 Helmet",
            "price": 12950.0,
            "urls": [
                "https://motocentral.in/collections/mt-helmets",
                "https://mthelmets.com",
            ],
        },
    ],
    "running shoes": [
        {
            "brand": "Asics",
            "model": "Gel Kayano 30",
            "title": "Asics Gel-Kayano 30 Running Shoes",
            "price": 11999.0,
            "urls": [
                "https://asics.co.in/collections/running",
                "https://www.amazon.in/s?k=asics+gel+kayano+30",
            ],
        },
        {
            "brand": "Nike",
            "model": "Pegasus 40",
            "title": "Nike Air Zoom Pegasus 40",
            "price": 8495.0,
            "urls": [
                "https://www.flipkart.com/search?q=nike+pegasus+40",
                "https://www.amazon.in/s?k=nike+air+zoom+pegasus+40",
            ],
        },
        {
            "brand": "Puma",
            "model": "Velocity Nitro 2",
            "title": "Puma Velocity Nitro 2 Running Shoes",
            "price": 4999.0,
            "urls": [
                "https://in.puma.com/in/en/pd/velocity-nitro-2-mens-running-shoes/195337",
                "https://www.amazon.in/s?k=puma+velocity+nitro+2",
            ],
        },
    ],
    "laptop backpack": [
        {
            "brand": "Mokobara",
            "model": "The Transit Backpack",
            "title": "Mokobara The Transit Backpack 15.6 inch",
            "price": 4499.0,
            "urls": [
                "https://mokobara.com/products/the-transit-backpack",
                "https://www.amazon.in/s?k=mokobara+transit+backpack",
            ],
        },
        {
            "brand": "American Tourister",
            "model": "Valex",
            "title": "American Tourister Valex 28L Laptop Backpack",
            "price": 1899.0,
            "urls": [
                "https://americantourister.in",
                "https://www.amazon.in/s?k=american+tourister+valex",
            ],
        },
        {
            "brand": "Lenovo",
            "model": "Legion Recon",
            "title": "Lenovo Legion 15.6 inch Recon Gaming Backpack",
            "price": 2899.0,
            "urls": [
                "https://www.lenovo.com/in/en/p/accessories-and-software/cases-and-bags/backpacks/gx40s89445",
                "https://www.flipkart.com/search?q=lenovo+legion+recon",
            ],
        },
    ],
}


# Alternative phrasings that map to a registry category. Keys must exist in
# CURATED_CANDIDATE_REGISTRY. Matching is done on stemmed terms.
CATEGORY_ALIASES = {
    "riding jacket": ["motorcycle jacket", "motorbike jacket", "bike jacket"],
}

MARKET_SUFFIX = {
    "INR": "buy online india",
    "USD": "buy online",
    "EUR": "buy online",
    "GBP": "buy online uk",
}

MAX_SEARCH_RESULTS = 10
MAX_WEB_CANDIDATES = 8
BUDGET_UPPER_TOLERANCE = 1.10
BUDGET_LOWER_TOLERANCE = 0.80

GENERIC_FIRST_WORDS = frozenset(
    {"universal", "premium", "original", "genuine", "set", "pack", "pair", "buy", "shop"}
)


class DiscoverStage:
    def __init__(self) -> None:
        self.timeout_seconds = 20.0
        self.max_retries = 2

    def _normalize_key(self, brand: str, model: str) -> str:
        b = re.sub(r"[^a-zA-Z0-9]", "", brand.lower())
        m = re.sub(r"[^a-zA-Z0-9]", "", model.lower())
        return f"{b}:{m}"

    async def _query_searxng(self, query: str) -> list[dict]:
        if not settings.SEARXNG_URL:
            return []
        url = f"{settings.SEARXNG_URL}/search?q={quote_plus(query)}&format=json"
        try:
            res = await fetcher.fetch(url, timeout=5.0, respect_robots=False)
            if res.status_code == 200:
                data = json.loads(res.text)
                return [
                    {"title": r.get("title", ""), "url": r.get("url", "")}
                    for r in data.get("results", [])
                    if r.get("title")
                ]
        except Exception as exc:
            logger.warning(f"SearXNG query failed ({exc})")
        return []

    def _query_duckduckgo(self, query: str) -> list[dict]:
        try:
            try:
                from ddgs import DDGS
            except ImportError:
                from duckduckgo_search import DDGS

            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=MAX_SEARCH_RESULTS))
                return [
                    {"title": r.get("title", ""), "url": r.get("href", "")}
                    for r in results
                    if r.get("title")
                ]
        except Exception as exc:
            logger.warning(f"DuckDuckGo search failed ({exc})")
            return []

    async def _search(self, query: str, currency: str) -> list[dict]:
        """Run one search with SearXNG first, then DuckDuckGo, with backoff."""
        results = await self._query_searxng(query)
        if results:
            return results
        suffix = MARKET_SUFFIX.get(currency, "buy online")
        for attempt in range(self.max_retries):
            results = await asyncio.to_thread(self._query_duckduckgo, f"{query} {suffix}")
            if results:
                return results
            await asyncio.sleep(0.5 * (2**attempt))
        return []

    def match_registry_category(self, terms: list[str]) -> str | None:
        """Return the registry key the query describes, or None.

        Every word of the key (or one of its aliases) must appear in the query.
        A single shared word is not enough, so "jacket" does not become
        "riding jacket" and "laptop" does not become "laptop backpack".
        """
        if not terms or relevance.has_incompatible_qualifier(terms):
            return None
        term_set = set(terms)
        best: tuple[int, str] | None = None
        for key in CURATED_CANDIDATE_REGISTRY:
            for phrase in [key, *CATEGORY_ALIASES.get(key, [])]:
                words = set(relevance.core_terms(phrase))
                if words and words.issubset(term_set):
                    if best is None or len(words) > best[0]:
                        best = (len(words), key)
        return best[1] if best else None

    def _brand_from_title(self, title: str, terms: list[str]) -> tuple[str, str]:
        """Best-effort (brand, model) from a product title. Brand may be 'Generic'."""
        tokens = [t for t in re.split(r"\s+", title.strip()) if t]
        while tokens and tokens[0].lower() in relevance.LEADING_FLUFF:
            tokens = tokens[1:]
        first = re.sub(r"[^A-Za-z0-9\-]", "", tokens[0]) if tokens else ""
        looks_like_brand = (
            len(first) >= 2
            and first[0].isalpha()
            and first[0].isupper()
            and relevance.stem(first) not in terms
            and first.lower() not in relevance.STOPWORDS
            and first.lower() not in GENERIC_FIRST_WORDS
        )
        if looks_like_brand:
            return first, " ".join(tokens[1:4]) or first
        return "Generic", " ".join(tokens[:4])

    def _within_budget(self, price: float, spec) -> bool:
        if spec.budget_max and price > spec.budget_max * BUDGET_UPPER_TOLERANCE:
            return False
        return not (spec.budget_min and price < spec.budget_min * BUDGET_LOWER_TOLERANCE)

    def _add_web_results(
        self,
        results: list[dict],
        spec,
        terms: list[str],
        candidates_map: dict[str, DiscoveredCandidate],
        user_brands: list[str],
        required_brand: str | None = None,
    ) -> None:
        for res in results[:MAX_SEARCH_RESULTS]:
            if sum(1 for c in candidates_map.values() if c.source == "web") >= MAX_WEB_CANDIDATES:
                return
            title = (res.get("title") or "").strip()
            link = res.get("url") or ""
            if not title or relevance.is_blocked_domain(link) or relevance.is_category_page(link):
                continue
            if not relevance.looks_like_product_url(link):
                continue
            title = relevance.strip_retailer_prefix(title)
            if not relevance.is_relevant_title(title, terms):
                continue

            if required_brand and required_brand.lower() not in title.lower():
                continue

            brand, model = self._brand_from_title(title, terms)
            if brand == "Generic" and relevance.looks_like_store_page_title(title):
                # Storefront or category headline with no identifiable product.
                continue
            if required_brand:
                brand = required_brand.strip().title()
                model = re.sub(re.escape(required_brand), "", title, flags=re.I).strip()
                model = " ".join(model.split()[:3]) or title
            if any(ex.lower() in brand.lower() for ex in spec.brands_excluded):
                continue
            if user_brands and not any(inc.lower() in title.lower() for inc in user_brands):
                continue

            key = self._normalize_key(brand, model)
            if key in candidates_map:
                if link and link not in candidates_map[key].seed_urls:
                    candidates_map[key].seed_urls.append(link)
                continue
            candidates_map[key] = DiscoveredCandidate(
                canonical_brand=brand,
                canonical_model=model,
                title=title,
                seed_urls=[link] if link else [],
                # Price is unknown until Stage 4 reads it from the page.
                estimated_price=None,
                currency=spec.currency,
                source="web",
            )

    async def execute(self, ctx: PipelineContext) -> None:
        start_time = time.monotonic()
        ctx.log(2, "Starting Stage 2: Candidate Discovery")

        if not ctx.spec:
            ctx.log(2, "Missing structured spec, aborting discovery.", level="ERROR")
            ctx.telemetry.stage_status["stage2_discover"] = "failed"
            return

        spec = ctx.spec
        terms = relevance.core_terms(spec.product_type, spec.color_preferences)
        query_words = relevance.core_words(spec.product_type, spec.color_preferences)
        candidates_map: dict[str, DiscoveredCandidate] = {}

        raw_brands = ctx.raw_query.get("brands_included") or []
        if isinstance(raw_brands, str):
            raw_brands = [b.strip() for b in raw_brands.split(",") if b.strip()]
        user_brands = [b.strip() for b in raw_brands if b and b.strip()]

        # 1. Curated registry: only when the query actually names a known category.
        category = self.match_registry_category(terms)
        if category:
            ctx.log(2, f"Matched curated category '{category}'")
        for item in CURATED_CANDIDATE_REGISTRY.get(category or "", []):
            brand = item["brand"]
            if any(ex.lower() in brand.lower() for ex in spec.brands_excluded):
                continue
            if spec.brands_included and not any(
                inc.lower() in brand.lower() for inc in spec.brands_included
            ):
                continue
            if not self._within_budget(item["price"], spec):
                continue
            key = self._normalize_key(brand, item["model"])
            candidates_map.setdefault(
                key,
                DiscoveredCandidate(
                    canonical_brand=brand,
                    canonical_model=item["model"],
                    title=item["title"],
                    seed_urls=list(item["urls"]),
                    estimated_price=item["price"],
                    currency=spec.currency,
                    source="registry",
                ),
            )

        # 2. Live search, filtered for relevance. Never invents products or prices.
        search_query = " ".join(query_words) or spec.product_type
        results = await self._search(search_query, spec.currency)
        if not results and not candidates_map:
            ctx.telemetry.partial_failures.append("Search providers returned no results")
        self._add_web_results(results, spec, terms, candidates_map, user_brands)

        # 3. Each brand the user asked for gets its own targeted search.
        for brand in user_brands:
            if any(brand.lower() in c.canonical_brand.lower() for c in candidates_map.values()):
                continue
            if any(ex.lower() in brand.lower() for ex in spec.brands_excluded):
                continue
            brand_results = await self._search(f"{brand} {search_query}", spec.currency)
            self._add_web_results(
                brand_results, spec, terms, candidates_map, user_brands, required_brand=brand
            )

        ctx.candidates = list(candidates_map.values())
        duration = (time.monotonic() - start_time) * 1000.0
        ctx.telemetry.stage_durations_ms["stage2_discover"] = duration
        ctx.telemetry.stage_status["stage2_discover"] = "completed"
        if not ctx.candidates:
            ctx.log(
                2,
                f"No relevant products found for '{spec.product_type}'. "
                "Returning an empty result instead of unrelated products.",
                level="WARNING",
            )
        ctx.log(
            2,
            f"Stage 2 completed: discovered {len(ctx.candidates)} deduplicated candidate products in {duration:.1f}ms",
        )
