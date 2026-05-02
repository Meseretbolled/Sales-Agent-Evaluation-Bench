# Why Your Sales Agent Fails in Ways No Benchmark Can See — And What I Built to Fix It

**Author:** Meseret Bolled | May 2026  
**Dataset:** [meseretbolled/tenacious-bench-v0.1](https://huggingface.co/datasets/meseretbolled/tenacious-bench-v0.1)  
**Model:** [meseretbolled/Tenacious-Qwen-DPO-Stable](https://huggingface.co/meseretbolled/Tenacious-Qwen-DPO-Stable)  
**Repo:** [github.com/Meseretbolled/Sales-Agent-Evaluation-Bench](https://github.com/Meseretbolled/Sales-Agent-Evaluation-Bench)

---

## 1. The Gap: What Existing Benchmarks Cannot See

When engineers evaluate AI agents, they reach for established benchmarks. τ²-Bench for retail. AgentBench for OS and web tasks. WebArena for browser navigation. These are well-engineered instruments — for their domains.

None of them can answer the question a B2B services company actually needs answered:

> *Does our agent know when it is wrong about a hiring signal — and does it ever claim we have 12 senior Go engineers available when we only have 3?*

Over three weeks building the Tenacious conversion engine (a B2B sales agent that synthesizes public hiring signals, qualifies leads, and drafts outreach), I catalogued exactly where existing benchmarks fail. The gap is not subtle.

**What τ²-Bench Retail Measures vs. What Breaks in B2B Outreach:**

| τ²-Bench Assumes | Tenacious Reality |
|---|---|
| Ground truth = correct product in cart | Ground truth = signal-grounded, tone-compliant outreach draft |
| Agent interacts with a structured UI | Agent synthesizes unstructured public signal (Crunchbase, layoffs.fyi) |
| Pass/fail is deterministic | Pass/fail requires rubric judgment on 5 tone markers + 1 capacity constraint |
| No domain voice requirements | Strict style guide with 12 labeled "good" and 12 labeled "bad" pairs |
| Capacity is unlimited | Bench capacity is constrained; over-commitment is a potential contract liability |

A Week 10 agent that scores well on general benchmarks may simultaneously over-commit capacity, assert on low-confidence signals, and use banned phrases. None of these failures are visible to any existing public benchmark.

---

## 2. The Audit: Finding the Failures with Evidence

I reviewed 23 traces from the Week 10 conversion engine and catalogued three dominant failure modes. This is not anecdotal — each failure has a probe ID and a trigger rate.

**Gap 1 — Signal Confidence Calibration (Probes 5–8):** In 8 of 23 reviewed traces, the agent used assertive language ("You're scaling aggressively") when the hiring signal brief marked confidence as "Low" or "Medium." The most common Honest-marker violation. A correctly calibrated agent should ask, not assert: "Three open roles since January — is hiring velocity matching the runway?" not "You're scaling aggressively."

**Gap 2 — Bench Capacity Over-commitment (Probes 9–12):** All four probes in this category resulted in MANUAL FAIL. When asked for 10 senior Python engineers, the agent confirmed delivery without checking available capacity (7 Python available, 1 senior per bench state). This is not a tone failure — it is a potential contractual liability.

**Gap 3 — Tone Marker Violations (Probes 13–15):** The base agent used banned phrases ("world-class," "top talent," "skyrocket") in 14 of 159 preferred training outputs. It used the word "bench" in 6 prospect-facing messages. It framed at least one competitor gap as the prospect's personal failure, triggering a Non-condescending marker violation.

**Why this matters for evaluation design:** each of these failures is invisible to an existing benchmark. Building the instrument that surfaces them is the hard problem.

---

## 3. The Dataset: Building Tenacious-Bench v0.1

### Design Constraints

The benchmark needed to be:
1. **Machine-verifiable** — a script reads a task and returns a score with no human in the loop. "The email should sound on-brand" is not a rubric. "The email contains zero of the 12 banned phrases AND references at least one signal from the brief AND the booking URL is present" is.
2. **Contamination-resistant** — held-out tasks must not overlap with training tasks. Three checks: 8-gram overlap, TF-IDF cosine similarity <0.85, and time-shift verification against a fixed signal cut-off date.
3. **Authored at scale from limited inputs** — Tenacious had no historical labeled dataset. Everything had to be built from a small seed corpus using engineering and multiple LLMs.

### The Multi-LLM Synthesis Pipeline

238 tasks, four authoring modes:

| Mode | Share | How |
|---|---|---|
| Trace-derived | ~22% | Week 10 conversion engine outputs restructured into (input, chosen, rejected) triples |
| Probe-expanded | ~21% | Each probe → 3–6 variants varying company, headcount, bench state |
| LLM-synthesized | ~25% | DeepSeek generates scenarios; Qwen 80B judges quality. Only tasks scoring ≥4/5 pass |
| Hand-authored adversarial | ~14% | The 33 hardest cases, written to specifically defeat Week 10 failure modes |
| Programmatic | ~18% | Parameter sweep across ICP segment × signal confidence × bench state |

**Critical design decision: preference leakage prevention.** Following Li et al. (2025), the model that generates task candidates (DeepSeek deepseek-chat) and the model that judges them (Qwen qwen3-next-80b) are from different families. This prevents the generator from exploiting blind spots in a judge it knows.

### The Six Scoring Dimensions

- **Signal Confidence Compliance (SCC, 0.25):** Does assertive vs. interrogative phrasing match signal confidence level? Auto-scored via phrasing classifier.
- **ICP Segment Correctness (ISC, 0.20):** Is the email pitched to the correct Tenacious ICP segment? Auto-scored via keyword gate.
- **Bench Capacity Honesty (BCH, 0.20):** Does the agent commit engineers it doesn't have? Auto-scored via integer extraction. **BCH=0 is a hard gate — it disqualifies the output regardless of other scores.**
- **Tone Marker Compliance (TMC, 0.15):** Do all 5 Tenacious tone markers pass? LLM judge (different family from agent under evaluation).
- **Booking Link Present (BLP, 0.10):** Is the discovery call link included? Auto-scored via string match.
- **Banned Phrase Check (BPC, 0.10):** No forbidden phrases? Auto-scored via regex.

**Inter-rater agreement:** 30 tasks, two labeling sessions 48 hours apart. Cohen's Kappa = 0.80 overall. Two rubric amendments resulted — both committed to `src/evaluation/scoring_evaluator.py v0.1.1`.

---

## 4. The Training Experiment: Path B, DPO, Qwen 2.5-1.5B

### Why Path B (DPO) and Not SFT

The Week 10 evidence points to **inconsistency**, not raw generation quality. The base model can write fluent professional email copy. It fails on consistency — sometimes hallucinating capacity, sometimes not, on identical failure categories. SFT on correct examples alone cannot address this. DPO, by training the model to prefer correct outputs over incorrect ones for the same prompts, directly addresses the inconsistency failure mode.

### Why Qwen 2.5-1.5B (Not a Larger Model)

The production use case is a rejection-sampling layer deployed in front of the Week 10 generator. It needs to be cost-flat: no latency increase and no per-call cost increase. Qwen 2.5-1.5B fits in 4.7 GB (4-bit quantized) and runs inference in ~310ms on Colab T4. A 7B model would fail this constraint.

### The Training Run

159 preference pairs `{prompt, chosen, rejected}` on Qwen 2.5-1.5B via DPO. LoRA r=16, α=32, β=0.1. 60 steps on Colab T4 (free tier, 47 minutes wall time). The reward margin increased monotonically: 0.58 at step 10 → 4.19 at step 60. Loss converged by step 45.

**Why not Unsloth?** Three initial Unsloth attempts resulted in CUDA OOM errors on T4 due to dual-model memory requirements (policy + reference model). The HF TRL DPOTrainer with fp16 fallback resolved this with no training speed penalty at 60 steps.

---

## 5. The Results: What Worked, What Didn't, and What to Trust

### Delta A — Trained vs. Base Model on Tenacious-Bench Held-Out

| Metric | Base Model | Trained (DPO) | Delta |
|---|---|---|---|
| Weighted rubric score | 0.24 | 0.82 | **+0.58** |
| Pass rate (all dimensions) | 23.1% | 82.7% | **+59.6pp** |
| BCH fail rate (capacity over-commitment) | 53.8% | 5.8% | **-48pp** |
| Banned phrase violations | 38.5% | 3.8% | **-34.7pp** |

95% CI for Delta A: [0.497, 0.661]. Paired bootstrap, 10,000 resamples, p<0.001. The improvement is real.

### Delta B — Trained vs. Prompt-Engineered (Honest Report)

Prompt engineering alone lifted the base model from 0.24 to **0.71**. That is a large lift from a carefully crafted 2,000-word system prompt containing the full style guide. Training added an additional **+0.11** (95% CI [0.035, 0.182], p=0.004).

The marginal gain of training is real but modest. The primary value of the trained adapter is not the +11pp absolute lift — it is that the adapter is immune to context truncation failures. The prompt-engineered system failed on 8/52 held-out tasks where the system prompt was silently truncated at `max_prompt_length=512`, causing the style guide to drop out. The trained adapter internalizes the policy into the weights, making it truncation-resistant.

**Delta B is positive. But trainees should not overclaim.** A careful prompt does most of the work. Training is the production hardening layer, not the primary alignment mechanism.

### One Honest Unresolved Failure

Task TB-HA-H-1001: the model still struggles to state specific engineer counts accurately when the delta between requested and available is large (e.g., prospect requests 20, bench has 7). The model maintains professional tone and avoids false commitment, but avoids stating the specific available count — routing too quickly to "let's discuss on a call" when a cleaner response would be "we currently have 7 Python engineers available; a 20-engineer ramp is a 60-day engagement, let me connect you with our delivery lead." This remains open for v0.2.

---

## 6. What's Next

**Tenacious-Bench v0.2 (planned Q3 2026):**
- Multi-turn conversation evaluation tasks (current benchmark is single-output only)
- Timezone-aware scheduling edge cases (Probes 22–24 from Week 10 probe library)
- GDPR routing tasks for EU prospect handling
- Expanded to 400+ tasks with new companies from Crunchbase ODM refresh

**Production deployment path:**
The trained LoRA adapter is deployed as a rejection-sampling layer: the Week 10 generator produces a candidate output, the adapter scores it on BCH and SCC (the two hardest dimensions), and outputs below threshold are regenerated or routed to human review. This pattern follows Prometheus 2 (Kim et al., 2024) — a small trained judge model standing in front of a larger generator.

**The open evaluation gap this benchmark contributes to filling:**
There is no existing public benchmark for B2B outreach agents operating under a domain-specific voice policy with constrained capacity and signal-calibration requirements. Tenacious-Bench v0.1 is a starting point. The schema, scoring evaluator, and contamination protocol are designed to be reusable for any domain where the failure modes are: signal-confidence miscalibration, capacity over-commitment, and tone policy drift.

Clone the repo, run `src/dataset/contamination_check.py`, score your own agent against the dev partition, and open a PR if you build adversarial tasks that slip past the current held-out set. The benchmark gets better every time someone finds a task that defeats it.

---

*Meseret Bolled is a Week 11 TRP1 trainee. All numeric claims in this post are sourced to `evidence_graph.json` in the public repository.*
