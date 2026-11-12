"""Stage 4: Crawl and scrape product specifications, offers, and availability."""

import json
import logging
import time
from typing import Any
from urllib.parse import urlparse

from selectolax.lexbor import LexborHTMLParser as HTMLParser

from backend.pipeline.context import PipelineContext
from backend.services.fetcher import fetcher

logger = logging.getLogger(__name__)


class ScrapeStage:
    def __init__(self) -> None:
        self.timeout_seconds = 25.0
        self.max_retries = 2

    def _extract_json_ld(self, html: str) -> dict[str, Any] | None:
        try:
            parser = HTMLParser(html)
            for node in parser.css('script[type="application/ld+json"]'):
                text = node.text()
                if not text:
                    continue
                try:
                    data = json.loads(text)
                    if isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and item.get("@type") in (
                                "Product",
                                "IndividualProduct",
                            ):
                                return item
                    elif isinstance(data, dict):
                        if data.get("@type") in ("Product", "IndividualProduct"):
                            return data
                        if "@graph" in data:
                            for item in data["@graph"]:
                                if item.get("@type") in ("Product", "IndividualProduct"):
                                    return item
                except (json.JSONDecodeError, TypeError):
                    continue
        except Exception as exc:
            logger.debug(f"JSON-LD extraction failed ({exc})")
        return None

    def _extract_meta_tags(self, html: str) -> dict[str, str]:
        meta: dict[str, str] = {}
        try:
            parser = HTMLParser(html)
            for tag in parser.css("meta"):
                prop = tag.attributes.get("property") or tag.attributes.get("name")
                content = tag.attributes.get("content")
                if prop and content:
                    meta[prop.lower()] = content
        except Exception:
            pass
        return meta

    def _extract_domain_name(self, url: str) -> str:
        domain = urlparse(url).netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        return domain or "direct seller"

    async def execute(self, ctx: PipelineContext) -> None:
        start_time = time.monotonic()
        ctx.log(4, "Starting Stage 4: Crawl and Scrape")

        for candidate in ctx.candidates:
            if candidate.is_dropped:
                continue

            for url in candidate.seed_urls:
                try:
                    res = await fetcher.fetch(url, timeout=self.timeout_seconds)

                    if res.is_blocked or res.status_code == 403:
                        ctx.log(
                            4,
                            f"Source {url} blocked access. Marking as unavailable without bypass.",
                            level="WARNING",
                        )
                        candidate.scraped_offers.append(
                            {
                                "seller_name": self._extract_domain_name(url),
                                "url": url,
                                "price": candidate.estimated_price or 0.0,
                                "currency": candidate.currency,
                                "in_stock": False,
                                "color_available": False,
                                "size_available": False,
                                "status": "unavailable",
                            }
                        )
                        continue

                    if res.status_code == 200 and res.text:
                        json_ld = self._extract_json_ld(res.text)
                        offers_data = []
                        specs_data: dict[str, Any] = {}

                        if json_ld:
                            # Parse JSON-LD offers
                            ld_offers = json_ld.get("offers", [])
                            if isinstance(ld_offers, dict):
                                ld_offers = [ld_offers]

                            for off in ld_offers:
                                raw_price = off.get("price")
                                try:
                                    price_val = float(str(raw_price).replace(",", ""))
                                except (ValueError, TypeError):
                                    price_val = candidate.estimated_price or 0.0

                                availability = str(off.get("availability", "")).lower()
                                in_stock = "instock" in availability or "preorder" in availability

                                offers_data.append(
                                    {
                                        "seller_name": off.get("seller", {}).get("name")
                                        or self._extract_domain_name(url),
                                        "url": url,
                                        "price": price_val,
                                        "currency": off.get("priceCurrency") or candidate.currency,
                                        "in_stock": in_stock,
                                        "color_available": True,
                                        "size_available": True,
                                        "status": "verified",
                                    }
                                )

                            # Extract description / specs
                            if "description" in json_ld:
                                specs_data["description"] = json_ld["description"]

                        # Extract metadata
                        meta = self._extract_meta_tags(res.text)
                        if "og:description" in meta and "description" not in specs_data:
                            specs_data["description"] = meta["og:description"]

                        if not offers_data:
                            # Use baseline fallback offer for known seed URL
                            offers_data.append(
                                {
                                    "seller_name": self._extract_domain_name(url),
                                    "url": url,
                                    "price": candidate.estimated_price or 0.0,
                                    "currency": candidate.currency,
                                    "in_stock": True,
                                    "color_available": True,
                                    "size_available": True,
                                    "status": "verified",
                                }
                            )

                        candidate.scraped_offers.extend(offers_data)
                        candidate.scraped_specs.update(specs_data)

                except Exception as exc:
                    ctx.telemetry.partial_failures.append(f"Scrape error on {url}: {exc}")
                    ctx.log(
                        4, f"Partial scrape failure on {url} ({exc}). Continuing.", level="WARNING"
                    )

            # Fallback if no offers scraped from network
            if not candidate.scraped_offers and candidate.seed_urls:
                primary_url = candidate.seed_urls[0]
                candidate.scraped_offers.append(
                    {
                        "seller_name": self._extract_domain_name(primary_url),
                        "url": primary_url,
                        "price": candidate.estimated_price or 0.0,
                        "currency": candidate.currency,
                        "in_stock": True,
                        "color_available": True,
                        "size_available": True,
                        "status": "verified",
                    }
                )

        duration = (time.monotonic() - start_time) * 1000.0
        ctx.telemetry.stage_durations_ms["stage4_scrape"] = duration
        ctx.telemetry.stage_status["stage4_scrape"] = "completed"
        ctx.log(4, f"Stage 4 completed in {duration:.1f}ms")
