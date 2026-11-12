"""Stage 8: Presentation and persistence of pipeline results to database."""

import logging
import time

from backend.database import get_session_factory
from backend.pipeline.context import PipelineContext
from backend.repository import Repository

logger = logging.getLogger(__name__)


class PresentStage:
    def __init__(self) -> None:
        self.timeout_seconds = 5.0

    async def execute(self, ctx: PipelineContext) -> None:
        start_time = time.monotonic()
        ctx.log(8, "Starting Stage 8: Presentation and Persistence")

        session_factory = get_session_factory()
        async with session_factory() as session:
            repo = Repository(session)

            for candidate in ctx.candidates:
                if candidate.is_dropped:
                    continue

                # 1. Create Product
                specs = dict(candidate.scraped_specs)
                score = specs.pop("score", 0.0)
                confidence = specs.pop("confidence", 0.0)
                verdict = specs.pop("verdict", "")
                pros = specs.pop("pros", [])
                cons = specs.pop("cons", [])

                product = await repo.create_product(
                    run_id=ctx.run_id,
                    canonical_brand=candidate.canonical_brand,
                    canonical_model=candidate.canonical_model,
                    title=candidate.title,
                    description=specs.get("description", ""),
                    primary_category=ctx.spec.product_type if ctx.spec else "",
                    specs=specs,
                    score=score,
                    confidence=confidence,
                    pros=pros,
                    cons=cons,
                    verdict=verdict,
                )

                # 2. Add Offers
                for off in candidate.scraped_offers:
                    await repo.add_offer(
                        product_id=product.id,
                        seller_name=off.get("seller_name", "Unknown Seller"),
                        url=off.get("url", ""),
                        price=off.get("price", candidate.estimated_price or 0.0),
                        currency=off.get("currency", candidate.currency),
                        in_stock=off.get("in_stock", True),
                        color_available=off.get("color_available", candidate.color_available),
                        size_available=off.get("size_available", candidate.size_available),
                        status=off.get("status", "verified"),
                    )

                # 3. Add Reviews
                for rev in candidate.reviews:
                    await repo.add_review(
                        product_id=product.id,
                        source=rev.get("source", "community"),
                        url=rev.get("url", ""),
                        author=rev.get("author", "anonymous"),
                        rating=rev.get("rating"),
                        content=rev.get("content", ""),
                        sentiment_score=rev.get("sentiment_score", 0.0),
                        is_verified_purchase=rev.get("is_verified_purchase", False),
                        fake_probability=rev.get("fake_probability", 0.0),
                    )

                # 4. Add Videos
                for vid in candidate.videos:
                    await repo.add_video(
                        product_id=product.id,
                        youtube_video_id=vid.get("youtube_video_id", ""),
                        title=vid.get("title", ""),
                        channel_title=vid.get("channel_title", ""),
                        url=vid.get("url", ""),
                        transcript_summary=vid.get("transcript_summary", ""),
                        is_sponsored=vid.get("is_sponsored", False),
                        view_count=vid.get("view_count", 0),
                    )

                # 5. Add Evidence
                for ev in candidate.claims_evidence:
                    await repo.add_evidence(
                        product_id=product.id,
                        claim=ev.get("claim", ""),
                        source_url=ev.get("source_url", ""),
                        source_title=ev.get("source_title", ""),
                        verification_status=ev.get("verification_status", "verified"),
                    )

            # Mark Run completed
            await repo.update_run_status(ctx.run_id, status="completed")
            await repo.update_run_progress(
                ctx.run_id,
                stage=8,
                progress=100.0,
                log_message="Pipeline execution completed successfully.",
            )
            await session.commit()

        duration = (time.monotonic() - start_time) * 1000.0
        ctx.telemetry.stage_durations_ms["stage8_present"] = duration
        ctx.telemetry.stage_status["stage8_present"] = "completed"
        ctx.log(8, f"Stage 8 completed in {duration:.1f}ms")
