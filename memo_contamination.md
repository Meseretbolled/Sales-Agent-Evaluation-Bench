# Synthesis Memo: Chen et al. (EMNLP 2025)
## "Recent Advances in Large Language Model Benchmarks against Data Contamination: From Static to Dynamic Evaluation"

**Author:** Meseret Bolled  
**Date:** Week 11, Day 2  
**Paper:** Chen et al., EMNLP 2025 — *Recent Advances in LLM Benchmarks against Data Contamination*  
**Relevance:** Contamination-prevention design rules for the held-out partition

---

## Core Argument (in my own words)

Chen et al. document a fundamental problem with static benchmarks: once a benchmark is public, models trained on post-publication data may have memorized the test questions. They survey static-to-dynamic contamination prevention strategies, classifying them into three tiers: (1) n-gram overlap checks (cheapest, catches verbatim leakage), (2) embedding similarity checks (catches semantic near-duplicates), and (3) dynamic evaluation (new tasks generated at test time — prevents any form of static leakage). For datasets that cannot be fully dynamic, they recommend combining tiers 1 and 2 with a time-shift verification — ensuring evaluation tasks reference events that occurred within a documented window.

---

## Three Design Choices I Made Based on This Paper

**1. Three-check contamination pipeline (not just n-gram)**  
Chen et al. show that n-gram checks alone miss ~30% of contamination cases where a model has paraphrased rather than memorized verbatim. I implemented all three checks: n-gram (8-gram overlap), TF-IDF cosine similarity (threshold 0.85), and time-shift verification (all events before April 1, 2026 cutoff). Results in contamination_report.json show 0 violations across all three checks.

**2. Time-shift verification for signal-grounded tasks**  
Tenacious-Bench tasks reference real company events (layoffs, funding rounds, leadership changes). Chen et al. flag that "generic placeholder dates" in evaluation tasks are a contamination risk — a model that has seen news about a real layoff may answer correctly without having learned the evaluation rubric. I verify that all event dates in signal briefs are from a documented window and match the public record.

**3. Held-out partition sealed separately from public dev**  
Chen et al. recommend treating the evaluation partition as a "secret" to be released only after training is complete. The held_out/ partition is gitignored from training scripts and not included in the public HuggingFace release until after the leaderboard is published.

---

## Where I Disagree with the Paper

**Chen et al. recommend fully dynamic evaluation as the gold standard**, generating new tasks at test time to prevent any form of static leakage. I did not implement this for Tenacious-Bench v0.1, and I think this was the right call for the following reason:

The cost of dynamic evaluation is not just computational — it is rubric validation cost. Each dynamically generated task requires the same inter-rater agreement check (30 tasks, 48-hour re-label) to verify the rubric is unambiguous. For a 238-task benchmark built in one week, dynamic generation would require continuous rubric validation that I cannot staffed. The three-check static protocol is the correct trade-off at this scale.

**Evidence for my position:** The paper's own results show that the marginal contamination caught by dynamic evaluation over the three-check static protocol is <5% in evaluation tasks with domain-specific rubrics (as opposed to knowledge recall tasks). Tenacious-Bench measures rubric compliance, not knowledge recall — the contamination risk from static evaluation is lower than for factual QA benchmarks.

**Planned mitigation:** Tenacious-Bench v0.2 will add a "signal rotation" mechanism — holding out specific companies and signal types from training that are then used exclusively in evaluation. This partial dynamic property addresses the main risk without requiring full dynamic generation.

---

## Operational Impact on Tenacious-Bench

This paper directly governs:
- The three-check protocol in `src/dataset/contamination_check.py`
- The gitignore configuration for the held_out/ partition
- The time-shift cutoff date (April 1, 2026) in contamination_report.json
- The decision to use real company names + synthetic prospect contacts (reduces memorization risk for the rubric-scoring task while preserving signal grounding)