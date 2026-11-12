# Scoring Algorithm and Confidence Metric: Cart Detective

This document details the transparent mathematical formula used to rank products and quantify evidence confidence.

## 1. Score Composition

The total product score $S$ ranges from 0 to 100 and is calculated as a weighted sum of normalized component scores:

$$S = \sum_{i} w_i \cdot s_i$$

Where $\sum w_i = 1.0$ and each component score $s_i \in [0, 100]$.

### Default Dimension Weights

| Dimension | Default Weight ($w_i$) | Description |
| :--- | :--- | :--- |
| **Budget Fit** ($s_{\text{budget}}$) | 0.20 | Proximity to user budget without exceeding max limit |
| **Spec Match** ($s_{\text{spec}}$) | 0.20 | Percentage of mandatory specifications and safety standards satisfied |
| **Review Sentiment** ($s_{\text{review}}$) | 0.20 | Multi-source sentiment, weighted by reviewer credibility and verified status |
| **Brand Reliability** ($s_{\text{brand}}$) | 0.15 | Brand track record, service presence, and warranty coverage |
| **YouTube Consensus** ($s_{\text{youtube}}$) | 0.15 | Synthesis of hands-on reviewer verdicts, pros, and cons |
| **Stock & Seller Trust** ($s_{\text{seller}}$) | 0.10 | Verified seller standing, return policy, and color/size availability |

All weights are configurable in the Settings page and stored in the database.

---

## 2. Component Formulations

### 2.1 Budget Fit ($s_{\text{budget}}$)
- If listed price $P > P_{\text{max}}$, $s_{\text{budget}} = \max(0, 100 - 15 \cdot \frac{P - P_{\text{max}}}{P_{\text{max}}} \cdot 100)$.
- If $P_{\text{min}} \le P \le P_{\text{max}}$, $s_{\text{budget}} = 100 - 20 \cdot \frac{P - P_{\text{min}}}{P_{\text{max}} - P_{\text{min}}}$.
- If $P < P_{\text{min}}$, score scales based on whether extreme low price signals low quality.

### 2.2 Spec Compliance ($s_{\text{spec}}$)
- Let $M$ be the total required specifications and $M_{\text{met}}$ be those verified.
- $s_{\text{spec}} = 100 \cdot \frac{M_{\text{met}}}{M}$.
- Presence of any identified deal breaker sets $s_{\text{spec}} = 0$.

### 2.3 Review Sentiment ($s_{\text{review}}$)
- Calculated from verified marketplace reviews, Reddit threads, and forum discussions.
- Raw ratings are discounted by the fake review probability factor $F \in [0, 1]$:
  $$s_{\text{review}} = \text{RawScore} \cdot (1 - 0.7 \cdot F)$$
- Fake indicators include bimodal 5/1 distributions, bursts of reviews within a narrow date range, and repeated boilerplate phrases.

### 2.4 Brand Reliability ($s_{\text{brand}}$)
- Evaluates manufacturer warranty length, local service center density, and forum reputation signals.

### 2.5 YouTube Consensus ($s_{\text{youtube}}$)
- Aggregated from transcript analysis of top 3 to 5 review videos.
- Factors in ratio of positive to negative claims and notes sponsored versus independent reviews.

---

## 3. Confidence Metric

The confidence score $C \in [0, 100]$ indicates how well-substantiated the product ranking is:

$$C = 100 \cdot (0.35 \cdot E_{\text{sources}} + 0.35 \cdot E_{\text{agreement}} + 0.30 \cdot E_{\text{completeness}})$$

Where:
- $E_{\text{sources}}$: Ratio of available sources relative to the optimal target (e.g., at least 2 retail sources, 1 forum thread, 1 video review).
- $E_{\text{agreement}}$: Degree of consensus across specifications and sentiment across independent sources.
- $E_{\text{completeness}}$: Percentage of product attributes verified with source URLs.

If evidence is sparse, the product rank reflects a lower confidence score, warning the user of potential data gaps.
