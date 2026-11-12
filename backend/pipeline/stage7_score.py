"""Stage 7: Transparent weighted scoring, confidence estimation, and ranking."""

import logging
import time

from backend.pipeline.context import DiscoveredCandidate, PipelineContext
from backend.scoring import ScoringEngine

logger = logging.getLogger(__name__)


class ScoringStage:
    def __init__(self, weights: dict[str, float] | None = None) -> None:
        self.engine = ScoringEngine(weights=weights)

    async def execute(self, ctx: PipelineContext) -> None:
        start_time = time.monotonic()
        ctx.log(7, "Starting Stage 7: Multi-Factor Scoring and Ranking")

        active_candidates = [c for c in ctx.candidates if not c.is_dropped]

        # Deduplicate active candidates by canonical brand and canonical model
        dedup_candidates: dict[str, DiscoveredCandidate] = {}
        for candidate in active_candidates:
            brand_norm = candidate.canonical_brand.strip().lower()
            model_norm = candidate.canonical_model.strip().lower()
            key = f"{brand_norm}:{model_norm}"
            if key not in dedup_candidates:
                dedup_candidates[key] = candidate
            else:
                existing = dedup_candidates[key]
                # Merge offers avoiding duplicate URLs
                existing_urls = {o.get("url") for o in existing.scraped_offers}
                for off in candidate.scraped_offers:
                    if off.get("url") not in existing_urls:
                        existing.scraped_offers.append(off)
                        existing_urls.add(off.get("url"))
                # Merge evidence
                existing_claims = {e.get("claim") for e in existing.claims_evidence}
                for ev in candidate.claims_evidence:
                    if ev.get("claim") not in existing_claims:
                        existing.claims_evidence.append(ev)
                        existing_claims.add(ev.get("claim"))
        active_candidates = list(dedup_candidates.values())

        for candidate in active_candidates:
            score, confidence, verdict, pros, cons = self.engine.score_candidate(
                candidate, ctx.spec
            )
            candidate.scraped_specs["score"] = score
            candidate.scraped_specs["confidence"] = confidence
            candidate.scraped_specs["verdict"] = verdict
            candidate.scraped_specs["pros"] = pros
            candidate.scraped_specs["cons"] = cons

        # Sort descending by score
        active_candidates.sort(key=lambda c: c.scraped_specs.get("score", 0.0), reverse=True)
        ctx.candidates = active_candidates + [c for c in ctx.candidates if c.is_dropped]

        # Generate comparison table and decision summary
        ctx.comparison_table = self.engine.generate_comparison_table(active_candidates, top_n=5)

        if active_candidates:
            top_item = active_candidates[0]
            top_score = top_item.scraped_specs.get("score", 0.0)
            ctx.decision_rationale = (
                f"Ranked {len(active_candidates)} active products across budget compliance, "
                f"spec verification, review sentiment, brand warranty, and video consensus. "
                f"Top recommendation is {top_item.title} with an overall score of {top_score}/100."
            )
        else:
            ctx.decision_rationale = (
                "No candidates met minimum brand reliability and budget constraints."
            )

        duration = (time.monotonic() - start_time) * 1000.0
        ctx.telemetry.stage_durations_ms["stage7_score"] = duration
        ctx.telemetry.stage_status["stage7_score"] = "completed"
        ctx.log(7, f"Stage 7 completed in {duration:.1f}ms")
