# MEMORANDUM

**TO:** CEO and CFO, Tenacious Intelligence Corporation  
**FROM:** Meseret Bolled, AI Engineering  
**DATE:** May 2, 2026  
**SUBJECT:** Deployment Recommendation — DPO-Tuned Sales Outreach Agent (Tenacious-Qwen-DPO-Stable)

---

## PAGE 1: THE DECISION

### Three-Sentence Executive Summary

We built Tenacious-Bench v0.1, a 238-task evaluation benchmark measuring the three failure modes in our Week 10 sales agent that no public benchmark captures: signal-confidence miscalibration, bench capacity over-commitment, and tone policy drift. We trained a LoRA adapter (Tenacious-Qwen-DPO-Stable) on 159 preference pairs using Direct Preference Optimization. On the sealed 52-task held-out partition, the trained adapter scored 0.82 vs the base model's 0.24 — a **+0.58 absolute improvement** with a 95% confidence interval of [0.497, 0.661] (paired bootstrap, p<0.001).

### Headline Lift — Delta A (Trained vs. Base on Tenacious-Bench Held-Out)

| Metric | Base (Qwen 2.5-1.5B) | Trained (DPO Adapter) | Δ |
|---|---|---|---|
| Weighted rubric score | 0.24 | **0.82** | **+0.58** (95% CI: [0.497, 0.661]) |
| Task pass rate | 23.1% | **82.7%** | **+59.6pp** |
| Capacity over-commitment rate (BCH) | 53.8% | **5.8%** | **-48pp** |
| Banned phrase violation rate | 38.5% | **3.8%** | **-34.7pp** |
| Signal phrasing errors | 42.3% | **7.7%** | **-34.6pp** |

### Delta B — Trained vs. Prompt-Engineered (Honest Report)

A carefully crafted 2,000-word system-prompt version of the same backbone scored **0.71** on the held-out partition. The trained adapter scored **0.82** — a **+0.11 (11pp) advantage** for training over prompt engineering (95% CI: [0.035, 0.182], p=0.004). The prompt-engineered system failed 8/52 tasks where the style guide was silently dropped due to prompt truncation at `max_prompt_length=512`. The trained adapter internalizes the policy into weights and is truncation-immune. **Both Delta A and Delta B are positive and statistically significant.**

### Cost Per Task — With vs. Without Trained Component

| | Base + Prompt Engineering | Trained Adapter |
|---|---|---|
| Avg. inference latency | 310 ms | 318 ms (+2.6%) |
| Prompt tokens (avg.) | ~2,300 (includes system prompt) | ~1,950 (style guide internalized) |
| Token cost per email | 1.0× (baseline) | **0.85× (15% reduction)** |
| Tone judge cost (held-out only) | $0.029/task | $0.029/task |

**Verdict: Deploy.** The trained adapter is Pareto-dominant — +59.6pp task pass rate for a 15% token cost reduction and negligible latency increase.

### Recommendation

**Recommendation: Deploy with a 30-day monitored rollout.** Replace the general prompt-engineered assistant with the Tenacious-Qwen-DPO-Stable adapter for all automated B2B outreach. Monitor BCH (capacity commitment) violations and tone judge scores daily for the first 30 days before full production rollout. The kill-switch trigger is defined on Page 2.

---

## PAGE 2: THE SKEPTIC'S APPENDIX

### Four Failure Modes Tenacious-Bench v0.1 Does Not Yet Capture

**1. Multi-turn conversation coherence.** Every task in v0.1 is a single-output evaluation. The adapter has not been tested on 3–5 turn prospect conversations where signal information accumulates and may conflict across turns. A prospect who mentions a layoff in turn 1 and denies it in turn 3 is not tested.

**2. Timezone-aware scheduling.** Probes 22–24 from the Week 10 probe library document scheduling edge cases (prospect in APAC requesting overlap with US-EST hours that exceeds the 3-hour minimum). These are not in v0.1. The adapter may hallucinate timezone commitments.

**3. GDPR/CCPA routing for EU prospects.** Outreach to EU-domiciled CTOs may require consent signaling before signal-grounded assertions. The current rubric does not include a GDPR compliance dimension. Add in v0.2 before expanding to EU pipeline.

**4. Rapidly-stale signals.** The benchmark cut-off is April 1, 2026. Signal briefs referencing events from this window are already 30+ days old at evaluation time. Production use will encounter signals from hours ago and from 6+ months ago — the rubric currently does not stratify by signal recency and cannot penalize stale signal assertion.

### Public-Signal Lossiness in Ground Truth

Layoff counts from layoffs.fyi are frequently understated by 20–40% at the time of publication and are corrected retroactively. Signal briefs built from Day-1 layoffs.fyi data will undercount the true layoff. This means the BCH dimension cannot flag cases where the agent correctly states a layoff count that was, in fact, wrong at the time the brief was generated. Ground truth here is the brief content, not the underlying event — a known limitation.

### One Honest Unresolved Failure

Task TB-HA-H-1001 (Adobe, 20 Python engineers requested, 7 available): the adapter avoids false commitment but fails to state the specific available count. Instead of "we have 7 Python engineers available; a 20-engineer ramp is a 60-day engagement, here is our delivery lead's calendar," the model produces "let's discuss specifics on a call." This is a hedge, not a routing — it fails the SCC dimension on one rubric sub-check. Root cause: the DPO training data underrepresents large-delta capacity requests. Fix: add 15 training pairs with explicit available-count citation before v0.2 deployment.

### Kill-Switch Trigger

The adapter is automatically reverted to the prompt-engineered fallback if **any** of the following conditions occurs in a rolling 24-hour production window:

1. **BCH violation rate exceeds 2%** — any confirmed capacity over-commitment in production logs (defined as: agent text commits a specific engineer count not supported by that day's bench_summary.json snapshot).
2. **Tone judge score average falls below 3.5/5.0** on the hourly 10-sample spot-check via the Qwen judge (different model family from deployed adapter).
3. **Banned phrase trigger** — any banned phrase from the Tenacious Style Guide v2 appears in a prospect-facing message (detected via the production banned-phrase regex in `src/evaluation/scoring_evaluator.py`).
4. **Model card score degradation** — if the meseretbolled/Tenacious-Qwen-DPO-Stable model card's public evaluation section shows a community-reported regression below 0.70 weighted score on the dev partition.

Human review is required before re-enabling the adapter after any kill-switch trigger.

---

*Evidence for all numeric claims maps to `evidence_graph.json` in the public GitHub repository.*

*Signed,*  
Meseret Bolled  
AI Engineering, Tenacious Project  
Week 11 TRP1 Challenge
