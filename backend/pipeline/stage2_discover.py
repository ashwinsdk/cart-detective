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
        for category_key, items in CURATED_CANDIDATE_REGISTRY.items():
            if category_key in p_type or any(word in p_type for word in category_key.split()):
                matched_registry_items.extend(items)

        # Generic fallback seeds if no category directly matches
        if not matched_registry_items:
            for items in CURATED_CANDIDATE_REGISTRY.values():
                matched_registry_items.extend(items[:1])

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

        # 2. Query external search engines if configured
        search_query = " ".join(spec.search_keywords[:3])
        try:
            results = await self._query_searxng(search_query)
            for res in results[:5]:
                title = res.get("title", "")
                link = res.get("url", "")
                # Attempt to extract brand and model from title
                parts = title.split(" ")
                if len(parts) >= 2:
                    cand_brand = parts[0]
                    cand_model = " ".join(parts[1:3])
                    key = self._normalize_key(cand_brand, cand_model)
                    if key not in candidates_map:
                        candidates_map[key] = DiscoveredCandidate(
                            canonical_brand=cand_brand,
                            canonical_model=cand_model,
                            title=title,
                            seed_urls=[link] if link else [],
                            currency=spec.currency,
                        )
        except Exception as exc:
            ctx.telemetry.partial_failures.append(f"External discovery query failed: {exc}")
            ctx.log(
                2,
                f"External search provider failed ({exc}). Continuing with curated seeds.",
                level="WARNING",
            )

        ctx.candidates = list(candidates_map.values())
        duration = (time.monotonic() - start_time) * 1000.0
        ctx.telemetry.stage_durations_ms["stage2_discover"] = duration
        ctx.telemetry.stage_status["stage2_discover"] = "completed"
        ctx.log(
            2,
            f"Stage 2 completed: discovered {len(ctx.candidates)} deduplicated candidate products in {duration:.1f}ms",
        )
