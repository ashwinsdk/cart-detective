"""Pluggable LLM provider abstraction and structured extraction models."""

import json
import logging
import re
from abc import ABC, abstractmethod
from typing import Any

import httpx
from pydantic import BaseModel, Field

from backend.config import settings

logger = logging.getLogger(__name__)


class StructuredQuerySpec(BaseModel):
    product_type: str
    budget_min: float | None = None
    budget_max: float | None = None
    currency: str = "INR"
    mandatory_specs: list[str] = Field(default_factory=list)
    standards_and_certifications: list[str] = Field(default_factory=list)
    red_flags: list[str] = Field(default_factory=list)
    search_keywords: list[str] = Field(default_factory=list)
    color_preferences: list[str] = Field(default_factory=list)
    size_fit_gender: str | None = None
    brands_included: list[str] = Field(default_factory=list)
    brands_excluded: list[str] = Field(default_factory=list)


class ReviewClaims(BaseModel):
    sentiment_score: float = 0.0
    pros: list[str] = Field(default_factory=list)
    cons: list[str] = Field(default_factory=list)
    summary: str = ""
    is_sponsored: bool = False


class BaseLLMProvider(ABC):
    @abstractmethod
    async def parse_query_spec(self, raw_input: dict[str, Any]) -> StructuredQuerySpec:
        """Parse raw user criteria into a typed query spec."""
        pass

    @abstractmethod
    async def extract_review_claims(self, text: str) -> ReviewClaims:
        """Extract sentiment, pros, cons, and sponsorship disclosures from review text."""
        pass


class HeuristicProvider(BaseLLMProvider):
    """Deterministic rule-based extractor operating completely offline without external keys."""

    async def parse_query_spec(self, raw_input: dict[str, Any]) -> StructuredQuerySpec:
        product_type = str(raw_input.get("product_type", "")).strip() or "general product"
        currency = str(raw_input.get("currency", "INR")).upper()

        b_min = raw_input.get("budget_min")
        b_max = raw_input.get("budget_max")

        budget_min = float(b_min) if b_min is not None else None
        budget_max = float(b_max) if b_max is not None else None

        # Look for numbers in product_type if budget not set
        if budget_max is None:
            match = re.search(
                r"(?:under|below|up to)\s*(\d+)(?:k|000)?", product_type, re.IGNORECASE
            )
            if match:
                raw_num = match.group(1)
                val = float(raw_num) * 1000 if int(raw_num) < 100 else float(raw_num)
                budget_max = val

        colors = raw_input.get("color_preferences", [])
        if isinstance(colors, str):
            colors = [c.strip() for c in colors.split(",") if c.strip()]

        size_gender = raw_input.get("size_fit_gender")
        must_haves = raw_input.get("must_haves") or ""
        deal_breakers = raw_input.get("deal_breakers") or ""

        mandatory_specs: list[str] = []
        standards: list[str] = []
        red_flags: list[str] = []

        # Category heuristics
        p_lower = product_type.lower()
        if "riding jacket" in p_lower or "motorcycle" in p_lower:
            standards.extend(["CE Level 2", "CE Level 1"])
            mandatory_specs.extend(["Elbow armor", "Shoulder armor"])
        elif "running shoe" in p_lower:
            mandatory_specs.extend(["Cushioning", "Breathable upper"])
        elif "backpack" in p_lower or "bag" in p_lower:
            mandatory_specs.extend(["Padded laptop sleeve", "Water resistant fabric"])

        if must_haves:
            mandatory_specs.extend([item.strip() for item in must_haves.split(",") if item.strip()])
        if deal_breakers:
            red_flags.extend([item.strip() for item in deal_breakers.split(",") if item.strip()])

        keywords = [product_type]
        if colors:
            keywords.extend(colors)
        if mandatory_specs:
            keywords.extend(mandatory_specs[:2])

        return StructuredQuerySpec(
            product_type=product_type,
            budget_min=budget_min,
            budget_max=budget_max,
            currency=currency,
            mandatory_specs=list(dict.fromkeys(mandatory_specs)),
            standards_and_certifications=list(dict.fromkeys(standards)),
            red_flags=list(dict.fromkeys(red_flags)),
            search_keywords=list(dict.fromkeys(keywords)),
            color_preferences=colors,
            size_fit_gender=size_gender,
            brands_included=raw_input.get("brands_included", []),
            brands_excluded=raw_input.get("brands_excluded", []),
        )

    async def extract_review_claims(self, text: str) -> ReviewClaims:
        text_lower = text.lower()
        is_sponsored = any(
            marker in text_lower
            for marker in [
                "#ad",
                "sponsored by",
                "sent by brand",
                "paid partnership",
                "promotion",
            ]
        )

        positives = [
            "excellent",
            "great",
            "durable",
            "comfortable",
            "high quality",
            "recommended",
            "value for money",
            "solid build",
        ]
        negatives = [
            "poor",
            "broke",
            "disappointed",
            "uncomfortable",
            "heavy",
            "cheap",
            "overpriced",
            "stitching torn",
        ]

        pos_count = sum(1 for word in positives if word in text_lower)
        neg_count = sum(1 for word in negatives if word in text_lower)

        pros: list[str] = []
        cons: list[str] = []

        if pos_count > 0:
            pros.append("Positive user feedback regarding durability and performance.")
        if neg_count > 0:
            cons.append("Some users reported fit or construction tradeoffs.")

        total = pos_count + neg_count
        score = 0.0
        if total > 0:
            score = (pos_count - neg_count) / float(total)

        summary = f"Review sentiment score {score:.2f} based on community feedback keywords."

        return ReviewClaims(
            sentiment_score=score,
            pros=pros,
            cons=cons,
            summary=summary,
            is_sponsored=is_sponsored,
        )


