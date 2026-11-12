# Skill: Review Analysis and Fake Detection

- **Name**: review-analysis-and-fake-detection
- **Description**: Aggregate consumer feedback across marketplaces and forums, detect fake or incentivized review patterns, and calculate trust-weighted sentiment.

## When to Use
Use this skill in Stage 5 and Stage 6 to analyze customer reviews, compute credibility metrics, and filter out deceptive ratings.

## Step by Step Procedure
1. Ingest reviews from multiple sources (marketplaces, Reddit, dedicated enthusiast forums).
2. Compute rating distribution shape: flag bimodal distributions (disproportionate 5-star and 1-star clusters).
3. Compute verified purchase ratio: flag products with high volume of unverified reviews.
4. Detect burst anomalies: check if large percentages of positive reviews appeared within narrow date windows.
5. Identify repeated phrase templates or duplicate content across reviewer profiles.
6. Check for incentivized review keywords ("received free product", "in exchange for honest review").
7. Compute composite fake probability score $F \in [0, 1]$.
8. Discount raw sentiment ratings by fake probability factor.

## Code Patterns
```python
def calculate_fake_probability(
    rating_distribution: dict[int, int],
    verified_ratio: float,
    burst_detected: bool,
    incentivized_count: int,
    total_reviews: int,
) -> float:
    if total_reviews == 0:
        return 0.0
    score = 0.0
    five_star_pct = rating_distribution.get(5, 0) / total_reviews
    one_star_pct = rating_distribution.get(1, 0) / total_reviews
    if five_star_pct > 0.85 and verified_ratio < 0.4:
        score += 0.35
    if burst_detected:
        score += 0.25
    if incentivized_count / total_reviews > 0.15:
        score += 0.25
    if verified_ratio < 0.2:
        score += 0.15
    return min(1.0, score)
```

## Pitfalls
- Over-discounting legitimate products that have naturally high customer satisfaction.
- Treating all unverified reviews as fake: some platforms (like forums or Reddit) do not have purchase verification badges.
- Failing to account for low sample sizes (less than 10 reviews).

## Done Checklist
- [ ] Rating distribution analyzed.
- [ ] Verified purchase ratio calculated.
- [ ] Burst and template repetition heuristics applied.
- [ ] Sentiment score discounted appropriately.
- [ ] Raw third-party text preserved in database without modification.
