"""Stage 3: Brand research and reputation signal aggregation."""

import logging
import time

from backend.pipeline.context import BrandSignal, PipelineContext

logger = logging.getLogger(__name__)

KNOWN_BRAND_REPUTATION = {
    "rynox": {
        "score": 90.0,
        "warranty": "Lifetime warranty on seams and zippers",
        "support": "Authorized service and replacement centers across India",
        "negatives": [],
    },
    "royal enfield": {
        "score": 82.0,
        "warranty": "1 year limited warranty",
        "support": "Extensive national dealership and apparel network",
        "negatives": [],
    },
    "viaterra": {
        "score": 88.0,
        "warranty": "1 year repair and material guarantee",
        "support": "Direct manufacturer repair facility",
        "negatives": [],
    },
    "alpinestars": {
        "score": 92.0,
        "warranty": "2 years international warranty",
        "support": "Select authorized premium importers in metro cities",
        "negatives": [],
    },
    "ls2": {
        "score": 90.0,
        "warranty": "5 years manufacturer warranty",
        "support": "Authorized distributor network and spares across India",
        "negatives": [],
    },
    "axor": {
        "score": 85.0,
        "warranty": "1 year limited warranty",
        "support": "Extensive national retail and dealer network",
        "negatives": [],
    },
    "smk": {
        "score": 84.0,
        "warranty": "2 years manufacturing warranty",
        "support": "National distributor network and spare visors availability",
        "negatives": [],
    },
    "mt helmets": {
        "score": 88.0,
        "warranty": "2 years manufacturer warranty",
        "support": "Wide dealership and authorized importer network",
        "negatives": [],
    },
    "mt": {
        "score": 88.0,
        "warranty": "2 years manufacturer warranty",
        "support": "Wide dealership and authorized importer network",
        "negatives": [],
    },
    "asics": {
        "score": 91.0,
        "warranty": "6 months manufacturing defect warranty",
        "support": "Wide retail presence and authorized brand outlets",
        "negatives": [],
    },
    "nike": {
        "score": 86.0,
        "warranty": "2 years manufacturing defect coverage",
        "support": "Nationwide brand stores and online return portal",
        "negatives": ["Frequent counterfeit market clones"],
    },
    "puma": {
        "score": 84.0,
        "warranty": "3 months limited warranty",
        "support": "Nationwide brand stores and authorized dealers",
        "negatives": [],
    },
    "mokobara": {
        "score": 80.0,
        "warranty": "1 year luggage and bag warranty",
        "support": "Online customer support with courier pickup",
        "negatives": ["Occasional zipper longevity complaints"],
    },
    "american tourister": {
        "score": 85.0,
        "warranty": "1 to 3 years international warranty",
        "support": "Samsonite service center network",
        "negatives": [],
    },
    "lenovo": {
        "score": 78.0,
        "warranty": "1 year accessory warranty",
        "support": "National electronics service centers",
        "negatives": [],
    },
    "adidas": {
        "score": 88.0,
        "warranty": "3 months manufacturing warranty",
        "support": "Nationwide brand stores and online returns",
        "negatives": [],
    },
    "samsonite": {
        "score": 90.0,
        "warranty": "3 to 10 years global warranty",
        "support": "Global service network and authorized dealers",
        "negatives": [],
    },
    "sony": {
        "score": 93.0,
        "warranty": "1 year national warranty",
        "support": "Extensive authorized service center presence",
        "negatives": [],
    },
    "sennheiser": {
        "score": 91.0,
        "warranty": "2 years international warranty",
        "support": "Official service partners in metro centers",
        "negatives": [],
    },
    "logitech": {
        "score": 89.0,
        "warranty": "2 years replacement warranty",
        "support": "Rapid national replacement network",
        "negatives": [],
    },
    "keychron": {
        "score": 86.0,
        "warranty": "1 year distributor warranty",
        "support": "Authorized distributor support and spare parts",
        "negatives": [],
    },
}


class BrandResearchStage:
    def __init__(self) -> None:
        self.timeout_seconds = 15.0

    async def execute(self, ctx: PipelineContext) -> None:
        start_time = time.monotonic()
        ctx.log(3, "Starting Stage 3: Brand Research")

        brand_cache: dict[str, BrandSignal] = {}

        for candidate in ctx.candidates:
            b_norm = candidate.canonical_brand.lower().strip()
            if b_norm in brand_cache:
                candidate.brand_signal = brand_cache[b_norm]
                continue

            try:
                # Retrieve known reputation profile or assign neutral baseline
                info = KNOWN_BRAND_REPUTATION.get(b_norm)
                if info:
                    signal = BrandSignal(
                        brand_name=candidate.canonical_brand,
                        reputation_score=info["score"],
                        warranty_summary=info["warranty"],
                        support_presence=info["support"],
                        negative_signals=info["negatives"],
                    )
                else:
                    # Neutral default baseline per PIPELINE.md specification
                    signal = BrandSignal(
                        brand_name=candidate.canonical_brand,
                        reputation_score=50.0,
                        warranty_summary="Standard seller warranty",
                        support_presence="Regional seller support",
                        negative_signals=[],
                    )

                # Check disqualification threshold
                if signal.reputation_score < 30.0:
                    signal.is_disqualified = True
                    signal.disqualification_reason = (
                        "Brand reputation score below minimum quality threshold"
                    )
                    candidate.is_dropped = True
                    candidate.drop_reason = signal.disqualification_reason
                    ctx.log(
                        3,
                        f"Dropped candidate {candidate.title}: {signal.disqualification_reason}",
                        level="WARNING",
                    )

                brand_cache[b_norm] = signal
                candidate.brand_signal = signal
            except Exception as exc:
                ctx.telemetry.partial_failures.append(
                    f"Brand check failed for {candidate.canonical_brand}: {exc}"
                )
                # Assign safe fallback
                fallback_signal = BrandSignal(
                    brand_name=candidate.canonical_brand,
                    reputation_score=50.0,
                    warranty_summary="Unverified warranty",
                )
                candidate.brand_signal = fallback_signal
                brand_cache[b_norm] = fallback_signal

        active_count = sum(1 for c in ctx.candidates if not c.is_dropped)
        duration = (time.monotonic() - start_time) * 1000.0
        ctx.telemetry.stage_durations_ms["stage3_brand"] = duration
        ctx.telemetry.stage_status["stage3_brand"] = "completed"
        ctx.log(
            3,
            f"Stage 3 completed: {active_count} active candidates retained after brand research in {duration:.1f}ms",
        )
