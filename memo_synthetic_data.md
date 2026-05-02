# Synthesis Memo: Liu et al. (COLM 2024)
## "Best Practices and Lessons Learned on Synthetic Data for Language Models"

**Author:** Meseret Bolled  
**Date:** Week 11, Day 2  
**Paper:** Liu et al., COLM 2024 — *Best Practices and Lessons Learned on Synthetic Data for Language Models*  
**Relevance:** Operational reference for the four dataset-authoring decisions in Acts I–II

---

## Core Argument (in my own words)

Liu et al. argue that synthetic data has moved from a compromise to a first-class strategy for language model training, but only when governed by three properties: **factual grounding** (synthetic examples anchored to verifiable real-world sources), **diversity** (avoiding collapse into repetitive patterns that bias evaluation), and **quality filtering** (using a separate judge to remove low-quality generations before they enter training or evaluation). The paper's most operationally useful finding is that small, high-quality synthetic datasets often outperform large, noisy ones — which directly governs the 238-task scope of Tenacious-Bench rather than attempting 1,000+ tasks.

---

## Five Design Choices I Made Based on This Paper

**1. Multi-LLM routing instead of single-model generation**  
Liu et al. show that single-model self-generation collapses to the model's own biases. I used DeepSeek for task generation and Qwen-80B for judging — different model families — to reduce this collapse. This is directly the "diverse source" recommendation.

**2. Judge-filter threshold ≥4/5 on three dimensions**  
The paper recommends explicit quality thresholds for filtering, not soft acceptance. I set hard thresholds: input_coherence ≥4, ground_truth_verifiability ≥4, rubric_clarity ≥4. Tasks below threshold on any single dimension are discarded.

**3. ~30% hand-authored adversarial tasks**  
Liu et al. note that synthesis pipelines have systematic blind spots — they generate tasks that follow the distribution of their training data, not tasks that specifically defeat a known failure mode. My 14% hand-authored slice (33 tasks) addresses this by writing directly to the failure modes in probe_library.md that the synthesis pipeline missed.

**4. Trace-derived tasks as the highest-fidelity mode**  
Liu et al. recommend grounding synthetic data in real operational data when available. The Week 10 `trace_log.jsonl` is real agent behavior on real prospects — the highest fidelity starting point. I weighted this at ~22% of the dataset (53 tasks) rather than more because the trace corpus is small.

**5. Deduplication before partitioning, not after**  
The paper flags that post-partitioning deduplication can accidentally "deduplicate" evaluation signal by removing near-duplicate tasks that were legitimately split across train and eval. I run contamination checks before stratified partitioning to avoid this.

---

## Where I Disagree with the Paper

**Liu et al. recommend diversity of generation sources as the primary quality signal.** I partially disagree for the Tenacious domain. In our case, the failure modes are highly specific (6 rubric dimensions, each derived from a concrete probe result). Broad diversity in generation sources risks introducing tasks that test failure modes not in the Tenacious failure taxonomy — which dilutes the signal. My approach weights source diversity lower than failure-mode coverage: I prefer 10 high-quality tasks targeting Bench Over-commitment (the $3.6M ACV-at-risk category) over 10 tasks that are generically diverse but only loosely related to observed failures.

**Evidence for my position:** The inter-rater agreement analysis showed that the highest Kappa scores came from the most mechanically constrained dimensions (bench_capacity_honesty: 0.83, banned_phrase_check: 1.00). The lowest Kappa (tone_compliance: 0.61) came from the most open-ended dimension. This supports investing in constrained, failure-mode-specific tasks over diverse open-ended ones.

---

## Operational Impact on Tenacious-Bench

This paper directly governs:
- The four authoring modes and their proportions (Section 2 of datasheet.md)
- The judge-filter calibration in `src/dataset/synthesizer.py`
- The deduplication sequence in `src/dataset/contamination_check.py`
- The decision to cap at 238 tasks rather than scaling to 1,000+