class GroqProvider(BaseLLMProvider):
    """Groq API provider utilizing free-tier Llama models with configurable model name."""

    def __init__(self, api_key: str, model: str | None = None) -> None:
        self.api_key = api_key
        self.model = model or settings.LLM_MODEL
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.heuristic_fallback = HeuristicProvider()

    async def parse_query_spec(self, raw_input: dict[str, Any]) -> StructuredQuerySpec:
        if not self.api_key:
            return await self.heuristic_fallback.parse_query_spec(raw_input)

        prompt = (
            "You are a shopping product research parser. Output pure JSON matching this schema:\n"
            "{\n"
            '  "product_type": "string",\n'
            '  "budget_min": float or null,\n'
            '  "budget_max": float or null,\n'
            '  "currency": "string",\n'
            '  "mandatory_specs": ["string"],\n'
            '  "standards_and_certifications": ["string"],\n'
            '  "red_flags": ["string"],\n'
            '  "search_keywords": ["string"],\n'
            '  "color_preferences": ["string"],\n'
            '  "size_fit_gender": "string or null",\n'
            '  "brands_included": ["string"],\n'
            '  "brands_excluded": ["string"]\n'
            "}\n"
            f"User Criteria: {json.dumps(raw_input)}"
        )

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(
                    self.base_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {
                                "role": "system",
                                "content": "You output JSON only without formatting wrappers.",
                            },
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": 0.0,
                        "response_format": {"type": "json_object"},
                    },
                )
                if res.status_code == 200:
                    data = res.json()
                    content = data["choices"][0]["message"]["content"]
                    parsed = json.loads(content)
                    return StructuredQuerySpec(**parsed)
        except Exception as exc:
            logger.warning(f"Groq parse failed ({exc}), falling back to heuristic")

        return await self.heuristic_fallback.parse_query_spec(raw_input)

    async def extract_review_claims(self, text: str) -> ReviewClaims:
        if not self.api_key:
            return await self.heuristic_fallback.extract_review_claims(text)

        prompt = (
            "Extract review claims as JSON:\n"
            "{\n"
            '  "sentiment_score": float between -1.0 and 1.0,\n'
            '  "pros": ["string"],\n'
            '  "cons": ["string"],\n'
            '  "summary": "string",\n'
            '  "is_sponsored": boolean\n'
            "}\n"
            f"Review text: {text[:2000]}"
        )

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(
                    self.base_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": "You output JSON only."},
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": 0.0,
                        "response_format": {"type": "json_object"},
                    },
                )
                if res.status_code == 200:
                    data = res.json()
                    content = data["choices"][0]["message"]["content"]
                    parsed = json.loads(content)
                    return ReviewClaims(**parsed)
        except Exception as exc:
            logger.warning(f"Groq review extraction failed ({exc}), falling back to heuristic")

        return await self.heuristic_fallback.extract_review_claims(text)


class GeminiProvider(BaseLLMProvider):
    """Google Gemini API provider with configurable model name."""

    def __init__(self, api_key: str, model: str | None = None) -> None:
        self.api_key = api_key
        self.model = model or settings.GEMINI_MODEL
        self.heuristic_fallback = HeuristicProvider()

    async def parse_query_spec(self, raw_input: dict[str, Any]) -> StructuredQuerySpec:
        if not self.api_key:
            return await self.heuristic_fallback.parse_query_spec(raw_input)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        prompt = f"Parse the shopping query into JSON: {json.dumps(raw_input)}"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(
                    url,
                    json={
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {"responseMimeType": "application/json"},
                    },
                )
                if res.status_code == 200:
                    data = res.json()
                    text = data["candidates"][0]["content"]["parts"][0]["text"]
                    return StructuredQuerySpec(**json.loads(text))
        except Exception as exc:
            logger.warning(f"Gemini parse failed ({exc}), falling back to heuristic")

        return await self.heuristic_fallback.parse_query_spec(raw_input)

    async def extract_review_claims(self, text: str) -> ReviewClaims:
        return await self.heuristic_fallback.extract_review_claims(text)


class OllamaProvider(BaseLLMProvider):
    """Local Ollama instance provider with configurable model name."""

    def __init__(self, base_url: str | None = None, model: str | None = None) -> None:
        self.base_url = base_url or settings.OLLAMA_BASE_URL
        self.model = model or settings.OLLAMA_MODEL
        self.heuristic_fallback = HeuristicProvider()

    async def parse_query_spec(self, raw_input: dict[str, Any]) -> StructuredQuerySpec:
        url = f"{self.base_url}/api/generate"
        prompt = f"Extract shopping criteria JSON: {json.dumps(raw_input)}"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(
                    url,
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "format": "json",
                        "stream": False,
                    },
                )
                if res.status_code == 200:
                    data = res.json()
                    return StructuredQuerySpec(**json.loads(data["response"]))
        except Exception as exc:
            logger.warning(f"Ollama parse failed ({exc}), falling back to heuristic")

        return await self.heuristic_fallback.parse_query_spec(raw_input)

    async def extract_review_claims(self, text: str) -> ReviewClaims:
        return await self.heuristic_fallback.extract_review_claims(text)


def get_llm_provider() -> BaseLLMProvider:
    provider = settings.LLM_PROVIDER.lower()
    if provider == "groq" and settings.GROQ_API_KEY:
        return GroqProvider(api_key=settings.GROQ_API_KEY, model=settings.LLM_MODEL)
    if provider == "gemini" and settings.GEMINI_API_KEY:
        return GeminiProvider(api_key=settings.GEMINI_API_KEY, model=settings.GEMINI_MODEL)
    if provider == "ollama":
        return OllamaProvider(base_url=settings.OLLAMA_BASE_URL, model=settings.OLLAMA_MODEL)
    return HeuristicProvider()
