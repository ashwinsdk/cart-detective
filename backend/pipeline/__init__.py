"""Cart Detective pipeline stages package."""

from backend.pipeline.context import (
    BrandSignal,
    DiscoveredCandidate,
    PipelineContext,
    PipelineTelemetry,
)
from backend.pipeline.stage1_understand import UnderstandStage
from backend.pipeline.stage2_discover import DiscoverStage
from backend.pipeline.stage3_brand import BrandResearchStage
from backend.pipeline.stage4_scrape import ScrapeStage
from backend.pipeline.stage5_reviews import ReviewMiningStage
from backend.pipeline.stage6_verify import VerificationStage

__all__ = [
    "BrandResearchStage",
    "BrandSignal",
    "DiscoverStage",
    "DiscoveredCandidate",
    "PipelineContext",
    "PipelineTelemetry",
    "ReviewMiningStage",
    "ScrapeStage",
    "UnderstandStage",
    "VerificationStage",
]
