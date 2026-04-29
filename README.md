# Sales Agent Evaluation Bench (Tenacious-Bench v0.1.0)

A domain-specific evaluation benchmark for B2B sales agents, grounded in Tenacious Intelligence Corporation's ICP segments, signal enrichment pipeline, and tone requirements.

Built on top of Week 10: [github.com/Meseretbolled/conversion-engine](https://github.com/Meseretbolled/conversion-engine)

---

## What This Is

τ²-Bench retail — the standard agent benchmark — cannot grade Tenacious-specific failure modes. It scores retail transaction completion. It has no concept of signal confidence thresholds, ICP segment priority rules, bench capacity constraints, or Tenacious tone requirements.

Tenacious-Bench fills this gap with 189+ tasks grounded in Week 10 production traces and adversarial probes, scored automatically on six rubric dimensions.

---

## Repository Structure

```
├── audit_memo.md              # What τ²-Bench misses — 6 failure modes
├── schema.json                # Task schema + 3 example tasks
├── datasheet.md               # Gebru + Pushkarna dataset documentation
├── methodology.md             # Path B justification from Week 10 evidence
├── inter_rater_agreement.md   # Label consistency — kappa=0.80 overall
├── cost_log.md                # Every API charge logged
├── contamination_report.json  # 3 contamination checks
│
├── src/
│   ├── dataset/
│   │   ├── trace_restructurer.py   # Converts 150 traces → 60 tasks
│   │   ├── probe_expander.py       # Expands 13 probes → 52 tasks
│   │   ├── synthesizer.py          # Multi-LLM generation → 54+ tasks
│   │   ├── contamination_check.py  # N-gram, embedding, time-shift checks
│   │   └── partitioner.py          # Stratified 50/30/20 split
│   └── evaluation/
│       └── scoring_evaluator.py    # Auto-grades any agent output
│
├── tenacious_bench_v0.1/
│   ├── train/     # 97 tasks — LoRA fine-tuning
│   ├── dev/       # 56 tasks — training iteration
│   └── held_out/  # 36 tasks — final delta (gitignored)
│
├── generation_scripts/    # Reproducible generation scripts
├── synthesis_memos/       # Critical reading memos (Liu, Gebru)
└── training/              # Colab notebook (Day 5)
```

---

## Dataset Composition

| Source | Tasks | Share |
|---|---|---|
| trace_derived | 60 | 32% |
| probe_expanded | 52 | 28% |
| llm_synthesized | 54 | 29% |
| hand_authored | 1 | <1% |
| **Total** | **189** | |

| Partition | Count | Purpose |
|---|---|---|
| train/ | 97 | LoRA fine-tuning |
| dev/ | 56 | Training iteration |
| held_out/ | 36 | Final delta measurement |

---

## Six Rubric Dimensions

| Dimension | Weight | How Checked |
|---|---|---|
| signal_confidence_compliance | 0.25 | Rule-based signal parsing |
| icp_segment_correctness | 0.20 | Keyword + reference classifier |
| bench_capacity_honesty | 0.20 | Regex + bench_summary.json |
| tone_compliance | 0.15 | LLM judge (different model family) |
| booking_link_present | 0.10 | Exact string match |
| banned_phrase_check | 0.10 | Case-insensitive search |

---

## Quick Start

```bash
# Clone
git clone https://github.com/Meseretbolled/Sales-Agent-Evaluation-Bench.git
cd Sales-Agent-Evaluation-Bench

# Install
pip install -r requirements.txt

# Regenerate dataset from Week 10 traces
python3 src/dataset/trace_restructurer.py \
  --traces ../conversion-engine/eval/trace_log.jsonl \
  --output-dir tenacious_bench_v0.1

# Score an agent output against a task
python3 src/evaluation/scoring_evaluator.py \
  --task tenacious_bench_v0.1/dev/TB-HA-E-000.json \
  --output "Your agent output here"
```

---

## Week 10 Reference

| Metric | Value |
|---|---|
| Total traces | 150 |
| Passed traces | 109 (72.7%) |
| Failed traces | 41 (27.3%) |
| Adversarial probes | 30 — 100% pass rate |
| τ²-Bench baseline | 72.67% |
| tenacious_method_v3 | 56.7% (17/30) |
| Delta | -15.97pp (domain mismatch) |

---

## Training Plan (Path B — SimPO)

- Model: Qwen 3.5 2B via Unsloth on Colab T4 (free)
- Algorithm: SimPO — reference-free, fits T4
- Epochs: 1 (LIMA recommendation for <200 examples)
- Chosen: discovery transcripts + passed traces
- Rejected: failed traces + pre-fix probe outputs

---

## Status

- [x] Act I — Audit memo, schema, scoring evaluator
- [x] Act II — Dataset 189 tasks, contamination check, partitioned
- [ ] Act III — Training path declared (Path B — SimPO)
- [ ] Act IV — LoRA training on Colab T4
- [ ] Act V — HuggingFace publication, blog post

---

## Author

Meseret Bolled — meseretbolled@gmail.com
10Academy KAIM Week 11 — April 2026