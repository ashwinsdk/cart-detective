"""Pipeline orchestrator and real-time Server-Sent Events broadcaster."""

import asyncio
import json
import logging
import traceback
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any

from backend.database import get_session_factory
from backend.pipeline.context import PipelineContext
from backend.pipeline.stage1_understand import UnderstandStage
from backend.pipeline.stage2_discover import DiscoverStage
from backend.pipeline.stage3_brand import BrandResearchStage
from backend.pipeline.stage4_scrape import ScrapeStage
from backend.pipeline.stage5_reviews import ReviewMiningStage
from backend.pipeline.stage6_verify import VerificationStage
from backend.pipeline.stage7_score import ScoringStage
from backend.pipeline.stage8_present import PresentStage
from backend.repository import Repository

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    def __init__(self) -> None:
        self.event_queues: dict[str, list[asyncio.Queue]] = {}
        self.active_tasks: dict[str, asyncio.Task] = {}
        self.lock = asyncio.Lock()

    async def register_listener(self, run_id: str) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue()
        async with self.lock:
            if run_id not in self.event_queues:
                self.event_queues[run_id] = []
            self.event_queues[run_id].append(queue)
        return queue

    async def unregister_listener(self, run_id: str, queue: asyncio.Queue) -> None:
        async with self.lock:
            if run_id in self.event_queues and queue in self.event_queues[run_id]:
                self.event_queues[run_id].remove(queue)
                if not self.event_queues[run_id]:
                    del self.event_queues[run_id]

    async def broadcast_event(self, run_id: str, event_type: str, data: dict[str, Any]) -> None:
        async with self.lock:
            queues = list(self.event_queues.get(run_id, []))

        payload = {"event": event_type, **data, "timestamp": datetime.now(UTC).isoformat()}
        for q in queues:
            await q.put(payload)

    async def sse_generator(self, run_id: str) -> AsyncGenerator[dict[str, Any], None]:
        queue = await self.register_listener(run_id)
        try:
            while True:
                # Wait for next event with keepalive ping timeout
                try:
                    payload = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield {
                        "event": payload.get("event", "message"),
                        "data": json.dumps(payload),
                    }
                    if payload.get("event") in ("complete", "error"):
                        break
                except TimeoutError:
                    # Send keepalive ping comment
                    yield {
                        "event": "ping",
                        "data": json.dumps({"timestamp": datetime.now(UTC).isoformat()}),
                    }
        finally:
            await self.unregister_listener(run_id, queue)

    async def run_pipeline(self, search_id: str, run_id: str, raw_query: dict[str, Any]) -> None:
        async with self.lock:
            if run_id in self.active_tasks:
                logger.info(
                    f"Run {run_id} is already actively executing. Awaiting existing pipeline task."
                )
                existing_task = self.active_tasks[run_id]
            else:
                existing_task = None
                curr = asyncio.current_task()
                if curr:
                    self.active_tasks[run_id] = curr

        if existing_task is not None:
            await existing_task
            return

        ctx = PipelineContext(run_id=run_id, search_id=search_id, raw_query=raw_query)

        session_factory = get_session_factory()

        stages = [
            (1, "Understand", UnderstandStage()),
            (2, "Discover Candidates", DiscoverStage()),
            (3, "Brand Research", BrandResearchStage()),
            (4, "Crawl and Scrape", ScrapeStage()),
            (5, "Reviews and Video Mining", ReviewMiningStage()),
            (6, "Verify and Validate", VerificationStage()),
            (7, "Score and Rank", ScoringStage()),
            (8, "Present and Persist", PresentStage()),
        ]

        try:
            # Update DB run status to running
            async with session_factory() as session:
                repo = Repository(session)
                await repo.update_run_status(run_id, status="running")
                await session.commit()

            for stage_num, stage_name, stage_instance in stages:
                await self.broadcast_event(
                    run_id,
                    "stage_start",
                    {
                        "stage": stage_num,
                        "name": stage_name,
                    },
                )

                # Execute stage
                await stage_instance.execute(ctx)

                progress_pct = (stage_num / float(len(stages))) * 100.0

                # Update database progress
                async with session_factory() as session:
                    repo = Repository(session)
                    await repo.update_run_progress(
                        run_id,
                        stage=stage_num,
                        progress=progress_pct,
                        log_message=f"Completed {stage_name}",
                    )
                    await session.commit()

                await self.broadcast_event(
                    run_id,
                    "stage_complete",
                    {
                        "stage": stage_num,
                        "name": stage_name,
                        "progress": progress_pct,
                    },
                )

            # Broadcast final completion
            active_count = sum(1 for c in ctx.candidates if not c.is_dropped)
            await self.broadcast_event(
                run_id,
                "complete",
                {
                    "run_id": run_id,
                    "product_count": active_count,
                    "decision_rationale": ctx.decision_rationale,
                },
            )

        except Exception as exc:
            logger.error(f"Pipeline error for run {run_id}: {exc}\n{traceback.format_exc()}")
            err_msg = str(exc)
            async with session_factory() as session:
                repo = Repository(session)
                await repo.update_run_status(run_id, status="failed", error_message=err_msg)
                await session.commit()

            await self.broadcast_event(
                run_id,
                "error",
                {
                    "run_id": run_id,
                    "message": err_msg,
                },
            )
        finally:
            async with self.lock:
                self.active_tasks.pop(run_id, None)


orchestrator = PipelineOrchestrator()
