# Synthesis Memo: Gu et al. (2024–2025)
## "A Survey on LLM-as-a-Judge"

**Author:** Meseret Bolled  
**Date:** Week 11, Day 2  
**Paper:** Gu et al., 2024–2025 (latest revision) — *A Survey on LLM-as-a-Judge*  
**Relevance:** Judge-design reference for the tone-compliance scoring dimension and training-data quality filter

---

## Core Argument (in my own words)

Gu et al. survey the design space of using LLMs as automated evaluators. The key operational findings are: (1) **position bias** — judges reliably prefer the first option presented in pairwise comparisons; (2) **verbosity bias** — judges reliably prefer longer responses; (3) **self-enhancement bias** — a model used to judge outputs similar to its own training distribution gives systematically higher scores; and (4) **calibration** — judge quality varies significantly across evaluation dimensions, with factual accuracy being better calibrated than subjective tone. The paper recommends: using a different model family for judging than for generation, using structured rubrics rather than open-ended scoring, and spot-checking judge calibration against human labels.

---

## Three Design Choices I Made Based on This Paper

**1. Different model family for generation vs. judging**  
Gu et al.'s self-enhancement bias finding is directly relevant: using DeepSeek to generate tasks and Qwen-80B to judge them prevents the judge from preferring outputs that resemble DeepSeek's generation style. This is also the preference leakage prevention required by Li et al. (2025). The constraint is enforced in `src/dataset/synthesizer.py` via `GENERATE_MODEL` and `JUDGE_MODEL` constants.

**2. Structured binary rubric for tone compliance, not open-ended**  
The survey shows that open-ended scoring ("rate this email 1–10") produces lower calibration than structured binary rubrics ("does this email contain a question mark when signal confidence is Low?"). I designed the TMC dimension as 5 binary sub-dimensions (direct/grounded/honest/professional/non_condescending) that the judge scores as pass/fail, not a continuous scale. The LLM judge prompt in `src/evaluation/scoring_evaluator.py` enforces this: "Return ONLY valid JSON in this exact format."

**3. Spot-check calibration against inter-rater labels**  
Gu et al. recommend validating the LLM judge against human labels on a calibration sample. The 30-task inter-rater agreement study (see inter_rater_agreement.md) provides this: human labels on 30 dev tasks were compared against the Qwen judge scores on the same tasks. Where they disagreed, the rubric was revised (two amendments). This is the "judge calibration" step.

---

## Where I Disagree with the Paper

**Gu et al. recommend pairwise comparison over pointwise scoring** for most evaluation scenarios, citing that relative judgments are more reliable than absolute ones. I used pointwise scoring for the TMC dimension (5 binary markers, not pairwise comparison of two outputs).

My reasoning: pairwise comparison requires two candidate outputs per task. For the judge-filter phase of dataset construction (deciding whether a synthesized task is good enough to include), I only have one output to evaluate — the task itself. Pairwise comparison would require generating a second candidate just to enable comparison, which doubles the API cost. At $0.004 per judge batch, this is manageable, but the inter-rater agreement results (Kappa 0.61 for tone_compliance) are good enough that the added cost of pairwise comparison is not justified.

**More importantly:** the binary 5-marker rubric from the Tenacious Style Guide is a better representation of ground truth than a pairwise preference. The style guide says "a draft that fails two or more markers is a brand violation" — this is an absolute threshold, not a relative one. Pointwise scoring against that absolute threshold is semantically correct.

---

## Operational Impact on Tenacious-Bench

This paper directly governs:
- The model rotation policy in `src/dataset/synthesizer.py`
- The structured binary rubric in `TONE_JUDGE_PROMPT` in `src/evaluation/scoring_evaluator.py`
- The calibration approach in `inter_rater_agreement.md`
- The decision to use a cheap judge model (Qwen) for bulk filtering and spot-check with a more capable model for calibration