# Skill: LLM Extraction with Groq and Pluggable Providers

- **Name**: llm-extraction-groq
- **Description**: Convert unstructured user criteria and reviews into typed Pydantic models using Groq with seamless fallback to Gemini, Ollama, or deterministic regex.

## When to Use
Use this skill in Stage 1 (query parsing) and Stage 5 (review claim extraction) to structure text inputs.

## Step by Step Procedure
1. Verify provider configuration from environment variables (`LLM_PROVIDER`, `LLM_MODEL`). Do not hardcode model names.
2. If `LLM_PROVIDER` is `groq` and `GROQ_API_KEY` is present, initialize the Groq client.
3. If Groq is missing or errors out, attempt fallback to Gemini or Ollama if configured.
4. If no external LLM is accessible, use the deterministic `HeuristicProvider`.
5. Construct prompts with strict JSON schema instructions and zero temperature.
6. Validate output using Pydantic v2 schemas (`model_validate_json`).
7. Log provider used, execution latency, and token consumption.

## Code Patterns
```python
from pydantic import BaseModel, Field

class StructuredQuerySpec(BaseModel):
    category: str
    budget_min: float | None = None
    budget_max: float | None = None
    currency: str = "INR"
    mandatory_specs: list[str] = Field(default_factory=list)
    red_flags: list[str] = Field(default_factory=list)
```

## Pitfalls
- Hardcoding `llama-3.3-70b-versatile`: load the model name from `os.getenv("LLM_MODEL")`.
- Crashing when JSON contains unexpected markdown backticks: strip markdown fences before JSON parsing.
- Allowing pipeline to fail completely when API keys are absent: always fall back to the heuristic provider.

## Done Checklist
- [ ] Model names read from configuration.
- [ ] Pydantic v2 validation enforced on LLM output.
- [ ] Heuristic fallback operational with no API keys.
- [ ] Markdown code block fences stripped safely.
