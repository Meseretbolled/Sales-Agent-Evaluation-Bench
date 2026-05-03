# Cost Log — Tenacious-Bench Week 11

**Author:** Meseret Bolled
**Budget:** $10.00 total
**Repository:** github.com/Meseretbolled/Sales-Agent-Evaluation-Bench

Rule: every API charge logged with timestamp, model, purpose, tokens, and cost.
No eval-tier model used before Day 5 (held-out evaluation only).

---

## Hard Rules

- No eval-tier model on Days 1–4
- No τ²-Bench retail re-runs — Week 10 score reused
- Generation model and judge model must be different families (leakage prevention)

---

## Charge Log

### Day 1 — April 28, 2026 (Actual)

| Time (UTC) | Model | Purpose | Cost |
|------------|-------|---------|------|
| 09:00 | — | audit_memo.md — no API call | $0.00 |
| 09:30 | — | schema.json — no API call | $0.00 |
| 10:00 | — | scoring_evaluator.py — no API call | $0.00 |
| **Day 1 Total** | | | **$0.00** |

### Day 2 — April 29, 2026 (Actual)

| Time (UTC) | Model | Purpose | Input Tokens | Output Tokens | Cost |
|------------|-------|---------|-------------|--------------|------|
| 08:00 | — | trace_restructurer.py — local CSV processing | — | — | $0.00 |
| 09:00 | — | probe_expander.py — parametric, no API | — | — | $0.00 |
| 10:00 | deepseek/deepseek-chat | synthesizer.py — task generation batch 1 (20 tasks) | ~40,000 | ~20,000 | ~$0.008 |
| 10:30 | qwen/qwen3-8b-instruct | synthesizer.py — judge filter batch 1 | ~20,000 | ~2,000 | ~$0.004 |
| 11:00 | deepseek/deepseek-chat | synthesizer.py — task generation batch 2 (20 tasks) | ~40,000 | ~20,000 | ~$0.008 |
| 11:30 | qwen/qwen3-8b-instruct | synthesizer.py — judge filter batch 2 | ~20,000 | ~2,000 | ~$0.004 |
| 12:00 | deepseek/deepseek-chat | synthesizer.py — task generation batch 3 (20 tasks) | ~40,000 | ~20,000 | ~$0.008 |
| 12:30 | qwen/qwen3-8b-instruct | synthesizer.py — judge filter batch 3 | ~20,000 | ~2,000 | ~$0.004 |
| **Day 2 Total** | | | | | **~$0.036** |

### Day 3 — April 30, 2026 (Actual)

| Time (UTC) | Model | Purpose | Input Tokens | Output Tokens | Cost |
|------------|-------|---------|-------------|--------------|------|
| 09:00 | deepseek/deepseek-chat | synthesizer.py — additional tasks to reach 238 target | ~30,000 | ~15,000 | ~$0.010 |
| 09:30 | qwen/qwen3-8b-instruct | Judge filter — additional tasks | ~15,000 | ~1,500 | ~$0.003 |
| 10:00 | — | contamination_check.py — local TF-IDF, no API | — | — | $0.00 |
| 10:30 | — | partitioner.py — local, no API | — | — | $0.00 |
| 11:00 | deepseek/deepseek-chat | DPO pair construction — chosen rewrites (42 pairs) | ~84,000 | ~42,000 | ~$0.018 |
| **Day 3 Total** | | | | | **~$0.031** |

### Day 4 — May 1, 2026 (Actual)

| Time (UTC) | Model | Purpose | Cost |
|------------|-------|---------|------|
| 09:00 | — | Format preferences_train.jsonl + preferences_dev.jsonl — no API | $0.00 |
| 10:00 | — | inter_rater_agreement.md — manual re-label, no API | $0.00 |
| 11:00 | — | methodology_rationale.md — no API | $0.00 |
| **Day 4 Total** | | | **$0.00** |

### Day 5 — May 3, 2026 (Actual — Colab Training)

| Item | Cost |
|------|------|
| Google Colab T4 GPU (free tier) | $0.00 |
| Unsloth DPO training — 60 steps, 11.6 min | $0.00 |
| Model push to HuggingFace | $0.00 |
| **Day 5 Total** | **$0.00** |

### Day 6 — May 3–4, 2026 (Actual — Held-Out Evaluation)

| Item | Cost |
|------|------|
| scoring_evaluator.py on 52 held-out tasks — local rule-based (75% of score) | $0.00 |
| Tone judge (20% of score) — run locally via Qwen3 on Colab T4 | $0.00 |
| Bootstrap CI — local numpy, no API | $0.00 |
| **Day 6 Total** | **$0.00** |

---

## Final Summary

| Day | Actual Spend |
|-----|-------------|
| Day 1 (Apr 28) | $0.00 |
| Day 2 (Apr 29) | ~$0.036 |
| Day 3 (Apr 30) | ~$0.031 |
| Day 4 (May 1) | $0.00 |
| Day 5 (May 3) | $0.00 |
| Day 6 (May 3–4) | $0.00 |
| **Total** | **~$0.067** |

**Budget used: $0.067 of $10.00 (0.67%)**

The held-out evaluation used the local `scoring_evaluator.py` (rule-based checks +
Colab-hosted tone judge) rather than a paid eval-tier API call. This kept evaluation
cost at $0.00. The total week's spend was ~$0.07, entirely on dataset synthesis.

---

## OpenRouter Pricing Reference (April 2026)

| Model | Input (per M tokens) | Output (per M tokens) |
|-------|---------------------|----------------------|
| deepseek/deepseek-chat | $0.14 | $0.28 |
| qwen/qwen3-8b-instruct | $0.06 | $0.18 |
