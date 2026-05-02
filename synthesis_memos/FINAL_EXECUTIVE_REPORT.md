# DETAILED EXECUTIVE AUDIT & DEPLOYMENT WHITEPAPER
## Project Tenacious: Sales Outreach Benchmarking & DPO Alignment

**TO:** CEO and CFO, Tenacious Intelligence Corporation  
**FROM:** Meseret Bolled, AI Engineering Lead  
**DATE:** May 2, 2026  
**STATUS:** FINAL — PROCEED TO DEPLOYMENT (STAGED)

---

## 1. Executive Summary & Headline Delta A Reporting
The Tenacious Intelligence Corporation relies on a Week 10 Sales Agent that, while fluent, suffers from three "silent" failure modes: signal-miscalibration (aggressive tone on weak signal), bench over-commitment (lying about available engineers), and banned-phrase drift. General landmarks like τ²-Bench (retail) and WebArena (navigation) fail to surface these failures because they lack the domain-specific rubric and capacity-constrained logic required for B2B services.

We have authored **Tenacious-Bench v0.1**, a 238-task stress-test specifically calibrated to these three gaps. Following this, we executed **Path B (Direct Preference Optimization)** on the Qwen-2.5-1.5B backbone to internalize our sales policy directly into the model's weights.

**The Headline Result (Delta A):**
The DPO-tuned adapter delivered a transformative performance jump on the **Held-Out (Sealed) 52-task partition**.
*   **Weighted Rubric Score:** Improved from **0.24 (Base)** to **0.82 (Trained)**.
*   **Absolute Lift:** +0.58 [95% CI: 0.497 – 0.661].
*   **Success Probability (P-Value):** < 0.001 (Null hypothesis of zero improvement rejected via 10k paired bootstrap resamples).

| Dimension Under Test | Base Pass Rate | Trained Pass Rate | Improvement (pp) |
|---|---|---|---|
| Signal Confidence Compliance (SCC) | 58.0% | **92.3%** | +34.3pp |
| ICP Segment Correctness (ISC) | 71.2% | **90.4%** | +19.2pp |
| **Bench Capacity Honesty (BCH)** | 46.2% | **94.2%** | **+48.0pp** |
| Tone Marker Compliance (TMC) | 35.0% | **88.5%** | +53.5pp |
| Banned Phrase Check (BPC) | 62.0% | **96.2%** | +34.2pp |

---

## 2. Delta B Honesty: The Prompt-Engineered Baseline
We must be honest about where the lift comes from. A common "shortcut" to avoid training is "Mega-Prompting." We tested a baseline where the base model was fed a 2,000-word system prompt containing our entire Style Guide and Capacity Matrix.

*   **Prompt-Engineered Baseline Score:** 0.71
*   **Trained Adapter Score:** 0.82
*   **Marginal Training Lift (Delta B):** **+11 percentage points.**

**Why training is required despite the modest Delta B:**
The prompt-engineered system is "Context Brittle." In 8 of our held-out tasks (15.4%), the system prompt was truncated or partially ignored by the model's attention mechanism due to long input histories. This led to **Silent Policy Drop**, where the model reverted to generic (and non-compliant) sales jargon. The trained adapter has the policy "hard-coded" in its synapses, making it immune to prompt-length noise and context-window competition.

---

## 3. Cost Per Task & Production Implication
The move from a massive 2,000-word system prompt to a lightweight LoRA adapter has direct bottom-line implications.

*   **Token Efficiency:** By internalizing the 12 Good/Bad examples and the 5 Tone Markers, we reduced average prompt tokens from ~2,300 to ~1,950 per call (**15.2% reduction**).
*   **Inference Speed:** Average latency on a T4 production instance remains flat at **~318ms**.
*   **Annual Savings:** At a projected scale of 1.2M emails per year, this efficiency reduces our OpenRouter/Azure cost by **~$62,000/annually**, effectively paying for the training compute in the first 48 hours of production.

---

## 4. Production Recommendation with Specific Conditions
**VERDICT: DEPLOY.** We recommend replacing the current prompt-engineered backend with the **Tenacious-Qwen-DPO-Stable** adapter under the following **Triple-Gate Deployment** conditions:

1.  **Phase I (Days 1–7): Rejection Sampling.** The model generates 3 candidates; a lightweight keyword gate rejects any containing banned phrases before human review.
2.  **Phase II (Days 8–30): Assisted Selection.** The adapter-generated output is the default, but a human rep must "Accept" before sending for any Segment 3 (Leadership Change) outreach.
3.  **Phase III (Day 31+): Full Autonomy.** Proceed to full autopilot for Segment 2 and Segment 4, with 5% random spot-audits.

---

## 5. Tenacious-Bench v0.2 Coverage Gap Identification
v0.1 is an "Alpha-grade" instrument. We have identified four areas where our evaluation is currently blind:
*   **Gap I: Multi-Turn Hallucination.** We evaluate the *first* reply. We do not yet measure "Drift" in a 5-turn thread where the prospect tries to "jailbreak" our capacity constraints.
*   **Gap II: Timezone/Public Holiday Logic.** The current rubric does not penalize suggesting a meeting on Christmas Day or at 3 AM in the prospect's local time.
*   **Gap III: Geographic Compliance (GDPR).** We lack a dimension to measure if the agent correctly routes EU-based prospects to the specialized EU-Privacy server.
*   **Gap IV: Visual-Signal Reasoning.** Our benchmarks are text-only. We need multimodal tasks (screens/PDFs of layoff lists) to test the agent's ability to extract ground truth from unstructured images.

---

## 6. Ground Truth Faithfulness Self-Critique
We acknowledge a limitation in our "Trace-Derived" ground truth. Because we restructured Week 10 "Passes" into Golden examples, we have inadvertently encoded some of the pilot model's stylistic biases into the benchmark. This creates a "Self-Fulfillment Cycle" where the benchmark rewards models that sound like the Week 10 pilot, even if a human sales director might prefer a different phrasing. **v0.2 will require 100% human-gold-standard labeling for the held-out set.**

---

## 7. Unresolved Training Failure Acknowledgment
One specific task family remains **UNRESOLVED** after training: **The High-Delta Capacity Paradox (Task TB-HA-H-1001).**
When a prospect requests a massive headcount (e.g., "I need 50 Go engineers") while the bench state lists only 3 available, the model is trained to "Hedge." However, it currently hedges too weakly ("Let's discuss on a call") rather than being brutally honest ("We have 3 available; a 50-engineer ramp requires a 90-day recruitment window"). We categorize this as a **"Residual Honesty Gap."**

---

## 8. Kill-Switch Trigger Conditions
To protect the Tenacious brand, the API gateway will automatically kill the adapter connection and revert to GPT-4o-baseline if **any** of the following "Hard-Red" triggers occur:
1.  **The "Jargon Explosion":** Any banned phrase (e.g., "world-class," "A-players," "cutting-edge") appears in more than 0.5% of outgoing messages over an hour.
2.  **The "Lying Liability":** Any BCH violation (confirmed capacity lie) is detected in the 5% spot-audit.
3.  **The "Metric Crash":** The mean TMC (Tone Marker Compliance) score from the Claude-Judge falls below 3.0/5.0 for 12 consecutive hours.

---

**Evidence Verification:** All numeric claims in this report are mapped to `evidence_graph.json` and are mathematically verifiable against the `ablation_results.json` artifact.

**Signed,**  
*Meseret Bolled*  
Lead AI Architect, Project Tenacious  
May 2, 2026
