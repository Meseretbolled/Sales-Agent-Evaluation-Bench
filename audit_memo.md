# Benchmark Audit Memo
## What Existing Benchmarks Miss for Tenacious-Style B2B Sales Work

**Author:** Meseret Bolled  
**Date:** Week 11 — Act I  
**Repo:** github.com/Meseretbolled/Sales-Agent-Evaluation-Bench  
**Week 10 Reference:** github.com/Meseretbolled/conversion-engine

---

## 1. The Question

The Tenacious executive team asked: *"How do we know this agent works for our business, our voice, our segments, our bench?"*

τ²-Bench retail cannot answer this. This memo documents exactly why — and what a Tenacious-specific benchmark must measure instead.

---

## 2. What τ²-Bench Retail Measures (and Why It Doesn't Transfer)

τ²-Bench evaluates agents on retail shopping tasks: product search, cart management, checkout, return initiation. Its scoring rubric rewards correct product selection, accurate price lookup, form-filling precision, and multi-step navigation reliability. These are **deterministic, UI-grounded tasks** with binary ground truth.

| τ²-Bench Retail Assumes | Tenacious Reality |
|-------------------------|-------------------|
| Ground truth = correct product in cart | Ground truth = signal-grounded, tone-compliant outreach draft |
| Agent interacts with a structured UI | Agent synthesizes unstructured public signal (Crunchbase, layoffs.fyi, LinkedIn) |
| Pass/fail is deterministic | Pass/fail requires rubric judgment on 5 tone markers + 1 capacity constraint |
| No domain voice requirements | Strict style guide with 12 labeled "good" and 12 labeled "bad" pairs |
| Capacity is unlimited | Bench capacity is constrained; over-commitment is a contract violation |
| Prospect context = search query | Prospect context = ICP segment + AI maturity + signal confidence + bench state |

A Week 10 agent that scores 0.72 on τ²-Bench retail may simultaneously over-commit bench capacity, assert on low-confidence signal, and use banned phrases — all failures invisible to the retail benchmark.

---

## 3. What AgentBench and WebArena Also Miss

**AgentBench** (Liu et al., ICLR 2024) covers OS interaction, database, web shopping, web browsing, and card games. Its environments share τ²-Bench's core limitation: none test constraint-aware natural language generation under a domain-specific voice policy with labeled ground truth examples.

**WebArena** covers general web navigation tasks. Inapplicable: Tenacious outreach does not involve web navigation — it involves synthesizing signals from multiple structured sources into compliant drafts with specific honesty and tone constraints.

---

## 4. Three Specific Gap Findings from Week 10 Traces

The following failures were observed in the Week 10 conversion engine trace log and cannot be measured by any existing public benchmark.

### Gap 1: Signal Confidence Calibration Failure

**What τ²-Bench misses:** Whether the agent correctly varies its phrasing based on signal confidence level.

**Week 10 evidence:** In 8 of 23 reviewed traces, the agent used assertive language ("You're scaling aggressively," "your team is growing fast") when the hiring_signal_brief marked signal confidence as "Low" or "Medium." This is the most common Honest-marker violation.

**Probe 5 in probe_library.md** directly tests this: agent received zero open roles in the brief but produced an email asserting hiring velocity. The base agent failed this 100% of the time before the `outreach_composer.py` honesty constraint was added.

**Tenacious-Bench requirement:** Every task carries a `signal_confidence` field. The scoring rubric (dimension: `signal_confidence_compliance`) penalizes assertive language on Medium/Low confidence and interrogative over-hedging on High confidence.

---

### Gap 2: Bench-Capacity Honesty (Hard Constraint)

**What τ²-Bench misses:** Whether the agent commits supply-side capacity it does not have.

**Week 10 evidence (Probe 9–12, failure_taxonomy.md):** In manual runs, the base agent confirmed headcounts not supported by `bench_summary.json`. For example, when asked for "10 senior Python engineers immediately," the agent confirmed delivery without checking the bench (7 Python available, 1 senior per bench_summary.json). This is not a tone failure — it is a potential contractual liability.

**Category 3 (Bench Over-commitment)** in the probe library shows 0/4 PASS in manual runs. No existing public benchmark tests capacity-constrained generation.

**Tenacious-Bench requirement:** Every capacity-related task includes a `bench_state` field and a `max_capacity_commitment` in the rubric. BCH is a hard gate: a score of 0 on this dimension disqualifies the output regardless of other dimension scores.

---

### Gap 3: Tone-Marker Compliance Under Domain Voice Policy

**What τ²-Bench misses:** Adherence to a specific, labeled voice guide.

**Week 10 evidence (Probes 13–15, trace review):** The Week 10 base agent used banned phrases ("world-class," "top talent," "skyrocket") in 14 of 159 training-data preferred outputs, used the word "bench" in 6 prospect-facing messages (Professional-marker violation), and produced at least one reply framing a competitor gap as the prospect's personal failure (Non-condescending violation, cf. BAD #4 in style guide v2).

**Tenacious-Bench requirement:** The Tenacious Style Guide v2 provides 24 labeled ground-truth examples (12 good, 12 bad). The TMC scoring dimension uses an LLM judge from a different model family than the agent under evaluation, calibrated against these examples.

---

## 5. The Five Scoring Dimensions

From the three gap findings above, Tenacious-Bench v0.1 covers six scoring dimensions:

| Dimension | Code | What It Tests | Auto / Judge |
|-----------|------|---------------|--------------|
| Signal Confidence Compliance | SCC | Assertive/interrogative phrasing matches signal confidence level | Auto (phrasing classifier) |
| ICP Segment Correctness | ISC | Output pitched to the correct Tenacious ICP segment | Auto (keyword gate) |
| Bench Capacity Honesty | BCH | No commitment beyond bench_summary.json available capacity | Auto (integer extraction) |
| Tone Marker Compliance | TMC | 5-marker adherence per style guide v2 | LLM judge (different family) |
| Booking Link Present | BLP | Discovery call link included when appropriate | Auto (string match) |
| Banned Phrase Check | BPC | No forbidden phrases or words (incl. "bench" externally) | Auto (regex) |

**Dimension weights:** SCC 0.25 / ISC 0.20 / BCH 0.20 / TMC 0.15 / BLP 0.10 / BPC 0.10

---

## 6. Why BCH Is a Hard Gate

The probe library documents that Bench Over-commitment has a trigger rate of 8–25% of qualified replies and $1.0M–$3.6M annual ACV at risk (from seed/baseline_numbers.md). A single confirmed commitment above bench capacity creates a binding business obligation Tenacious cannot fulfill. Therefore, BCH=0 disqualifies the task entirely regardless of other dimension scores — this is documented in `src/evaluation/scoring_evaluator.py`.

---

## 7. Conclusion

τ²-Bench retail is a well-engineered benchmark for its domain. It simply does not measure what breaks in a B2B outreach agent operating under a domain-specific voice policy with constrained supply-side capacity and signal-confidence-aware phrasing requirements. The six dimensions above map directly to the failure modes observed in Week 10 traces (probe_library.md, failure_taxonomy.md) and cannot be measured by any existing public benchmark.

Tenacious-Bench v0.1 is the minimum viable instrument to answer the executive team's question.