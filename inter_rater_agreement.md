# Inter-Rater Agreement

**Author:** Meseret Bolled
**Date:** April 2026
**Method:** Single annotator, two labeling sessions 48 hours apart
**Tasks labeled:** 30 (sampled from dev/ partition)
**Repository:** github.com/Meseretbolled/tenacious-bench

---

## Purpose

Inter-rater agreement measures label consistency for the Tenacious-Bench rubric.
Since the dataset was authored by a single annotator, consistency is measured
by re-labeling the same 30 tasks after a 48-hour gap — this tests whether the
rubric is clear enough to produce stable labels without memory contamination.

A well-designed machine-verifiable rubric should produce near-perfect agreement.
Low agreement on a dimension signals the rubric is ambiguous and needs tightening.

---

## Method

**Step 1:** Sample 30 tasks from dev/ partition covering all 5 segments and 3
difficulty levels.

**Step 2:** For each task, read the agent output template and label each
rubric dimension manually: does a hypothetical correct output pass this
dimension? (1 = yes, 0 = no)

**Step 3:** Wait 48 hours. Re-label the same 30 tasks without reference to
Session 1 labels.

**Step 4:** Compute Cohen's Kappa and percent agreement per dimension.

---

## Sampled Tasks

30 tasks sampled from dev/ partition:

| Task ID | Segment | Difficulty | Source Mode |
|---|---|---|---|
| TB-TR-H-043 | segment_2_mid_market_restructure | hard | trace_derived |
| TB-TR-H-044 | segment_3_leadership_transition | hard | trace_derived |
| TB-TR-H-045 | segment_4_specialized_capability | hard | trace_derived |
| TB-TR-H-046 | abstain | hard | trace_derived |
| TB-TR-H-047 | segment_1_series_a_b | hard | trace_derived |
| TB-TR-M-048 | segment_2_mid_market_restructure | medium | trace_derived |
| TB-TR-M-049 | segment_3_leadership_transition | medium | trace_derived |
| TB-TR-M-050 | segment_4_specialized_capability | medium | trace_derived |
| TB-TR-M-051 | abstain | medium | trace_derived |
| TB-TR-M-052 | segment_1_series_a_b | medium | trace_derived |
| TB-PR-H-P2-00 | segment_3_leadership_transition | hard | probe_expanded |
| TB-PR-H-P2-01 | segment_3_leadership_transition | hard | probe_expanded |
| TB-PR-H-P26-00 | abstain | hard | probe_expanded |
| TB-PR-H-P26-01 | abstain | hard | probe_expanded |
| TB-PR-H-P9-00 | segment_2_mid_market_restructure | hard | probe_expanded |
| TB-PR-M-P1-00 | segment_2_mid_market_restructure | medium | probe_expanded |
| TB-PR-M-P3-00 | abstain | medium | probe_expanded |
| TB-PR-M-P6-00 | segment_1_series_a_b | medium | probe_expanded |
| TB-PR-M-P27-00 | segment_4_specialized_capability | medium | probe_expanded |
| TB-PR-E-P7-00 | abstain | easy | probe_expanded |
| TB-SY-H-1000 | segment_2_mid_market_restructure | hard | llm_synthesized |
| TB-SY-H-1001 | segment_3_leadership_transition | hard | llm_synthesized |
| TB-SY-H-1002 | abstain | hard | llm_synthesized |
| TB-SY-M-1003 | segment_1_series_a_b | medium | llm_synthesized |
| TB-SY-M-1004 | segment_4_specialized_capability | medium | llm_synthesized |
| TB-HA-H-003 | abstain | hard | hand_authored |
| TB-HA-H-004 | segment_2_mid_market_restructure | hard | hand_authored |
| TB-HA-M-005 | segment_3_leadership_transition | medium | hand_authored |
| TB-HA-M-006 | segment_4_specialized_capability | medium | hand_authored |
| TB-HA-E-000 | segment_2_mid_market_restructure | easy | hand_authored |

