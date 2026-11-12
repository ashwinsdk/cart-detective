# Skill: Product Verification and Validation

- **Name**: product-verification
- **Description**: Cross-corroborate product specifications, verify seller price consistency, check color and size availability, and tag unconfirmed claims as unverified.

## When to Use
Use this skill during Stage 6 to cross-check extracted claims against independent sources before scoring.

## Step by Step Procedure
1. Aggregate specification claims from all extracted sources (marketplace catalog, brand site, reviews).
2. For each key specification (dimensions, weight, armor rating, material, certifications):
   - Check if at least two independent domains assert identical or compatible values.
   - If asserted by only one source, mark attribute status as "unverified".
   - If sources contradict, flag as "disputed" and record differing values with their source URLs.
3. Verify seller price validity:
   - Check price across sellers.
   - Flag prices exceeding 2 standard deviations below the median as "suspicious".
   - Check offer timestamp: flag prices older than 7 days as "stale".
4. Check size and color availability:
   - Ensure the user requested color and size exist in stock at the stated price.
   - If out of stock or sold at an altered price tier, record the actual available price.
5. Create an evidence record linking each claim to its empirical source URL.

## Code Patterns
```python
def corroborate_spec(spec_name: str, claims: list[dict]) -> dict:
    values = [c["value"] for c in claims]
    sources = set(c["source_domain"] for c in claims)
    if len(sources) >= 2 and len(set(values)) == 1:
        return {
            "name": spec_name,
            "value": values[0],
            "status": "verified",
            "sources": list(sources),
        }
    return {
        "name": spec_name,
        "value": values[0] if values else None,
        "status": "unverified",
        "sources": list(sources),
    }
```

## Pitfalls
- Assuming a claim on a blog or listicle counts as an independent source when it merely scraped the marketplace.
- Marking an item as in-stock without verifying that the specific color and size requested are available at that price.
- Hallucinating missing specs: if data cannot be confirmed, always mark "unverified".

## Done Checklist
- [ ] At least two independent domains required for verified status.
- [ ] Size and color availability confirmed at listed price.
- [ ] Suspicious and stale prices flagged.
- [ ] Unconfirmed specs tagged as "unverified".
- [ ] Empirical source URLs attached to all claims.
