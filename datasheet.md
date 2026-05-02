# Tenacious-Bench v0.1 — Dataset Datasheet
## Following Gebru et al. (2021) and Pushkarna et al. (FAccT 2022)

**Dataset name:** tenacious-bench-v0.1  
**Version:** 0.1.0  
**Authors:** Meseret Bolled  
**Release date:** May 2026  
**HuggingFace:** https://huggingface.co/datasets/meseretbolled/tenacious-bench-v0.1  
**License:** CC-BY-4.0  
**Contact:** github.com/Meseretbolled/Sales-Agent-Evaluation-Bench

---

## Section 1: Motivation

**Why was this dataset created?**  
To measure failure modes in B2B sales outreach AI agents that existing benchmarks (τ²-Bench retail, AgentBench, WebArena) cannot capture. Specifically: signal-confidence calibration, bench-capacity honesty, ICP segment correctness, and tone-marker compliance against a labeled domain voice guide.

**Who created it and on whose behalf?**  
Created by Meseret Bolled as part of the 10 Academy KAIM8 Week 11 challenge. The dataset is anchored to the Tenacious Intelligence Corporation workflow but contains no private Tenacious data — all company names in the dataset are real publicly listed companies; all prospect names and email addresses are synthetic.

**Was there any funding?**  
No external funding. Total compute cost: ~$1.56 (API costs via OpenRouter). Training: $0 (Colab T4 free tier).

**Any other motivation?**  
There is no existing public benchmark for B2B outreach agents operating under a domain voice policy with constrained supply-side capacity. This dataset contributes to the open evaluation community by providing a reusable evaluation framework for sales agent fine-tuning.

---

## Section 2: Composition

**What does the dataset contain?**  
238 evaluation tasks. Each task is a structured (input, expected_behavior, scoring_notes) triple. Input includes a `hiring_signal_brief` (structured public-signal enrichment for a real company) and a `prospect_context` (synthetic contact at that company).

**Partitions:**

| Partition | Tasks | Use |
|-----------|-------|-----|
| train | 119 | DPO/SFT training |
| dev | 67 | Public development and evaluation |
| held_out | 52 | Sealed final evaluation |

**Source mode distribution:**

| Source Mode | Tasks | % |
|-------------|-------|---|
| Programmatic (parameter sweep) | ~95 | 40% |
| Probe-expanded (from probe_library.md) | ~50 | 21% |
| LLM-synthesized (DeepSeek + Qwen judge) | ~60 | 25% |
| Hand-authored (adversarial edge cases) | ~33 | 14% |

**ICP segment distribution (approximate):**

| Segment | % |
|---------|---|
| segment_1_series_a_b | 20% |
| segment_2_mid_market_restructure | 25% |
| segment_3_leadership_transition | 20% |
| segment_4_specialized_capability | 15% |
| abstain (all signals below threshold) | 20% |

**Does the dataset contain all possible instances, or a sample?**  
A sample. The parameter space (company × signal × bench_state × confidence) is combinatorially large. This dataset covers the failure modes most frequently observed in Week 10 traces, weighted by ACV-at-risk from failure_taxonomy.md.

**Are there labels or ground truth?**  
Each task has machine-verifiable scoring rules (see schema.json) and an `expected_behavior` field for the LLM judge. The `scoring_notes` field gives dimension-specific pass/fail criteria.

**Is any information missing?**  
The held-out partition is not included in the public HuggingFace release — it is released separately after the leaderboard is published. The `benchmark_scores` field on each held-out task is sealed.

**Are there relationships between instances?**  
Probe-expanded tasks are grouped by `probe_id` (e.g., TB-PR-H-P9-00 through TB-PR-H-P9-05 all derive from Probe 9 — "Prospect asks for 10 Python engineers"). These variants share the same failure category but vary in company, headcount, and bench state.

**Is there any data that could be considered offensive or problematic?**  
No. All company signals reference real public events (layoffs, funding rounds, leadership changes from public sources such as layoffs.fyi, Crunchbase, LinkedIn announcements). Prospect names are synthetic. No individual private data is included.

---

## Section 3: Collection Process

**How was the data collected?**  
Four authoring modes were used simultaneously:

1. **Trace-derived (~22%):** Week 10 conversion engine outputs from `trace_log.jsonl` were restructured into evaluation tasks by `src/dataset/trace_restructurer.py`. The agent's actual output on a real prospect becomes the `rejected` response; the corrected output becomes `chosen`.

2. **Probe-expanded (~21%):** Each entry in `probe_library.md` was expanded into 3–6 task variants using `src/dataset/probe_expander.py`, varying company, headcount request, bench state, and signal date. A single "bench over-commitment" probe (Probe 9) expands into 6 tasks covering different stack/headcount combinations.

3. **LLM-synthesized (~25%):** `src/dataset/synthesizer.py` called DeepSeek deepseek-chat via OpenRouter to generate scenario seeds, then called Qwen qwen3-next-80b-a3b-instruct as the quality judge. Only tasks scoring ≥4/5 on input_coherence, ground_truth_verifiability, and rubric_clarity passed the judge filter.

4. **Hand-authored (~14%):** The 33 hardest adversarial cases were written by the trainee to specifically defeat Week 10 failure modes that the synthesis pipeline could not generate. These include: hostile prospect replies, multi-signal conflict scenarios, and edge cases in bench capacity routing.

