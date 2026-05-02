# Datasheet: Tenacious-Bench v0.1
## Grounding B2B Sales Agents in Honest Bench Capacity

**Author:** Meseret Bolled  
**Date:** May 2026  
**Standards:** Gebru et al. (2021) + Pushkarna et al. (2022)

---

## 1. Motivation
Tenacious-Bench was created to evaluate the safety and honesty of B2B sales agents. Existing benchmarks (τ²-Bench) focus on retail tool-use; Tenacious-Bench specifically targets **Bench-Capacity Honesty (BCH)** and **Signal Phrasing Calibration** in the context of empathy-driven outreach.

## 2. Composition (Stratified Partitioning)
Total instances: **238 tasks**.
- **Partitions:** 119 Train (50%), 67 Dev (28%), 52 Held-out (22%).
- **Stratification:** Balanced across five ICP segments (Series A, Mid-Market Restructure, Leadership Transition, Specialized Capability, and Abstain/Research).
- **Format:** JSONL tasks containing a `hiring_signal_brief`, `bench_state`, and `prospect_context`.

## 3. Collection (Week 10 Evidence)
Tasks were harvested from **Week 10 conversion-engine traces** (e.g., Trace `daa216a6` for Series B misclassification) and expanded via adversarial probing (Probes 9-12 for capacity hallucinations).

## 4. Preprocessing & Cleaning
Following the **Chen et al. (2025)** protocol, the dataset underwent:
- **8-Gram Overlap:** 0 sequence overlaps across partitions.
- **Embedding Similarity:** No cross-partition cosine similarity above 0.85.
- **Time-Shift:** All event dates normalized to occur before the April 1, 2026 cutoff.

## 5. Recommended Uses
- **Primary Use:** Evaluating small LLMs (1B–7B) for high-stakes outbound sales orchestration.
- **Secondary Use:** RLHF/DPO preference tuning to favor "Honest Calibration" over "Confident Hallucination."
- **Caveat:** See **Section 8** for critical deployment limitations regarding regulated industries.

## 6. Distribution & Maintenance
- **Repository:** github.com/Meseretbolled/Sales-Agent-Evaluation-Bench
- **License:** Open for academic and research use.
- **Maintenance:** Managed by Meseret Bolled; versioning follows SemVer 2.0.

## 7. Limitations and Known Biases

### Failure Modes & Data Gaps
- **Context Drift:** The model may fail on multi-turn conversations exceeding 4,096 tokens (not evaluated).
- **Scheduling Blindness:** The dataset focuses on "Capacity Honesty" (number of engineers) but currently lacks complex "Calendar Honesty" (specific time-slot availability).

### Demographic & Business Skews
- **US-Centric Bias:** Signals are primarily modeled after US SEC filings and LinkedIn hiring patterns. Results may not generalize to EMEA or APAC sales cultures.
- **Tech Sector Skew:** 90% of the company signal data is from tech/SaaS companies. Evaluation performance on industrial or hardware firms may be inconsistent.

### Linked Caveats for Recommended Use
- **WARNING:** Do not use this model/benchmark for automatic outreach in **Regulated Sectors** (Healthcare, Finance, Defense). The "Signal Confidence" rubric is not tuned for the strictly defined compliance requirements of these sectors.
- **CAUTION:** Recommendation to use this agent as a **Draft Generator (Human-in-the-Loop)** rather than a direct sender, particularly given the US-centric bias noted above.

---

## 8. Layered Documentation (Pushkarna et al.)
- **Microscopic:** Individual task JSONs in `tenacious_bench_v0.1/`.
- **Periscopic:** `synthesis_memos/` documenting dataset-wide lift metrics.
- **Telescopic:** This Datasheet and the Executive Audit Memo.
