# Tenacious-Bench Datasheet

**Template:** Gebru et al. (2021) + Pushkarna et al. FAccT 2022
**Dataset:** Tenacious-Bench v0.1.0
**Author:** Meseret Bolled
**Date:** April 2026
**Repository:** github.com/Meseretbolled/tenacious-bench
**HuggingFace:** (pending publication)

---

## Telescopic Summary

Tenacious-Bench is a 200-300 task evaluation dataset for B2B sales agents. It tests six failure modes that τ²-Bench retail cannot grade: signal confidence compliance, ICP segment correctness, bench capacity honesty, tone compliance, booking link presence, and banned phrase avoidance. All tasks are machine-verifiable. The dataset is grounded in Week 10 production traces and adversarial probes from the Tenacious Conversion Engine project.

---

## 1. Motivation

**Why was this dataset created?**

τ²-Bench retail — the standard agent evaluation benchmark used in Week 10 — cannot grade Tenacious-specific failure modes. It scores whether retail transactions complete correctly. It has no concept of signal confidence thresholds, ICP segment priority rules, bench capacity constraints, or Tenacious tone requirements. A Tenacious outreach agent that passes τ²-Bench retail could still embarrass the company by asserting an unverified layoff signal to a CTO, over-committing engineers beyond bench availability, or using banned phrases in a cold email.

Tenacious-Bench fills this gap with domain-specific tasks grounded in real failure evidence from Week 10 production traces and adversarial probes.

**Who created this dataset and on whose behalf?**

Created by Meseret Bolled as part of the 10Academy KAIM Week 11 challenge. The dataset is designed to evaluate agents built for Tenacious Intelligence Corporation's B2B outreach pipeline.

**Who funded the creation?**

LLM synthesis costs were funded by the Week 11 API budget ($3-5 allocation). Training and evaluation costs are within the $10 per trainee envelope. No external funding.

---

## 2. Composition

**What does the dataset represent?**

Each instance is one evaluation task. A task consists of:
- A hiring signal brief (company, layoff signal, funding signal, leadership signal, AI maturity score, job signal)
- A bench state (available engineers by stack)
- A prospect context (name, title, company, email)
- An optional conversation history (for multi-turn tasks)
- An expected rubric (ground truth for all six dimensions)
- A ground truth ICP segment

The agent being evaluated receives the input and must produce a cold outreach email or conversation response. The scoring evaluator grades the output automatically on six dimensions.

**How many instances?**

Target: 200-300 tasks across four source modes:

| Source mode | Count | Share |
|---|---|---|
| trace_derived | ~60 | 25% |
| probe_expanded | ~90 | 35% |
| llm_synthesized | ~80 | 30% |
| hand_authored | ~30 | 10% |

**Partition split:**

| Partition | Count | Purpose |
|---|---|---|
| train/ | 50% | LoRA adapter fine-tuning |
| dev/ | 30% | Iteration during training |
| held_out/ | 20% | Final delta measurement only |

**What data does each instance contain?**

Structured JSON following the task schema in `schema.json`. All fields are synthetic or derived from public data (layoffs.fyi, Crunchbase ODM, company press releases). No private or personally identifiable information is included. Prospect names and emails are synthetic.

**Is there a label or target for each instance?**

Yes. Each task has:
- `ground_truth_segment` — the correct ICP segment (categorical, 5 classes)
- `expected_rubric` — ground truth for all 6 rubric dimensions (boolean per dimension)
- `scoring_notes` — human-readable explanation of what a correct output must contain

**Are there recommended splits?**

Yes — see partition split above. The held_out/ partition must not be used during training or iteration. It is gitignored.

**Are there any errors, sources of noise, or redundancies?**

**Trace-derived tasks** inherit the domain mismatch from Week 10 — the original traces come from τ²-Bench retail tasks, not actual Tenacious outreach conversations. The signal inputs are Tenacious-specific but the task structure is influenced by retail benchmark framing.

**LLM-synthesized tasks** are filtered by a judge model (qwen3-next-80b) with a threshold of 3/4 on four quality criteria. Tasks below threshold are discarded. False accept rate is estimated at 10-15% based on manual review of 20 accepted tasks.

**Probe-expanded tasks** share signal structure within probe families — variants of Probe 2 all test the same leadership-vs-layoff conflict at different companies. This is intentional but introduces within-family redundancy.

**Does the dataset contain data that might be considered confidential?**

No. All company names are either real public companies (Atlassian, Snap, Block, etc.) or fictional. All signal data is derived from public sources (layoffs.fyi, Crunchbase). No internal Tenacious data is included beyond the seed files (style_guide.md, icp_definition.md, pricing_sheet.md, bench_summary.json) which are pseudonymised program materials.

**Does the dataset contain data that might be considered offensive or harmful?**

No. Tasks involve B2B outreach scenarios. No sensitive personal data, political content, or harmful content is present.

---

## 3. Collection

**How was the data collected?**

Four authoring modes were used:

**Mode 1 — Trace-derived (~25%):**
150 traces from `eval/trace_log.jsonl` (Week 10 τ²-Bench evaluation run) were loaded. Each trace contains simulation_id, task_id, reward (0.0 or 1.0), duration, and termination_reason. Failed traces (reward=0.0, n=41) were prioritised as they represent real failure patterns. Each trace was restructured into a Tenacious-specific task by mapping it to a segment scenario with real company signal data.