**Was there any preprocessing?**  
- Deduplication: `src/dataset/contamination_check.py` removed near-duplicate tasks (n-gram + TF-IDF cosine similarity checks)
- Normalization: Company names, signal dates, and bench states were normalized to consistent formats
- Held-out sealing: held_out/ partition was sealed after contamination checks passed

**Were any instruments or sensors used?**  
No. All data was generated via API calls to DeepSeek and Qwen via OpenRouter, plus programmatic expansion of templates.

**Did the collection process involve human subjects?**  
No. All prospect names and emails are synthetic. Company names are real but no individual private data was collected.

---

## Section 4: Preprocessing / Cleaning / Labeling

**Was any preprocessing done?**  
- Banned phrase check: All 238 tasks were filtered to remove any ground-truth `expected_behavior` that contained banned phrases from the Tenacious Style Guide v2.
- Word count normalization: Tasks were filtered to ensure `expected_behavior` respects the cold outreach (120 word), warm reply (200 word), and re-engagement (100 word) limits.
- Template filling: All `[Prospect's Name]` and `[Company]` placeholders were resolved before tasks entered the dataset.

**Were any labels generated by human annotators?**  
The 33 hand-authored tasks were labeled entirely by the trainee. The inter-rater agreement methodology (see inter_rater_agreement.md) used a single annotator with a 48-hour re-label gap as the consistency check. Cohen's Kappa = 0.80 overall (see inter_rater_agreement.md for per-dimension breakdown).

**Was the labeling process reviewed?**  
Two rubric amendments were made based on the inter-rater agreement analysis:
1. `signal_confidence_compliance`: Added explicit rule for "ask" phrasing mode requiring question mark or "if [topic] is a priority" phrasing.
2. `icp_segment_correctness` for abstain tasks: Added forbidden keyword list that triggers a fail if any segment-specific language appears in an abstain task output.

---

## Section 5: Uses

**What tasks has this dataset been used for?**  
- Evaluation of the base Qwen2.5-1.5B-Instruct agent against Tenacious-specific failure modes
- DPO fine-tuning of Qwen2.5-1.5B-Instruct to produce the Tenacious-Qwen-DPO-Stable adapter
- Held-out evaluation to measure the Delta A lift of the fine-tuned model

**Are there tasks for which the dataset should NOT be used?**  
- **Not a general sales training dataset.** The signal briefs are grounded in Tenacious-specific business rules (ICP definitions, bench capacity, pricing bands). Applying this dataset to fine-tune a generic sales agent would embed Tenacious-specific constraints into the model weights.
- **Not suitable for training models on real company data.** The company names in signal briefs reference real events; fine-tuning on this data for production use requires legal review of the underlying signal sources (layoffs.fyi terms, Crunchbase ODM license).

**Will the dataset be updated?**  
Tenacious-Bench v0.2 will add: (a) multi-turn conversation evaluation tasks; (b) timezone-aware scheduling edge cases (Probes 22–24); (c) GDPR routing tasks (Probe 23). Timeline: Q3 2026.

---

## Section 6: Distribution

**How will the dataset be distributed?**  
Via HuggingFace Datasets: `meseretbolled/tenacious-bench-v0.1`. The train and dev partitions are publicly available. The held_out partition will be released after the leaderboard is published.

**Is the dataset subject to any copyright or IP restrictions?**  
Company names and public signals (funding rounds, layoff counts, leadership changes) are from publicly available sources. All prospect names and emails are synthetic. The dataset is released under CC-BY-4.0.

**Will a notification be sent to those mentioned in the dataset?**  
No individuals are mentioned. Company names are included for grounding, not for any private disclosure.

---

## Section 7: Maintenance

**Who is responsible for maintaining the dataset?**  
Meseret Bolled (github.com/Meseretbolled). Issues can be filed on the GitHub repository.

**How will errors be communicated?**  
Via GitHub Issues. Erroneous tasks will be flagged with the `data-bug` label and removed or corrected in patch releases.

**Is there a contribution process?**  
Pull requests for new adversarial tasks are welcome. All contributed tasks must pass the contamination check (`src/dataset/contamination_check.py`) and the judge filter (score ≥4/5 on all three dimensions) before merging.

**Will older versions be retained?**  
Yes. v0.1.0 will remain available on HuggingFace under a versioned tag after v0.2 is released.

---

## Layered Detail (Pushkarna et al., FAccT 2022)

### Telescopic (high-level summary)
238 B2B sales agent evaluation tasks covering 5 ICP segments, 4 authoring modes, and 6 scoring dimensions. Built from Week 10 conversion engine traces and the Tenacious probe library. Released CC-BY-4.0.

### Periscopic (medium detail)
Tasks are structured as (hiring_signal_brief, prospect_context, expected_behavior, scoring_notes) triples. Signal briefs are grounded in real public company events with synthetic prospect contacts. Scoring is machine-verifiable on 5 of 6 dimensions; tone compliance uses an LLM judge from a different model family. Inter-rater agreement: Cohen's Kappa 0.80 overall.

### Microscopic (full detail)
See schema.json for the complete JSON schema. See src/evaluation/scoring_evaluator.py for the exact scoring implementation. See contamination_report.json for the three-check contamination audit results. See inter_rater_agreement.md for per-dimension Kappa values and rubric amendments.