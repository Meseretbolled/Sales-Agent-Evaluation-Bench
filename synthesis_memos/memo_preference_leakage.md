---
title: Synthesis Memo — Preference Leakage
paper: "Preference Leakage: A Contamination Problem in LLM-as-a-Judge (Li et al., 2025)"
author: Meseret Bolled
path: B (DPO)
---

## Core Argument

Li et al. identify a systematic bias they call **preference leakage**: when the same LLM family generates training preference pairs AND is later used as a judge to evaluate outputs, the judge inflates scores for outputs that stylistically resemble its own generation patterns. The effect survives model-version changes within a family. The recommended mitigation is to use **completely different model families** for generation versus judging — e.g., generate chosen/rejected with Mistral, judge with Llama.

## Where I Disagree — Partially

Li et al. treat preference leakage as a binary: same family = contaminated, different family = clean. This overstates the problem for benchmarks where the majority of the score is **not LLM-judged**.

For Tenacious-Bench, our `scoring_evaluator.py` assigns weights as follows:
- Banned-phrase check: 25% (regex, zero LLM involvement)
- Hiring-signal grounding: 25% (string match against `hiring_signal_brief` fields)
- Calendar link presence: 15% (regex)
- No over-commitment: 15% (keyword list)
- Tone score from LLM judge: 20%

Only 20% of the score flows through an LLM judge. Preference leakage on 20% of the signal, while real, is bounded. Our ablation (Delta A +0.1904) is driven primarily by improvement on the mechanical checks — the trained model stopped using banned phrases and started referencing the brief — not by the tone score.

That said, Li et al. are **correct** that we created a contamination risk. Our preference pairs were generated using Qwen3-based rewrites for the chosen examples, and our judge uses a Qwen3-family call for tone scoring. This is preference leakage by their definition.

## How I Applied This

Two mitigations applied:
1. **Score decomposition**: the per-task `scoring` field in `held_out_traces.jsonl` records each sub-score separately. A reviewer can inspect tone scores independently and discount them if leakage is suspected.
2. **24-hour re-label agreement**: the 0.91 Cohen's Kappa in `inter_rater_agreement.md` was computed on human labels, not model labels — so the agreement signal is leakage-free even if individual scores are not.

The mitigation I did **not** implement — and should in a production version — is Li et al.'s recommendation to use a **different model family** for chosen-rewrite generation vs. the judge. Given our $10 compute budget and a 20% judge weight, the cost of the mitigation exceeded the risk. I document this as a limitation in `datasheet.md` §7.

**Word count: 378**
