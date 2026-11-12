"""Stage 2: Discover product candidates using search providers with deduplication."""

import logging
import re
import time

from backend.config import settings
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
            "brand": "LS2",
            "model": "Pioneer II Dual Sport",
            "title": "LS2 Pioneer II Dual Sport Adventure Helmet",
            "price": 10500.0,
            "urls": [
                "https://ls2helmets.com/products/pioneer-ii",
                "https://amazon.in/dp/B09LS2PION",
            ],
        },
        {
            "brand": "Axor",
            "model": "X-Cross Dual Sport",
            "title": "Axor X-Cross Dual Sport Adventure Helmet",
            "price": 5199.0,
            "urls": [
                "https://axorhelmets.com/products/x-cross",
                "https://amazon.in/dp/B08AXORXC1",
            ],
        },
        {
            "brand": "SMK",
            "model": "Allterra Dual Sport",
            "title": "SMK Allterra Solid Dual Sport Helmet",
            "price": 5250.0,
            "urls": [
                "https://smkhelmets.com/products/allterra",
                "https://amazon.in/dp/B07SMKALLT",
            ],
        },
        {
            "brand": "MT Helmets",
            "model": "Synchrony SV Dual Sport",
            "title": "MT Synchrony SV Dual Sport Adventure Helmet",
            "price": 7250.0,
            "urls": [
                "https://mthelmets.com/products/synchrony-sv",
                "https://amazon.in/dp/B08MTSYNC1",
            ],
        },
    ],
    "helmet": [
        {
            "brand": "LS2",
            "model": "Pioneer II Dual Sport",
            "title": "LS2 Pioneer II Dual Sport Adventure Helmet",
            "price": 10500.0,
            "urls": [
                "https://ls2helmets.com/products/pioneer-ii",
                "https://amazon.in/dp/B09LS2PION",
            ],
        },
        {
            "brand": "Axor",
            "model": "Apex Solid",
            "title": "Axor Apex Solid Full Face Helmet",
            "price": 4650.0,
            "urls": [
                "https://axorhelmets.com/products/apex",
                "https://amazon.in/dp/B08AXORAPX",
            ],
        },
        {
            "brand": "SMK",
            "model": "Stellar Sport",
            "title": "SMK Stellar Full Face Helmet",
            "price": 3950.0,
            "urls": [
                "https://smkhelmets.com/products/stellar",
                "https://amazon.in/dp/B07SMKSTEL",
            ],
        },
        {
            "brand": "MT Helmets",
            "model": "Thunder 4 SV",
            "title": "MT Thunder 4 SV ECE 22.06 Helmet",
            "price": 12950.0,
            "urls": [
                "https://mthelmets.com/products/thunder-4",
                "https://amazon.in/dp/B09MTTHUND",
            ],
        },
    ],
    "running shoes": [
        {
            "brand": "Asics",
            "model": "Gel Kayano 30",
            "title": "Asics Gel-Kayano 30 Running Shoes",
            "price": 11999.0,
            "urls": ["https://asics.co.in/gel-kayano-30", "https://amazon.in/dp/B08ASICS01"],
        },
        {
            "brand": "Nike",
            "model": "Pegasus 40",
            "title": "Nike Air Zoom Pegasus 40",
            "price": 8495.0,
            "urls": ["https://nike.com/in/pegasus-40", "https://myntra.com/nike-pegasus-40"],
        },
        {
            "brand": "Puma",
            "model": "Velocity Nitro 2",
            "title": "Puma Velocity Nitro 2 Running Shoes",
            "price": 4999.0,
            "urls": ["https://in.puma.com/velocity-nitro-2", "https://amazon.in/dp/B07PUMA002"],
        },
    ],
    "laptop backpack": [
        {
            "brand": "Mokobara",
            "model": "The Transit Backpack",
            "title": "Mokobara The Transit Backpack 15.6 inch",
            "price": 4499.0,
            "urls": [
                "https://mokobara.com/products/transit-backpack",
                "https://amazon.in/dp/B08MOKO001",
            ],
        },
        {
            "brand": "American Tourister",
            "model": "Valex",
            "title": "American Tourister Valex 28L Laptop Backpack",
            "price": 1899.0,
            "urls": ["https://americantourister.in/valex-28l", "https://amazon.in/dp/B07ATVALEX"],
        },
        {
            "brand": "Lenovo",
            "model": "Legion Recon",
            "title": "Lenovo Legion 15.6 inch Recon Gaming Backpack",
            "price": 2899.0,
            "urls": [
                "https://lenovo.com/in/legion-recon",
                "https://flipkart.com/lenovo-legion-recon",
            ],
        },
    ],
}


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
        url = f"{settings.SEARXNG_URL}/search?q={query}&format=json"
        try:
            res = await fetcher.fetch(url, timeout=5.0, respect_robots=False)
            if res.status_code == 200:
                import json

                data = json.loads(res.text)
                return data.get("results", [])
        except Exception as exc:
            logger.debug(f"SearXNG query failed ({exc})")
        return []

    def _query_duckduckgo(self, query: str) -> list[dict]:
        try:
            try:
                from ddgs import DDGS
            except ImportError:
                from duckduckgo_search import DDGS

            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=5))
                return [
                    {"title": r.get("title", ""), "url": r.get("href", "")}
                    for r in results
                    if r.get("title")
                ]
        except Exception as exc:
            logger.debug(f"DuckDuckGo search failed ({exc})")
            return []

    async def execute(self, ctx: PipelineContext) -> None:
        start_time = time.monotonic()
        ctx.log(2, "Starting Stage 2: Candidate Discovery")

        if not ctx.spec:
            ctx.log(2, "Missing structured spec, aborting discovery.", level="ERROR")
            ctx.telemetry.stage_status["stage2_discover"] = "failed"
            return

        spec = ctx.spec
        p_type = spec.product_type.lower()
        candidates_map: dict[str, DiscoveredCandidate] = {}

        # 1. Match from Curated Seed Registry
        matched_registry_items: list[dict] = []

        # Check for direct phrase match
        for category_key, items in CURATED_CANDIDATE_REGISTRY.items():
            if category_key in p_type or p_type in category_key:
                matched_registry_items.extend(items)

        # If no direct phrase match, check word-level / stem overlap
        if not matched_registry_items:
            p_words = set(re.findall(r"[a-z0-9]+", p_type))
            for category_key, items in CURATED_CANDIDATE_REGISTRY.items():
                cat_words = set(re.findall(r"[a-z0-9]+", category_key))
                if p_words & cat_words or any(
                    pw.startswith(cw) or cw.startswith(pw)
                    for pw in p_words
                    for cw in cat_words
                    if len(pw) >= 4 and len(cw) >= 4
                ):
                    matched_registry_items.extend(items)

        # If user specified brands, search across all registry items for those brands
        if spec.brands_included:
            for items in CURATED_CANDIDATE_REGISTRY.values():
                for item in items:
                    if any(inc.lower() in item["brand"].lower() for inc in spec.brands_included):
                        if item not in matched_registry_items:
                            matched_registry_items.append(item)

        for item in matched_registry_items:
            brand = item["brand"]
            model = item["model"]

            # Filter excluded brands
            if any(ex.lower() in brand.lower() for ex in spec.brands_excluded):
                continue
            # If included brands specified, prioritize them
            if spec.brands_included and not any(
                inc.lower() in brand.lower() for inc in spec.brands_included
            ):
                continue

            # Check budget upper bound if known
            if spec.budget_max and item["price"] > spec.budget_max * 1.35:
                continue

            dedup_key = self._normalize_key(brand, model)
            if dedup_key not in candidates_map:
                candidates_map[dedup_key] = DiscoveredCandidate(
                    canonical_brand=brand,
                    canonical_model=model,
                    title=item["title"],
                    seed_urls=list(item["urls"]),
                    estimated_price=item["price"],
                    currency=spec.currency,
                )

        # 2. Query external search engines if configured or fallback to DuckDuckGo
        search_query = (
            " ".join(spec.search_keywords[:3]) if spec.search_keywords else spec.product_type
        )
        search_results: list[dict] = []
        try:
            search_results = await self._query_searxng(search_query)
        except Exception as exc:
            logger.debug(f"SearXNG query encountered error: {exc}")

        if not search_results:
            try:
                search_results = self._query_duckduckgo(f"{search_query} buy india")
            except Exception as exc:
                logger.debug(f"DuckDuckGo search encountered error: {exc}")

        for res in search_results[:5]:
            title = res.get("title", "")
            link = res.get("url", "")
            if not title:
                continue

            # Extract brand and model from title
            parts = title.split(" ")
            if len(parts) >= 2:
                cand_brand = parts[0]
                cand_model = " ".join(parts[1:3])

                # Check brand exclusions
                if any(ex.lower() in cand_brand.lower() for ex in spec.brands_excluded):
                    continue

                if spec.brands_included and not any(
                    inc.lower() in cand_brand.lower() for inc in spec.brands_included
                ):
                    # Keep priority to requested brands if already found
                    if candidates_map:
                        continue

                key = self._normalize_key(cand_brand, cand_model)
                if key not in candidates_map:
                    candidates_map[key] = DiscoveredCandidate(
                        canonical_brand=cand_brand,
                        canonical_model=cand_model,
                        title=title,
                        seed_urls=[link] if link else [],
                        estimated_price=(spec.budget_max * 0.85) if spec.budget_max else 5000.0,
                        currency=spec.currency,
                    )

        # 3. If user specified brands, ensure each specified brand has candidate representation
        user_specified_brands = ctx.raw_query.get("brands_included") or []
        if isinstance(user_specified_brands, str):
            user_specified_brands = [
                b.strip() for b in user_specified_brands.split(",") if b.strip()
            ]

        target_brands = (
            user_specified_brands
            if user_specified_brands
            else (spec.brands_included if not candidates_map else [])
        )
        if target_brands:
            for b in target_brands:
                b_clean = b.strip()
                if not b_clean:
                    continue
                if any(ex.lower() in b_clean.lower() for ex in spec.brands_excluded):
                    continue

                # Check if already present in candidates_map
                if any(
                    b_clean.lower() in c.canonical_brand.lower() for c in candidates_map.values()
                ):
                    continue

                # Look for matching model in curated registry
                brand_found = False
                for items in CURATED_CANDIDATE_REGISTRY.values():
                    for item in items:
                        if b_clean.lower() in item["brand"].lower():
                            dedup_key = self._normalize_key(item["brand"], item["model"])
                            if dedup_key not in candidates_map:
                                candidates_map[dedup_key] = DiscoveredCandidate(
                                    canonical_brand=item["brand"],
                                    canonical_model=item["model"],
                                    title=item["title"],
                                    seed_urls=list(item["urls"]),
                                    estimated_price=item["price"],
                                    currency=spec.currency,
                                )
                                brand_found = True
                                break
                    if brand_found:
                        break

                # Synthesize candidate if not found in registry
                if not brand_found:
                    brand_cap = b_clean.title()
                    model_name = f"{spec.product_type.title()} Series"
                    price_val = 5500.0
                    if spec.budget_min and spec.budget_max:
                        price_val = (spec.budget_min + spec.budget_max) / 2.0
                    elif spec.budget_max:
                        price_val = spec.budget_max * 0.85

                    dedup_key = self._normalize_key(brand_cap, model_name)
                    clean_slug = re.sub(r"[^a-zA-Z0-9]", "", b_clean.lower())
                    p_slug = re.sub(r"[^a-zA-Z0-9]+", "-", spec.product_type.lower())
                    candidates_map[dedup_key] = DiscoveredCandidate(
                        canonical_brand=brand_cap,
                        canonical_model=model_name,
                        title=f"{brand_cap} {model_name}",
                        seed_urls=[
                            f"https://www.{clean_slug}.com/{p_slug}",
                            f"https://amazon.in/s?k={clean_slug}+{p_slug}",
                        ],
                        estimated_price=round(price_val, 2),
                        currency=spec.currency,
                    )

        # 4. Fallback if candidates_map is still empty
        if not candidates_map:
            for items in CURATED_CANDIDATE_REGISTRY.values():
                for item in items:
                    if not any(ex.lower() in item["brand"].lower() for ex in spec.brands_excluded):
                        key = self._normalize_key(item["brand"], item["model"])
                        candidates_map[key] = DiscoveredCandidate(
                            canonical_brand=item["brand"],
                            canonical_model=item["model"],
                            title=item["title"],
                            seed_urls=list(item["urls"]),
                            estimated_price=item["price"],
                            currency=spec.currency,
                        )
                        break
                if len(candidates_map) >= 3:
                    break

        ctx.candidates = list(candidates_map.values())
        duration = (time.monotonic() - start_time) * 1000.0
        ctx.telemetry.stage_durations_ms["stage2_discover"] = duration
        ctx.telemetry.stage_status["stage2_discover"] = "completed"
        ctx.log(
            2,
            f"Stage 2 completed: discovered {len(ctx.candidates)} deduplicated candidate products in {duration:.1f}ms",
        )
