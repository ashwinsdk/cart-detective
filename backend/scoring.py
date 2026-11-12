"""Transparent multi-dimensional scoring engine and confidence calculator."""

import logging
from typing import Any

from backend.pipeline.context import DiscoveredCandidate
from backend.services.llm import StructuredQuerySpec

logger = logging.getLogger(__name__)

DEFAULT_WEIGHTS = {
    "budget_fit": 0.20,
    "spec_match": 0.20,
    "review_sentiment": 0.20,
    "brand_reliability": 0.15,
    "youtube_consensus": 0.15,
    "stock_seller_trust": 0.10,
}


class ScoringEngine:
    def __init__(self, weights: dict[str, float] | None = None) -> None:
        self.weights = weights or dict(DEFAULT_WEIGHTS)
        # Normalize weights so sum is 1.0
        total_w = sum(self.weights.values())
        if total_w > 0:
            self.weights = {k: v / total_w for k, v in self.weights.items()}

    def compute_budget_score(
        self,
        price: float | None,
        budget_min: float | None,
        budget_max: float | None,
    ) -> float:
        if price is None or price <= 0:
            return 50.0

        if budget_max is not None and price > budget_max:
            # Penalize price exceeding max budget
            overshoot_ratio = (price - budget_max) / budget_max
            return max(0.0, 100.0 - (overshoot_ratio * 150.0))

        if budget_min is not None and budget_max is not None:
            if budget_min <= price <= budget_max:
                span = budget_max - budget_min
                if span > 0:
                    pos = (price - budget_min) / span
                    return 100.0 - (pos * 20.0)  # Cheaper items within budget get up to 100
                return 95.0
            if price < budget_min:
                # Modest penalty if unrealistically cheap compared to requested tier
                diff = (budget_min - price) / budget_min
                return max(50.0, 100.0 - (diff * 50.0))

        if budget_max is not None and price <= budget_max:
            return 100.0 - ((price / budget_max) * 20.0)

        return 85.0

    def compute_spec_score(
        self,
        verified_specs: dict[str, Any],
        mandatory_specs: list[str],
        red_flags: list[str],
    ) -> tuple[float, list[str], list[str]]:
        pros: list[str] = []
        cons: list[str] = []

        if not mandatory_specs:
            return 85.0, ["Standard functional specifications verified."], []

        met_count = 0
        for req in mandatory_specs:
            spec_info = verified_specs.get(req)
            if spec_info and spec_info.get("status") == "verified":
                met_count += 1
                pros.append(f"Verified feature: {req}")
            elif spec_info and spec_info.get("status") == "unverified":
                met_count += 0.5
                cons.append(f"Unverified feature claim: {req}")
            else:
                cons.append(f"Missing mandatory specification: {req}")

        # Check red flags
        for flag in red_flags:
            if flag.lower() in [s.lower() for s in verified_specs.keys()]:
                cons.append(f"Deal breaker identified: {flag}")
                return 0.0, pros, cons

        score = (met_count / float(len(mandatory_specs))) * 100.0
        return min(100.0, max(0.0, score)), pros, cons

    def compute_review_score(
        self,
        reviews: list[dict[str, Any]],
        fake_metrics: dict[str, Any],
    ) -> float:
        if not reviews:
            return 60.0

        sentiments = [r.get("sentiment_score", 0.0) for r in reviews]
        avg_sentiment = sum(sentiments) / float(len(sentiments))
        # Map sentiment [-1.0, 1.0] to [0, 100]
        base_score = 50.0 + (avg_sentiment * 50.0)

        # Discount by fake probability
        fake_prob = fake_metrics.get("fake_probability", 0.0)
        discount = 1.0 - (0.7 * fake_prob)
        return min(100.0, max(0.0, base_score * discount))

    def compute_brand_score(self, candidate: DiscoveredCandidate) -> float:
        if candidate.brand_signal:
            return candidate.brand_signal.reputation_score
        return 50.0

    def compute_youtube_score(self, videos: list[dict[str, Any]]) -> float:
        if not videos:
            return 60.0

        scores = []
        for vid in videos:
            if vid.get("is_sponsored", False):
                scores.append(70.0)
            else:
                scores.append(90.0)
        return sum(scores) / float(len(scores))

    def compute_seller_score(
        self,
        offers: list[dict[str, Any]],
        color_available: bool,
        size_available: bool,
    ) -> float:
        if not offers:
            return 40.0

        valid_offers = [
            o for o in offers if o.get("status") == "verified" and o.get("in_stock", True)
        ]
        if not valid_offers:
            return 30.0

        score = 80.0
        if len(valid_offers) >= 2:
            score += 10.0
        if color_available and size_available:
            score += 10.0
        return min(100.0, score)

    def compute_confidence(self, candidate: DiscoveredCandidate) -> float:
        # 1. Source quantity (target 3+ sources: 2 sellers + 1 video or review)
        total_sources = len(candidate.seed_urls) + len(candidate.videos) + len(candidate.reviews)
        e_sources = min(1.0, total_sources / 4.0)

        # 2. Consensus agreement
        verified_specs = candidate.verified_specs
        total_specs = len(verified_specs)
        if total_specs > 0:
            verified_count = sum(
                1 for s in verified_specs.values() if s.get("status") == "verified"
            )
            e_agreement = verified_count / float(total_specs)
        else:
            e_agreement = 0.6

        # 3. Completeness
        e_completeness = 0.5
        if candidate.scraped_offers:
            e_completeness += 0.3
        if candidate.brand_signal:
            e_completeness += 0.2

        confidence = 100.0 * (0.35 * e_sources + 0.35 * e_agreement + 0.30 * e_completeness)
        return round(min(100.0, max(10.0, confidence)), 1)

    def generate_verdict(
        self,
        candidate: DiscoveredCandidate,
        score: float,
        pros: list[str],
        cons: list[str],
    ) -> str:
        brand = candidate.canonical_brand
        model = candidate.canonical_model

        if score >= 85.0:
            highlight = (
                pros[0] if pros else "Strong category specifications and verified reliability"
            )
            return f"{brand} {model}: Top recommendation. {highlight}."
        elif score >= 70.0:
            highlight = pros[0] if pros else "Balanced price to performance ratio"
            tradeoff = cons[0] if cons else "Minor feature tradeoffs"
            return f"{brand} {model}: Solid contender. {highlight}, but note: {tradeoff}."
        else:
            tradeoff = cons[0] if cons else "Unverified specifications or budget variance"
            return f"{brand} {model}: Secondary option. {tradeoff}."

    def score_candidate(
        self,
        candidate: DiscoveredCandidate,
        spec: StructuredQuerySpec | None,
    ) -> tuple[float, float, str, list[str], list[str]]:
        primary_price = None
        if candidate.scraped_offers:
            primary_price = candidate.scraped_offers[0].get("price")
        if primary_price is None:
            primary_price = candidate.estimated_price

        b_min = spec.budget_min if spec else None
        b_max = spec.budget_max if spec else None
        mandatory = spec.mandatory_specs if spec else []
        red_flags = spec.red_flags if spec else []

        s_budget = self.compute_budget_score(primary_price, b_min, b_max)
        s_spec, pros, cons = self.compute_spec_score(candidate.verified_specs, mandatory, red_flags)
        s_review = self.compute_review_score(candidate.reviews, candidate.fake_review_metrics)
        s_brand = self.compute_brand_score(candidate)
        s_youtube = self.compute_youtube_score(candidate.videos)
        s_seller = self.compute_seller_score(
            candidate.scraped_offers, candidate.color_available, candidate.size_available
        )

        total_score = (
            self.weights["budget_fit"] * s_budget
            + self.weights["spec_match"] * s_spec
            + self.weights["review_sentiment"] * s_review
            + self.weights["brand_reliability"] * s_brand
            + self.weights["youtube_consensus"] * s_youtube
            + self.weights["stock_seller_trust"] * s_seller
        )
        total_score = round(min(100.0, max(0.0, total_score)), 1)
        confidence = self.compute_confidence(candidate)
        verdict = self.generate_verdict(candidate, total_score, pros, cons)

        return total_score, confidence, verdict, pros, cons

    def generate_comparison_table(
        self,
        ranked_candidates: list[DiscoveredCandidate],
        top_n: int = 5,
    ) -> list[dict[str, Any]]:
        comparison = []
        for cand in ranked_candidates[:top_n]:
            best_offer = cand.scraped_offers[0] if cand.scraped_offers else {}
            comparison.append(
                {
                    "product_id": f"{cand.canonical_brand}-{cand.canonical_model}",
                    "brand": cand.canonical_brand,
                    "model": cand.canonical_model,
                    "title": cand.title,
                    "price": best_offer.get("price", cand.estimated_price or 0.0),
                    "currency": cand.currency,
                    "seller": best_offer.get("seller_name", "Direct"),
                    "score": cand.scraped_specs.get("score", 0.0),
                    "confidence": cand.scraped_specs.get("confidence", 0.0),
                    "warranty": cand.brand_signal.warranty_summary
                    if cand.brand_signal
                    else "Standard",
                    "verified_features": [
                        k for k, v in cand.verified_specs.items() if v.get("status") == "verified"
                    ],
                    "color_available": cand.color_available,
                    "size_available": cand.size_available,
                }
            )
        return comparison
