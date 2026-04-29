# Cost Log — Tenacious-Bench Week 11

**Author:** Meseret Bolled
**Budget:** $10 total per trainee
**Repository:** github.com/Meseretbolled/tenacious-bench

Rule: every API charge logged with timestamp, model, purpose, tokens, and cost.
No eval-tier model (Claude Sonnet 4.6) used before Day 5.

---

## Budget Allocation

| Bucket | Allocation | Purpose |
|---|---|---|
| Dataset authoring | $3-5 | OpenRouter DeepSeek + Qwen3 synthesis and judging |
| Training | $0 | Free on Colab T4 via Unsloth |
| Held-out evaluation | $2-3 | Eval-tier model on sealed slice only |
| Reserve | $1-2 | Bug fixes, re-runs |
| **Total** | **$10** | |

---

## Hard Rules

- No eval-tier model (Claude Sonnet 4.6 / GPT-5) on Days 1-4
- No τ²-Bench retail re-runs — Week 10 score is reused
- All charges logged within 1 hour of incurring
- Generation model and judge model must be different families

---

## Charge Log

### Day 1 — April 28, 2026

| Time (UTC) | Model | Purpose | Input Tokens | Output Tokens | Cost (USD) |
|---|---|---|---|---|---|
| 09:00 | — | audit_memo.md — no API call needed | — | — | $0.00 |
| 09:30 | — | schema.json — no API call needed | — | — | $0.00 |
| 10:00 | — | scoring_evaluator.py — no API call needed | — | — | $0.00 |
| **Day 1 Total** | | | | | **$0.00** |

### Day 2 — April 29, 2026

| Time (UTC) | Model | Purpose | Input Tokens | Output Tokens | Cost (USD) |
|---|---|---|---|---|---|
| 08:00 | — | trace_restructurer.py — no API call (local CSV) | — | — | $0.00 |
| 09:00 | — | probe_expander.py — no API call (parametric) | — | — | $0.00 |
| 10:00 | deepseek/deepseek-chat | synthesizer.py — task generation batch 1 (20 tasks) | ~40,000 | ~20,000 | ~$0.008 |
| 10:30 | qwen/qwen3-next-80b-a3b-instruct | synthesizer.py — judge batch 1 (20 tasks) | ~20,000 | ~2,000 | ~$0.004 |
| 11:00 | deepseek/deepseek-chat | synthesizer.py — task generation batch 2 (20 tasks) | ~40,000 | ~20,000 | ~$0.008 |
| 11:30 | qwen/qwen3-next-80b-a3b-instruct | synthesizer.py — judge batch 2 (20 tasks) | ~20,000 | ~2,000 | ~$0.004 |
| 12:00 | deepseek/deepseek-chat | synthesizer.py — task generation batch 3 (20 tasks) | ~40,000 | ~20,000 | ~$0.008 |
| 12:30 | qwen/qwen3-next-80b-a3b-instruct | synthesizer.py — judge batch 3 (20 tasks) | ~20,000 | ~2,000 | ~$0.004 |
| **Day 2 Total** | | | | | **~$0.036** |

### Day 3 — April 30, 2026 (planned)

| Time (UTC) | Model | Purpose | Estimated Cost |
|---|---|---|---|
| 09:00 | deepseek/deepseek-chat | synthesizer.py — additional tasks to reach 200+ target | ~$0.015 |
| 09:30 | qwen/qwen3-next-80b-a3b-instruct | synthesizer.py — judge additional tasks | ~$0.008 |
| 10:00 | — | contamination_check.py — no API call (local TF-IDF) | $0.00 |
| 10:30 | — | partitioner.py — no API call | $0.00 |
| **Day 3 Estimate** | | | **~$0.023** |

### Day 4 — May 1, 2026 (planned)

| Time (UTC) | Model | Purpose | Estimated Cost |
|---|---|---|---|
| 09:00 | deepseek/deepseek-chat | Format chosen/rejected pairs for Path B training | ~$0.010 |
| **Day 4 Estimate** | | | **~$0.010** |

### Day 5 — May 2, 2026 (planned — Colab)

| Item | Cost |
|---|---|
| Colab T4 GPU | $0.00 (free tier) |
| Unsloth LoRA training run | $0.00 |
| Model push to HuggingFace | $0.00 |
| **Day 5 Estimate** | **$0.00** |

### Day 6 — May 3, 2026 (planned — held-out evaluation)

| Time (UTC) | Model | Purpose | Estimated Cost |
|---|---|---|---|
| 10:00 | claude-sonnet-4-5 (eval tier) | Tone judge on held_out/ partition (40 tasks × 5 markers) | ~$1.50 |
| 10:30 | — | scoring_evaluator.py — other dimensions (local) | $0.00 |
| **Day 6 Estimate** | | | **~$1.50** |

---

## Running Total

| Day | Actual | Estimated |
|---|---|---|
| Day 1 | $0.00 | — |
| Day 2 | ~$0.036 | — |
| Day 3 | — | ~$0.023 |
| Day 4 | — | ~$0.010 |
| Day 5 | — | $0.00 |
| Day 6 | — | ~$1.50 |
| **Total** | **~$0.036 actual** | **~$1.57 projected** |

**Remaining budget: ~$8.43 of $10.00**

---

## OpenRouter Pricing Reference (April 2026)

| Model | Input (per M tokens) | Output (per M tokens) |
|---|---|---|
| deepseek/deepseek-chat | $0.14 | $0.28 |
| qwen/qwen3-next-80b-a3b-instruct | $0.20 | $0.60 |
| claude-sonnet-4-5 (eval only) | $3.00 | $15.00 |

All costs estimated at listed rates. Actual charges may vary by ±10% due to
token count estimation error.