**Mode 2 — Probe-expanded (~35%):**
30 adversarial probes from `probes/probe_library.md` (Week 10) were selected. 13 probes covering 5 failure categories were expanded into 3-8 variants each by parametric sweep over companies, confidence levels, and bench states. Each variant tests the same failure mode under different input conditions.

**Mode 3 — LLM-synthesized (~30%):**
DeepSeek V3 (via OpenRouter, model: deepseek/deepseek-chat) generated task inputs from 6 seed scenario templates. Each generated task was judged by qwen3-next-80b-a3b-instruct (different model family, following Li et al. 2025 to prevent preference leakage). Tasks scoring < 3/4 on the quality rubric were discarded.

**Mode 4 — Hand-authored (~10%):**
30-50 tasks written manually by Meseret Bolled targeting the hardest edge cases not covered by synthesis — three-simultaneous-disqualifier scenarios, multi-turn conversations with booking intent, and cases where all signals are low confidence.

**Who was involved in data collection?**

Meseret Bolled authored all tasks. No crowdsourcing or external annotation.

**Over what time period was the data collected?**

April 28-30, 2026 (3 days during Week 11).

**Were any ethical review processes conducted?**

Not applicable. The dataset contains no personal data, no human subjects, and no sensitive content.

---

## 4. Preprocessing

**Was any preprocessing done?**

Yes:

1. **Contamination check** — three checks run before sealing held_out/: n-gram overlap (threshold: 8-gram), embedding similarity (threshold: cosine < 0.85, method: TF-IDF), and time-shift verification (layoff dates verified against Week 10 cutoff April 2026).

2. **Judge filtering** — all LLM-synthesized tasks passed through qwen3-next-80b quality judge before inclusion. Acceptance threshold: 3/4 on signal_consistency, segment_alignment, rubric_clarity, realistic_inputs.

3. **Stratified partitioning** — tasks split 50/30/20 stratified by source_mode × difficulty × segment to ensure representative coverage in each partition.

**Is the preprocessing reversible?**

Yes. The generation scripts in `generation_scripts/` are fully reproducible with the same random seed (seed=42).

---

## 5. Uses

**What tasks has the dataset been used for?**

- Evaluating the Tenacious Conversion Engine outreach agent (Week 11 delta measurement)
- Fine-tuning a LoRA adapter on Qwen 3.5 using Path B preference optimization (DPO/SimPO/ORPO)

**Is there anything about the composition of the dataset or the way it was collected that might impact future uses?**

Yes — three important limitations:

1. **Signal data is static.** Layoff dates and funding events are frozen at April 2026. The dataset will become stale as companies change. Tenacious-Bench requires periodic refresh of signal inputs to remain valid.

2. **Domain specificity.** Tasks are calibrated for Tenacious's four ICP segments, pricing, and bench capacity. The benchmark is not suitable for evaluating general-purpose sales agents without modification.

3. **Trace-derived domain mismatch.** 25% of tasks derive from τ²-Bench retail traces. These tasks inherit retail framing artifacts. Scores on these tasks may not reflect purely Tenacious-specific behavior.

**Are there tasks for which the dataset should not be used?**

This dataset should not be used to evaluate agents in domains unrelated to B2B sales. It should not be used to train general-purpose language models without significant modification of the rubric and seed materials.

---

## 6. Distribution

**How will the dataset be distributed?**

Published on HuggingFace Datasets under the dataset name `Meseretbolled/tenacious-bench` (pending). The held_out/ partition is withheld from the public release to preserve benchmark integrity.

**What license applies?**

Apache 2.0. Dataset may be used for research and commercial purposes with attribution.

**Have any third parties imposed restrictions on the data?**

No. All company signal data is derived from public sources. Seed files (style_guide.md, etc.) are pseudonymised program materials not subject to external restrictions.

---

## 7. Maintenance

**Who is maintaining the dataset?**

Meseret Bolled. Contact: meseretbolled@gmail.com

**How often will the dataset be updated?**

Version 0.1.0 is the initial release for Week 11 interim submission. Version 0.2.0 is planned following the training run, incorporating held_out task corrections and additional hand-authored adversarial tasks.

**Will older versions be retained?**

Yes — versioned in the GitHub repository and HuggingFace dataset card.

**If others want to contribute, is there a mechanism for them to do so?**

Pull requests are welcome on github.com/Meseretbolled/tenacious-bench. New tasks must follow the schema in `schema.json` and pass the contamination check before merge.

---

## Periscopic Detail — Rubric Dimensions

| Dimension | Weight | Check Method | Source |
|---|---|---|---|
| signal_confidence_compliance | 0.25 | Rule-based signal parsing | probe_library.md, outreach_composer.py |
| icp_segment_correctness | 0.20 | Keyword + reference classifier | icp_definition.md |
| bench_capacity_honesty | 0.20 | Regex + bench_summary.json | bench_summary.json |
| tone_compliance | 0.15 | LLM judge (different family) | style_guide.md |
| booking_link_present | 0.10 | Exact string match | outreach_composer.py |
| banned_phrase_check | 0.10 | Case-insensitive search | style_guide.md |

## Microscopic Detail — Inter-Rater Agreement

30 tasks were labeled twice by the same annotator (Meseret Bolled) at 48-hour intervals to measure label consistency. Agreement results are documented in `inter_rater_agreement.md`.