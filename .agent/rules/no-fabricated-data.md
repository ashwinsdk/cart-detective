# Rule: Zero Fabricated Data

## Scope
Applies to all scrapers, LLM extraction pipelines, scoring models, and UI data presenters.

## Requirements
1. **Source Grounding**:
   - Every product, specification, seller price, and review snippet must link directly to an empirical source URL.
   - If an attribute cannot be found or corroborated, mark it explicitly as "unverified".
2. **No Hallucinated Pricing**:
   - Never extrapolate or interpolate seller pricing. If an item is out of stock or price is obscured, mark status as "unavailable".
3. **Audit Trail**:
   - Persist evidence records in the database linking the exact claim to the source URL and retrieval timestamp.
