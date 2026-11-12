"""Stage 1: Understand user criteria into structured query spec."""

import asyncio
import logging
import time

from backend.pipeline.context import PipelineContext
from backend.services.llm import BaseLLMProvider, HeuristicProvider, get_llm_provider

logger = logging.getLogger(__name__)


class UnderstandStage:
    def __init__(self, llm_provider: BaseLLMProvider | None = None) -> None:
        self.llm = llm_provider or get_llm_provider()
        self.timeout_seconds = 10.0
        self.max_retries = 2

    async def execute(self, ctx: PipelineContext) -> None:
        start_time = time.monotonic()
        ctx.log(1, "Starting Stage 1: Query Understanding")

        for attempt in range(self.max_retries):
            try:
                spec = await asyncio.wait_for(
                    self.llm.parse_query_spec(ctx.raw_query),
                    timeout=self.timeout_seconds,
                )
                ctx.spec = spec
                ctx.log(
                    1,
                    f"Parsed specification for {spec.product_type} with max budget {spec.budget_max} {spec.currency}",
                )
                if not ctx.raw_query.get("brands_included") and spec.brands_included:
                    ctx.log(
                        1,
                        f"Auto-discovered authoritative brands for {spec.product_type}: {', '.join(spec.brands_included)}",
                    )
                if not ctx.raw_query.get("marketplaces") and spec.marketplaces:
                    ctx.log(
                        1,
                        f"Auto-discovered target marketplaces for {spec.currency}: {', '.join(spec.marketplaces)}",
                    )
                break
            except Exception as exc:
                ctx.telemetry.partial_failures.append(
                    f"Stage 1 attempt {attempt + 1} failed: {exc}"
                )
                ctx.log(1, f"Attempt {attempt + 1} failed ({exc}). Retrying...", level="WARNING")
                if attempt == self.max_retries - 1:
                    ctx.log(1, "Falling back to deterministic heuristic parser.", level="WARNING")
                    fallback = HeuristicProvider()
                    ctx.spec = await fallback.parse_query_spec(ctx.raw_query)

        duration = (time.monotonic() - start_time) * 1000.0
        ctx.telemetry.stage_durations_ms["stage1_understand"] = duration
        ctx.telemetry.stage_status["stage1_understand"] = "completed"
        ctx.log(1, f"Stage 1 completed in {duration:.1f}ms")
