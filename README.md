# Tenacious-Bench: B2B Sales Agent Evaluation Benchmark

[![Hugging Face Dataset](https://img.shields.io/badge/🤗%20Dataset-meseretbolled%2Ftenacious--bench--v0.1-yellow)](https://huggingface.co/datasets/meseretbolled/tenacious-bench-v0.1)
[![Hugging Face Model](https://img.shields.io/badge/🤗%20Model-meseretbolled%2FTenacious--Qwen--DPO--Stable-blue)](https://huggingface.co/meseretbolled/Tenacious-Qwen-DPO-Stable)
[![Technical Blog](https://img.shields.io/badge/Medium-Blog%20Post-black)](https://medium.com/@meseretbolled/why-your-sales-agent-fails-in-ways-no-benchmark-can-see-and-what-i-built-to-fix-it-73d7e41ada7d)
[![Community Engagement](https://img.shields.io/badge/GitHub-Community%20Issue-green)](https://github.com/sierra-research/tau2-bench/issues/292)
[![License: CC-BY-4.0](https://img.shields.io/badge/License-CC--BY--4.0-lightgrey)](https://creativecommons.org/licenses/by/4.0/)

---

## Overview

Tenacious-Bench is a **238-task evaluation dataset and fine-tuning pipeline** for B2B sales outreach AI agents. It measures three failure modes that no existing public benchmark (τ²-Bench, AgentBench, WebArena) captures:

1. **Signal-confidence miscalibration** — agent asserts on Low/Medium-confidence signals instead of asking
2. **Bench capacity over-commitment** — agent confirms more engineers than available in bench_summary.json
3. **Tone policy drift** — agent uses banned phrases or violates the Tenacious voice guide

The trained LoRA adapter (DPO on Qwen 2.5-1.5B) achieves **0.82 weighted rubric score** on the sealed held-out partition vs. 0.24 for the base model — a **+0.58 improvement** (95% CI: [0.497, 0.661], p<0.001).

---

## Status

| Component | Status |
|---|---|
| Dataset (238 tasks, 3 partitions) | ✅ Complete — on HuggingFace |
| Scoring evaluator (6 dimensions, machine-verifiable) | ✅ Complete — `src/evaluation/scoring_evaluator.py` |
| Contamination check (n-gram + embedding + time-shift) | ✅ Passed — `contamination_report.json` |
| Inter-rater agreement (30 tasks, Cohen's Kappa = 0.80) | ✅ Complete — `inter_rater_agreement.md` |
| DPO training run (Qwen 2.5-1.5B, 60 steps, Colab T4) | ✅ Complete — `training/training_run_seed42.log` |
| Ablation results (Delta A, Delta B, Cost-Pareto) | ✅ Complete — `ablation_results.json` |
| Evidence graph (every claim → source) | ✅ Complete — `evidence_graph.json` |
| CEO/CFO memo (2-page, with skeptic's appendix) | ✅ Complete — `memo_to_ceo_cfo.md` |
| Blog post | ✅ Complete — `blog_post_blueprint.md` |

---

## Dataset: Tenacious-Bench v0.1

**238 tasks** across 5 ICP segments, 4 authoring modes, 6 scoring dimensions.

| Partition | Tasks | Use |
|---|---|---|
| train | 119 | DPO/SFT training |
| dev | 67 | Public development and evaluation |
| held_out | 52 | Sealed final evaluation |

**Scoring dimensions:** Signal Confidence Compliance (0.25) · ICP Segment Correctness (0.20) · Bench Capacity Honesty (0.20, hard gate) · Tone Compliance (0.15) · Booking Link Present (0.10) · Banned Phrase Check (0.10)

---

## Setup

### 1. Install dependencies

```bash
git clone https://github.com/Meseretbolled/Sales-Agent-Evaluation-Bench
cd Sales-Agent-Evaluation-Bench
pip install -r requirements.txt
```

### 2. Verify contamination seal (required before any training)

```bash
python3 src/dataset/contamination_check.py
# Expected output: overall_pass: true, violations: 0
```

### 3. Score your agent on the dev partition

```bash
python3 src/evaluation/scoring_evaluator.py \
    --task tenacious_bench_v0.1/dev/TB-TR-H-043.json \
    --output "YOUR AGENT OUTPUT HERE"
```

### 4. Run DPO fine-tuning (Google Colab — free T4)

Upload `preferences_train.jsonl`, `preferences_dev.jsonl`, and `src/training/dpo_train.py` to Google Colab. Connect to a T4 runtime. Run the training script. Expected wall time: 35–55 minutes.

### 5. Reproduce the headline number

```bash
# Score the trained adapter on the dev partition
python3 src/evaluation/scoring_evaluator.py \
    --partition tenacious_bench_v0.1/dev/ \
    --judge-model openrouter/qwen/qwen3-next-80b-a3b-instruct \
    --output-file results/dev_scores.json
```

Expected dev partition weighted score (trained adapter): ≥0.80 within ±0.02.  
A stranger who clones the repo and follows steps 1–5 should reproduce the headline number within the tolerance above. Total time: under 60 minutes.

---

## Repository Structure

```text
tenacious-bench/
├── src/
│   ├── dataset/
│   │   ├── contamination_check.py    # 8-gram + TF-IDF + time-shift checks
│   │   ├── curate_dataset.py         # Stratified partitioning (50/30/20)
│   │   ├── generate_programmatic_tasks.py
│   │   ├── hand_author.py
│   │   ├── partitioner.py
│   │   ├── prepare_training_data.py  # DeepSeek preference pair generator
│   │   ├── probe_expander.py
│   │   ├── synthesizer.py            # Multi-LLM synthesis (DeepSeek gen + Qwen judge)
│   │   └── trace_restructurer.py
│   ├── evaluation/
│   │   └── scoring_evaluator.py      # Six-dimension machine-verifiable evaluator
│   └── training/
│       └── dpo_train.py              # HF TRL DPO trainer (fixed, seed pinned)
├── tenacious_bench_v0.1/
│   ├── train/                        # 119 tasks (DPO training)
│   ├── dev/                          # 67 tasks (public evaluation)
│   └── held_out/                     # 52 tasks (sealed — gitignored)
├── training/
│   └── training_run_seed42.log       # Step-by-step loss curve and metrics
├── ablation_results.json             # Delta A/B/C, cost-pareto, dim pass rates
├── evidence_graph.json               # Every numeric claim → source
├── contamination_report.json         # Three-check contamination audit
├── inter_rater_agreement.md          # 30-task sample, Cohen's Kappa = 0.80
├── methodology.md                    # Path choice, partitioning, training details
├── datasheet.md                      # Gebru + Pushkarna dataset datasheet
├── audit_memo.md                     # Act I audit (max 600 words)
├── schema.json                       # JSON schema for all task files
├── blog_post_blueprint.md            # Full published blog post
├── memo_to_ceo_cfo.md                # 2-page executive memo with skeptic's appendix
├── cost_log.md                       # Every API charge logged
├── preferences_train.jsonl           # 159 DPO (prompt, chosen, rejected) pairs
├── preferences_dev.jsonl             # Dev preference pairs
├── held_out_traces.jsonl             # Raw held-out evaluation traces
└── requirements.txt
```

---

## Results

| Evaluation | Base (Qwen 2.5-1.5B) | Trained (DPO) | Δ |
|---|---|---|---|
| Weighted rubric score | 0.24 | **0.82** | **+0.58** (95% CI [0.497, 0.661]) |
| Task pass rate | 23.1% | **82.7%** | +59.6pp |
| BCH fail rate | 53.8% | **5.8%** | -48pp |
| Banned phrase violations | 38.5% | **3.8%** | -34.7pp |
| Prompt-engineered baseline | 0.71 | — | Delta B: +0.11 (p=0.004) |

---

## License

**CC-BY-4.0.** You may use, share, and adapt this dataset and code with attribution.  
See [LICENSE](./LICENSE) for details.

Company names in signal briefs reference real public events (layoffs.fyi, Crunchbase). All prospect names and email addresses are synthetic. No private Tenacious data is included.

---

## Citation

```bibtex
@dataset{bolled2026tenacious,
  title        = {Tenacious-Bench: A B2B Sales Agent Evaluation Benchmark},
  author       = {Meseret Bolled},
  year         = {2026},
  publisher    = {HuggingFace},
  url          = {https://huggingface.co/datasets/meseretbolled/tenacious-bench-v0.1},
  license      = {CC-BY-4.0}
}
```

---

## Contact

Issues and pull requests welcome on [GitHub](https://github.com/Meseretbolled/Sales-Agent-Evaluation-Bench).  
New adversarial tasks must pass `contamination_check.py` and score ≥4/5 on the three judge dimensions before merging.