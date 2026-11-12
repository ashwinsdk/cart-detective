"""Pipeline context and state models for Cart Detective."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from backend.services.llm import StructuredQuerySpec


@dataclass
class BrandSignal:
    brand_name: str
    reputation_score: float = 50.0
    warranty_summary: str = "Standard manufacturer warranty"
    support_presence: str = "National authorized service"
    negative_signals: list[str] = field(default_factory=list)
    is_disqualified: bool = False
    disqualification_reason: str | None = None


@dataclass
class DiscoveredCandidate:
    canonical_brand: str
    canonical_model: str
    title: str
    seed_urls: list[str] = field(default_factory=list)
    estimated_price: float | None = None
    currency: str = "INR"
    brand_signal: BrandSignal | None = None
    is_dropped: bool = False
    drop_reason: str | None = None

    # Stage 4 to 6 attributes
    scraped_specs: dict[str, Any] = field(default_factory=dict)
    scraped_offers: list[dict[str, Any]] = field(default_factory=list)
    reviews: list[dict[str, Any]] = field(default_factory=list)
    videos: list[dict[str, Any]] = field(default_factory=list)
    verified_specs: dict[str, Any] = field(default_factory=dict)
    claims_evidence: list[dict[str, Any]] = field(default_factory=list)
    fake_review_metrics: dict[str, Any] = field(default_factory=dict)
    color_available: bool = True
    size_available: bool = True


@dataclass
class PipelineTelemetry:
    stage_durations_ms: dict[str, float] = field(default_factory=dict)
    stage_status: dict[str, str] = field(default_factory=dict)
    partial_failures: list[str] = field(default_factory=list)


@dataclass
class PipelineContext:
    run_id: str
    search_id: str
    raw_query: dict[str, Any]
    spec: StructuredQuerySpec | None = None
    candidates: list[DiscoveredCandidate] = field(default_factory=list)
    telemetry: PipelineTelemetry = field(default_factory=PipelineTelemetry)
    logs: list[dict[str, Any]] = field(default_factory=list)

    def log(self, stage: int, message: str, level: str = "INFO") -> None:
        self.logs.append(
            {
                "timestamp": datetime.now(UTC).isoformat(),
                "stage": stage,
                "level": level,
                "message": message,
            }
        )
