# Methodology Rationale — Tenacious-Bench v0.1 (Act III)

**Author:** Meseret Bolled
**Path:** B — Direct Preference Optimization (DPO)
**Date:** Week 11, May 2026

---

## 1. Why Path B Over Paths A and C

The Week 10 trace analysis produced a clear failure signal: the Conversion Engine
generated fluent, grammatically correct outreach — but violated Tenacious policy
on **preference-ranked dimensions**. Specifically:

- Trace `9f1bceea`: model referenced a prospect's recent layoffs as a buying
  signal, which Tenacious's style guide explicitly prohibits.
- Trace `3bb05cae`: model mirrored aggressive prospect language, producing
  non-Tenacious tone even when the content was factually accurate.
- Trace `daa216a6`: model misclassified a Series B cash-preservation signal as
  a budget expansion signal, leading to over-commitment on delivery scope.

These are not generation failures (Path A) or step-level reasoning errors
(Path C). They are **preference alignment failures**: the base model knows how
to write an email; it just ranks the wrong outputs higher. DPO is the correct
treatment because it directly optimizes the log-probability ratio between
Tenacious-compliant (chosen) and non-compliant (rejected) outputs without
requiring step annotations or a full SFT phase.

Supporting evidence from Rafailov et al. (§3.2, NeurIPS 2023): DPO's policy
gradient objective converges to the same solution as RLHF under the Bradley-Terry
preference model, but without the instability of a separate reward model.
At 1.7B parameters and 159 training pairs, a reward model would be underfit;
DPO's closed-form loss is the right choice at this data scale.

---

## 2. Why DPO Over SimPO / ORPO

SimPO (Meng et al., NeurIPS 2024) and ORPO (Hong et al., EMNLP 2024) both
eliminate the reference model, claiming memory savings. On a T4 with 16 GB VRAM
and Qwen3-1.7B at fp16 (3.55 GB loaded), the reference model in DPO with
`ref_model=None` adds ~0.3 GB via gradient-checkpointed frozen weights — within
tolerance. The memory argument does not apply at our scale.

SimPO introduces a margin hyperparameter γ with no established default for
short-text B2B domain tasks. Ablating γ over three values would require three
full T4 sessions. With a single free Colab session and a 60-step training budget,
DPO's β=0.1 default (validated across multiple RLHF studies) is the safer choice.

ORPO combines SFT and preference loss in one pass — valuable when the base model
needs generation correction. Qwen3-1.7B already generates grammatically correct,
contextually appropriate email. The failure is compliance, not generation. A
pure preference signal (DPO) is more targeted.

---

## 3. Preference Pair Construction

Chosen examples come from two sources:
1. Week 10 hand-reviewed passing traces — 42 pairs drawn directly from
   `conversion-engine/eval/trace_log.jsonl` (real distributional behavior).
2. Dev-tier model rewrites of failing traces — DeepSeek-Chat rewrites that
   pass the `scoring_evaluator.py` threshold (score ≥ 0.80).

Rejected examples come from:
1. Unmodified failing traces — probe-triggered violations confirmed by evaluator.
2. Programmatic corruptions — banned phrases injected, signal references removed,
   over-commitment phrases added. These are deterministic and not model-generated,
   which limits preference leakage (Li et al., 2025).

Preference leakage prevention: chosen rewrites used DeepSeek-Chat (Mixture-of-Experts
family); the judge for tone scoring uses Qwen3 (dense transformer family). Different
architecture families reduce the stylistic overlap that Li et al. identify as the
primary leakage mechanism.

---

## 4. Held-Out Protocol

The 52-task held-out partition was sealed before any training data was constructed.
Three contamination checks ran before sealing:
- N-gram overlap (8-gram): 0 collisions with training partition
- TF-IDF cosine similarity: max similarity 0.31 (threshold 0.70)
- Time-shift: held-out tasks use company signals from a different synthetic
  date window than training tasks

No training example was modified after the held-out was sealed.

---

## 5. Ablation Design

Two conditions evaluated on all 52 held-out tasks:
- **Base**: `unsloth/Qwen3-1.7B` with no adapter, greedy decoding
- **Trained**: same model with DPO LoRA adapter, greedy decoding

Identical prompts, identical scoring evaluator, same random seed (42).
Bootstrap CI computed over 10,000 resamples of per-task score differences.

**Result:** Delta A = +0.1904, 95% CI [0.1115, 0.2788], p = 0.0000.
Zero of 10,000 bootstrap samples produced a mean improvement ≤ 0.

---

*Word count: 598*
