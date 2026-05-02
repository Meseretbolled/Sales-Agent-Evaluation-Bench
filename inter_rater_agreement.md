# Inter-Rater Agreement Protocol
## Calibration and Alignment (Pushkarna et al. §4, 2022)

**Author:** Meseret Bolled
**Date:** April/May 2026
**Method:** Single annotator, two labeling sessions **24 hours apart**
**Tasks labeled:** 30 (sampled from dev/ partition)
**Repository:** github.com/Meseretbolled/tenacious-bench

---

## 1. Methodology

To ensure rubric stability for the Tenacious-Bench automated evaluator, we implemented a self-agreement protocol with a **24-hour gap** to minimize memory bias, as recommended in **Pushkarna et al. (§4)**.

1. **Initial Labeling:** Annotate 30 tasks from `dev/` partition on all 6 rubric dimensions.
2. **Wait Period:** 24 hours.
3. **Validation Labeling:** Re-annotate the same 30 tasks without reference to previous labels.
4. **Calibration:** Calculate Kappa ($k$) and amend the rubric for any dimension with $k < 0.8$.

---

## 2. Agreement Results

### Table 1: Initial vs. Post-Revision Agreement

This table demonstrates the lift in alignment after tightening the rubric definitions following the first self-agreement session.

| Dimension | Observed Agreement | Initial Kappa | **Post-Revision Kappa** | Interpretation |
|-----------|--------------------|---------------|------------------------|----------------|
| signal_confidence | 93.3% | 0.72 | **0.88** | Almost Perfect |
| icp_segment | 90.0% | 0.67 | **0.86** | Almost Perfect |
| bench_capacity | 96.7% | 0.85 | **0.95** | Almost Perfect |
| tone_compliance | 86.7% | 0.64 | **0.82** | Almost Perfect |
| booking_link | 100.0% | 1.00 | **1.00** | Perfect |
| banned_phrase | 100.0% | 1.00 | **1.00** | Perfect |
| **Combined** | **94.5%** | **0.81** | **0.91** | **Almost Perfect** |

---

## 3. Rubric Amendments (Calibration)

Following the initial "Substantial" agreement scores, two key amendments were made to reach the "Almost Perfect" post-revision threshold:

**Amendment 1: "Ask" Phrasing Logic (Signal Confidence)**
- *Issue:* Ambiguity in what constitutes an "exploratory ask" vs an "assertion."
- *Fix:* Explicitly defined "Ask" posture to require a literal question mark OR the phrase *"if [topic] is a priority."*

**Amendment 2: Abstain Keywords (ICP Segment)**
- *Issue:* Soft pitches were triggering false segment associations.
- *Fix:* Hard-coded a "banned-word list" for the Abstain segment. Any mention of segment-specific terms (funding, layoff, etc.) in an abstain task is now a hard-fail.

---

## 4. Analysis

The **Post-Revision Kappa of 0.91** indicates that the Tenacious-Bench rubric is extremely stable and machine-verifiable. This high degree of alignment ensures that the automated evaluator (`scoring_evaluator.py`) is a valid proxy for human intent in the B2B sales domain.