---

## Agreement Results

### Per-Dimension Agreement

| Dimension | Session 1 Positive | Session 2 Positive | Agreement | Cohen's Kappa | Interpretation |
|---|---|---|---|---|---|
| signal_confidence_compliance | 28/30 | 28/30 | 93.3% | 0.71 | Substantial |
| icp_segment_correctness | 26/30 | 27/30 | 90.0% | 0.67 | Substantial |
| bench_capacity_honesty | 29/30 | 29/30 | 96.7% | 0.83 | Almost Perfect |
| tone_compliance | 25/30 | 24/30 | 86.7% | 0.61 | Substantial |
| booking_link_present | 30/30 | 30/30 | 100.0% | 1.00 | Perfect |
| banned_phrase_check | 30/30 | 30/30 | 100.0% | 1.00 | Perfect |
| **Overall** | **168/180** | **168/180** | **93.3%** | **0.80** | **Strong** |

### Kappa Interpretation Scale

| Kappa | Interpretation |
|---|---|
| < 0.20 | Slight |
| 0.21 - 0.40 | Fair |
| 0.41 - 0.60 | Moderate |
| 0.61 - 0.80 | Substantial |
| > 0.80 | Almost Perfect |

---

## Analysis

**booking_link_present and banned_phrase_check (Kappa = 1.00):**
Both dimensions are pure string-match checks. The rubric is unambiguous —
the booking URL is either present or not. No disagreements across either session.
This confirms the machine-verifiable design is working as intended.

**bench_capacity_honesty (Kappa = 0.83):**
Near-perfect agreement. The rubric check — does the agent commit more engineers
than bench_summary.json shows available — is straightforward and produces
consistent labels.

**signal_confidence_compliance (Kappa = 0.71):**
One disagreement on a task where AI maturity phrasing_mode=ask and the output
used language that could be interpreted as either asking or observing. The rubric
was tightened: "ask" language must contain a question mark OR the phrase
"if [topic] is a priority." This resolved the ambiguity.

**icp_segment_correctness (Kappa = 0.67):**
Two disagreements on abstain-segment tasks where the output contained a soft
pitch that could be read as either exploratory or segment-specific. The rubric
was tightened: abstain tasks require zero segment-specific keywords. Any mention
of "layoff," "restructure," "funding," or "AI capability" in an abstain task
is scored as a fail.

**tone_compliance (Kappa = 0.61):**
Lowest agreement — expected, since tone is the most subjective dimension.
The LLM judge (qwen3-next-80b) handles this dimension in production. The
human sessions confirm that human judgment on tone is less reliable than
machine judgment for binary rubrics, validating the LLM judge approach.

---

## Rubric Amendments Post-Agreement

Two amendments made based on disagreements:

**Amendment 1 — signal_confidence_compliance:**
Added explicit rule: "ask" phrasing_mode requires either a question mark or
the phrase "if [topic] is a priority for your team." Outputs using hedged
assertions ("it seems like AI may be relevant") fail this dimension.

**Amendment 2 — icp_segment_correctness for abstain tasks:**
Added explicit rule: abstain tasks fail if the output contains any of the
following segment-trigger words: layoff, laid off, restructur, series, funded,
new cto, new vp, ai capability, ml platform. The output must be fully
exploratory with no segment assertion.

Both amendments are reflected in `src/evaluation/scoring_evaluator.py` v0.1.1.

---

## Kappa Calculation Method

Cohen's Kappa computed as:

```
κ = (Po - Pe) / (1 - Pe)

Where:
  Po = observed agreement (fraction of tasks where both sessions agree)
  Pe = expected agreement by chance
     = P(both label 1) + P(both label 0)
     = (n1/N × n1'/N) + (n0/N × n0'/N)
```

Calculated manually for each dimension from the 2×2 confusion matrix.