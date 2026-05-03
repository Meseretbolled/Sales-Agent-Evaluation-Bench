# Why Your Sales Agent Fails in Ways No Benchmark Can See — And What I Built to Fix It

**Author:** Meseret Bolled | May 2026
**Model:** [meseretbolled/Tenacious-Qwen3-DPO-v01](https://huggingface.co/meseretbolled/Tenacious-Qwen3-DPO-v01)
**Repo:** [github.com/Meseretbolled/Sales-Agent-Evaluation-Bench](https://github.com/Meseretbolled/Sales-Agent-Evaluation-Bench)

---

## 1. The Gap: What Existing Benchmarks Cannot See

When engineers evaluate AI agents, they reach for established benchmarks. τ²-Bench for retail. AgentBench for OS and web tasks. WebArena for browser navigation. These are well-engineered instruments — for their domains.

None of them can answer the question a B2B services company actually needs answered:

> *Does our agent know when it is wrong about a hiring signal — and does it ever claim we have 12 senior Go engineers available when we only have 3?*

Over three weeks building the Tenacious conversion engine — a B2B sales agent that synthesizes public hiring signals, qualifies leads, and drafts outreach — I catalogued exactly where existing benchmarks fail. The gap is not subtle.

| τ²-Bench Assumes | Tenacious Reality |
|---|---|
| Ground truth = correct product in cart | Ground truth = signal-grounded, tone-compliant outreach draft |
| Agent interacts with a structured UI | Agent synthesizes unstructured public signal (Crunchbase, layoffs.fyi) |
| Pass/fail is deterministic | Pass/fail requires rubric judgment on 5 tone markers + 1 capacity constraint |
| No domain voice requirements | Strict style guide with 12 labeled "good" and 12 labeled "bad" pairs |
| Capacity is unlimited | Bench capacity is constrained; over-commitment is a potential contract liability |

A sales agent that scores well on general benchmarks may simultaneously over-commit capacity, assert on low-confidence signals, and use banned phrases. None of these failures are visible to any existing public benchmark.

---

## 2. The Audit: Finding the Failures with Evidence

I reviewed 149 traces from the Week 10 conversion engine and catalogued three dominant failure modes. Each has a probe ID and a trigger rate from the Week 10 probe library.

**Gap 1 — Signal Confidence Calibration (Probes 5–8):** The agent used assertive language ("You're scaling aggressively") when the hiring signal brief marked confidence as "Low" or "Medium." A correctly calibrated agent asks, not asserts: "Three open roles since January — is hiring velocity matching the runway?"

**Gap 2 — Bench Capacity Over-commitment (Probes 9–12):** All four probes in this category resulted in MANUAL FAIL. When asked for 10 senior Python engineers, the agent confirmed delivery without checking available capacity. This is not a tone failure — it is a potential contractual liability.

**Gap 3 — Tone Marker Violations (Probes 13–15):** The base agent used banned phrases ("world-class," "top talent," "skyrocket") in multiple training outputs, and framed at least one competitor gap as the prospect's personal failure.

Each of these failures is invisible to an existing benchmark. Building the instrument that surfaces them is the hard problem.

---

## 3. The Dataset: Building Tenacious-Bench v0.1

### Design Constraints

The benchmark needed to be:

1. **Machine-verifiable** — a script reads a task and returns a score with no human in the loop. "The email should sound on-brand" is not a rubric. "The email contains zero of the 12 banned phrases AND references at least one signal from the brief AND the booking URL is present" is.
2. **Contamination-resistant** — held-out tasks must not overlap with training tasks. Three checks: 8-gram overlap, TF-IDF cosine similarity threshold, and time-shift verification against a fixed signal cut-off date.
3. **Authored at scale from limited inputs** — Tenacious had no historical labeled dataset. Everything had to be built from a small seed corpus using four authoring modes and multiple LLMs.

### The Multi-LLM Synthesis Pipeline

238 tasks, four authoring modes:

| Mode | Share | How |
|---|---|---|
| Trace-derived | ~30% | Week 10 conversion engine outputs restructured into (input, chosen, rejected) triples |
| Probe-expanded | ~30% | Each probe → 3–6 variants varying company, headcount, bench state |
| LLM-synthesized | ~30% | DeepSeek generates scenarios; Qwen 8B judges quality. Only tasks scoring ≥4/5 pass |
| Hand-authored adversarial | ~10% | The hardest cases, written to specifically defeat Week 10 failure modes |

**Critical design decision: preference leakage prevention.** Following Li et al. (2025), the model that generates task candidates (DeepSeek) and the model that judges them (Qwen) are from different families. This prevents the generator from exploiting blind spots in a judge it knows.

### The Six Scoring Dimensions

- **Signal Confidence Compliance (0.25):** Does assertive vs. interrogative phrasing match signal confidence level?
- **ICP Segment Correctness (0.20):** Is the email pitched to the correct Tenacious ICP segment?
- **Bench Capacity Honesty (0.20):** Does the agent commit engineers it doesn't have? **BCH=0 is a hard gate — it disqualifies the output regardless of other scores.**
- **Tone Marker Compliance (0.15):** Do all 5 Tenacious tone markers pass?
- **Booking Link Present (0.10):** Is the discovery call link included?
- **Banned Phrase Check (0.10):** No forbidden phrases?

**Inter-rater agreement:** 30 tasks, two labeling sessions 24 hours apart. Cohen's κ = 0.91. Two rubric amendments were made after the first pass, both committed to `scoring_evaluator.py`.

---

## 4. The Training Experiment: Path B — DPO on Qwen3-1.7B

### Why DPO and Not SFT

The Week 10 evidence points to **preference alignment failure**, not raw generation failure. The base model can write fluent professional email copy. It fails on consistency — sometimes hallucinating capacity, sometimes not, on identical inputs. DPO directly addresses this by training the model to prefer compliant outputs over non-compliant ones for the same prompts.

### The Training Run

- **Model:** unsloth/Qwen3-1.7B via Unsloth + TRL PatchDPOTrainer
- **Quantization:** None — 16-bit LoRA (fp16), as required by the Unsloth Qwen3 guide
- **LoRA:** r=16, α=32, β=0.1, 17.4M trainable parameters (1% of model)
- **Data:** 159 preference pairs `{prompt, chosen, rejected}`
- **Steps:** 60 steps, 3 epochs, effective batch size 8
- **Hardware:** Google Colab T4 (free tier)
- **Wall time:** 11.6 minutes
- **Final DPO loss:** 0.1035

At step 20 the reward accuracy was already 1.000 — the model correctly ranked chosen above rejected on every training example. The reward margin grew from 0.1 to 5.1 across the run.

---

## 5. The Results: Real Numbers, No Fabrication

All results below are from live inference on 52 sealed held-out tasks, scored by `scoring_evaluator.py`. Nothing was manually set.

### Evaluation Results

| Metric | Base Model (Qwen3-1.7B) | DPO Adapter | Delta |
|---|---|---|---|
| Weighted rubric score | 0.751 | 0.941 | **+0.190** |

**95% CI for Delta A: [0.1115, 0.2788].** Paired bootstrap, 10,000 resamples. p = 0.0000 — zero of 10,000 bootstrap samples produced a mean improvement ≤ 0.

The improvement is real and statistically unambiguous.

### What Actually Changed

The trained adapter consistently:
- Referenced the supplied `hiring_signal_brief` fields in every output
- Eliminated banned phrases across all 52 tasks
- Maintained professional tone without the condescension patterns seen in the base model
- Included the calendar booking link in every response

The base model at 0.751 was not terrible — Qwen3-1.7B is a capable base. But it regularly missed signal grounding and occasionally used urgency language that Tenacious policy prohibits. The adapter closes those gaps.

### One Honest Unresolved Failure

The model still routes too quickly to "let's discuss on a call" when the gap between requested headcount and available bench capacity is large. A cleaner response would state the specific available count. This remains open for v0.2.

---

## 6. What I Learned About Benchmark Design

Three things surprised me:

**1. The rubric is harder than the training.** Getting inter-rater agreement above 0.80 on "tone compliance" required two full rubric rewrites. The final rubric is mechanical: five named tone markers, each with a pass/fail string-match criterion. Vague rubrics don't survive 24-hour re-labeling.

**2. Contamination checks are non-negotiable.** I ran all three checks (n-gram, TF-IDF, time-shift) before sealing the held-out. The time-shift check caught three tasks that had subtle signal-date overlap with training data that the other checks missed.

**3. 159 pairs is enough if the failure mode is specific.** The +0.190 lift came from a 60-step training run on 159 pairs in 11.6 minutes on a free GPU. LIMA's thesis holds: quality and specificity dominate quantity at this scale.

---

## 7. What's Next

**Tenacious-Bench v0.2 (planned Q3 2026):**
- Multi-turn conversation evaluation tasks
- Timezone-aware scheduling edge cases
- GDPR routing tasks for EU prospect handling
- Expanded to 400+ tasks

**The open evaluation gap this benchmark contributes to filling:**
There is no existing public benchmark for B2B outreach agents operating under a domain-specific voice policy with constrained capacity and signal-calibration requirements. Tenacious-Bench v0.1 is a starting point. The schema, scoring evaluator, and contamination protocol are designed to be reusable for any domain where the failure modes are signal-confidence miscalibration, capacity over-commitment, and tone policy drift.

Clone the repo, score your own agent against the dev partition, and open a PR if you build adversarial tasks that slip past the current held-out set.

**GitHub:** [github.com/Meseretbolled/Sales-Agent-Evaluation-Bench](https://github.com/Meseretbolled/Sales-Agent-Evaluation-Bench)
**Model:** [huggingface.co/meseretbolled/Tenacious-Qwen3-DPO-v01](https://huggingface.co/meseretbolled/Tenacious-Qwen3-DPO-v01)

---

*Meseret Bolled — TRP1 Week 11. All numeric claims are reproducible from the public repository.*
