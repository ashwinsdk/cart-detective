# Skill: Product Scoring and Confidence Calculation

- **Name**: product-scoring
- **Description**: Calculate transparent multi-dimensional weighted scores, confidence ratings, and generate objective decision explanations.

## When to Use
Use this skill during Stage 7 of the pipeline to synthesize all verified metrics into a transparent ranking.

## Step by Step Procedure
1. Load user or default scoring weights (budget, spec, review, brand, youtube, seller).
2. Normalize all individual component scores to a 0 to 100 scale.
3. Compute total score $S = \sum w_i \cdot s_i$.
4. Compute confidence metric $C$ based on evidence volume, cross-source consensus, and spec completeness.
5. Generate objective verdict line: state primary strengths, notable tradeoffs, and the specific reason for ranking.
6. Build top 3 to 5 side-by-side comparison matrix.

## Code Patterns
```python
def compute_product_score(metrics: dict, weights: dict) -> tuple[float, float]:
    total_score = sum(metrics[dim] * weights[dim] for dim in weights)
    evidence_count = metrics.get("evidence_count", 1)
    consensus_rate = metrics.get("consensus_rate", 0.5)
    completeness = metrics.get("completeness", 0.5)
    confidence = 100.0 * (0.35 * min(1.0, evidence_count / 5.0) + 0.35 * consensus_rate + 0.30 * completeness)
    return round(total_score, 1), round(confidence, 1)
```

## Pitfalls
- Hardcoding weights in Python logic instead of reading from configuration or settings.
- Allowing confidence score to reach 100% when key specifications remain unverified.
- Using hyperbolic marketing phrases in verdict lines instead of objective, factual statements.

## Done Checklist
- [ ] Weights dynamically configurable via settings.
- [ ] Sum of weights verified to equal 1.0.
- [ ] Confidence metric computed from empirical evidence volume.
- [ ] Verdict line written in concise, factual prose.
- [ ] No emojis or unicode dashes present.
