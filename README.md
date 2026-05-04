# Tenacious-Bench v0.1 — B2B Sales Agent Evaluation Benchmark

A domain-specific evaluation benchmark for B2B sales agents, grounded in
Tenacious Intelligence Corporation's ICP segments, signal enrichment pipeline,
and tone requirements.

Built on top of Week 10: [github.com/Meseretbolled/conversion-engine](https://github.com/Meseretbolled/conversion-engine)

---

## Architecture

```mermaid
flowchart TD
    %% ── Layer 0: Production Source ──────────────────────────────────────────
    subgraph W10["Week 10 — Conversion Engine (Production)"]
        CE["Outreach Pipeline\nFastAPI + LLM"]
        TL["149 Langfuse Traces\ntrace_log.jsonl"]
        PL["30 Adversarial Probes\nprobe_library.md"]
        FT["Failure Taxonomy\n10 categories\nfailure_taxonomy.md"]
        CE -->|runtime logs| TL
        CE -->|manual injection| PL
        TL -->|pattern analysis| FT
        PL -->|pattern analysis| FT
    end

    %% ── Layer 1: Dataset Construction ───────────────────────────────────────
    subgraph DS["Act II — Dataset Construction"]
        TR["trace_restructurer.py\n72 trace-derived tasks"]
        PE["probe_expander.py\n71 probe-expanded tasks"]
        SY["synthesizer.py\nDeepSeek-Chat gen\nQwen3-8B judge\n71 llm-synthesized tasks"]
        HA["24 hand-authored\nadversarial tasks"]
        CC["contamination_check.py\n8-gram + TF-IDF + time-shift\n3 checks passed"]
        PT["partitioner.py\nseeds held-out FIRST"]
        BENCH["tenacious_bench_v0.1/\ntrain 159 · dev 57 · held_out 52"]

        TR --> CC
        PE --> CC
        SY --> CC
        HA --> CC
        CC --> PT
        PT --> BENCH
    end

    %% ── Layer 2: DPO Training ────────────────────────────────────────────────
    subgraph TR2["Act IV — DPO Training (Path B)"]
        PAIRS["preferences_train.jsonl\n159 chosen/rejected pairs"]
        COLAB["Google Colab T4\nUnsloth + PatchDPOTrainer\nfp16 LoRA r=16 β=0.1\n60 steps · 11.6 min"]
        ADAPTER["LoRA Adapter\nFinal loss: 0.1035"]
        HF["HuggingFace Hub\nmeseretbolled/Tenacious-Qwen3-DPO-v01"]

        PAIRS --> COLAB
        COLAB --> ADAPTER
        ADAPTER --> HF
    end

    %% ── Layer 3: Evaluation ──────────────────────────────────────────────────
    subgraph EV["Act IV — Ablation Evaluation"]
        HO["held_out/ (52 tasks)\nsealed before training"]
        BASE["Base: Qwen3-1.7B\nno adapter\nScore: 0.751"]
        TRAINED["Trained: Qwen3-1.7B\n+ DPO adapter\nScore: 0.941"]
        SE["scoring_evaluator.py\n6 rubric dimensions\n80% rule-based · 20% LLM judge"]
        AH["ablation_harness.py\n10k bootstrap CI\np-value: 0.0000"]
        RESULT["Delta A: +0.1904\n95% CI [0.1115, 0.2788]"]

        HO --> BASE & TRAINED
        BASE & TRAINED --> SE
        SE --> AH
        AH --> RESULT
    end

    %% ── Layer 4: Production Integration ─────────────────────────────────────
    subgraph PROD["Week 10 → Week 11 Production Integration"]
        QG["Quality Gate\noutreach_composer.py\nbanned-phrase · booking-link · grounding"]
        RENDER["Render Deployment\nconversion-engine10.onrender.com"]
        QG --> RENDER
    end

    %% ── Cross-layer edges ────────────────────────────────────────────────────
    FT -->|"failure modes\n→ rubric design"| DS
    BENCH -->|"train partition\n→ DPO pairs"| TR2
    BENCH -->|"held_out sealed\nbefore training"| EV
    RESULT -->|"+25.4% relative lift\n→ deploy criteria met"| PROD
    HF -->|"adapter available\nfor production swap"| PROD

    %% ── Styling ──────────────────────────────────────────────────────────────
    classDef prod fill:#1a1a2e,color:#e0e0ff,stroke:#4a4a8a
    classDef data fill:#0d3b2e,color:#d4f5e9,stroke:#2d8a6a
    classDef train fill:#2e1a0d,color:#f5e9d4,stroke:#8a5a2d
    classDef eval fill:#1a0d2e,color:#e9d4f5,stroke:#6a2d8a
    classDef integ fill:#2e0d1a,color:#f5d4e9,stroke:#8a2d5a

    class W10,CE,TL,PL,FT prod
    class DS,TR,PE,SY,HA,CC,PT,BENCH data
    class TR2,PAIRS,COLAB,ADAPTER,HF train
    class EV,HO,BASE,TRAINED,SE,AH,RESULT eval
    class PROD,QG,RENDER integ
```

---

## What This Is

τ²-Bench retail cannot grade Tenacious-specific failure modes — it scores retail
transaction completion. It has no concept of signal confidence thresholds, ICP
segment priority rules, bench capacity constraints, or Tenacious tone requirements.

Tenacious-Bench fills this gap with **238 tasks** grounded in Week 10 production
traces and adversarial probes, scored automatically on six rubric dimensions.

---

## Real Results (Path B — DPO, Colab T4, 2026-05-03)

| Metric | Value |
|--------|-------|
| Base model (Qwen3-1.7B) | 0.751 |
| DPO-trained adapter | **0.941** |
| Delta A | **+0.1904** |
| 95% CI (10k bootstrap) | [0.1115, 0.2788] |
| p-value (one-tailed) | 0.0000 |
| Held-out tasks evaluated | 52 |
| Training time (T4) | 11.6 min |
| Final DPO loss | 0.1035 |

**Model adapter:** [meseretbolled/Tenacious-Qwen3-DPO-v01](https://huggingface.co/meseretbolled/Tenacious-Qwen3-DPO-v01)
**Dataset:** [meseretbolled/tenacious-bench-v0.1](https://huggingface.co/datasets/meseretbolled/tenacious-bench-v0.1)

---

## Repository Structure

```
├── audit_memo.md                  # What τ²-Bench misses — 6 failure modes
├── schema.json                    # Task schema + 3 example tasks
├── datasheet.md                   # Gebru + Pushkarna dataset documentation
├── methodology.md                 # Path B justification from Week 10 evidence
├── inter_rater_agreement.md       # Label consistency — Cohen's κ = 0.91
├── cost_log.md                    # Every API charge logged
├── contamination_report.json      # 3 contamination checks passed
├── ablation_results.json          # Real evaluation results (52 tasks)
├── held_out_traces.jsonl          # 52 real inference traces
│
├── synthesis_memos/
│   ├── memo_synthetic_data.md     # Liu et al. COLM 2024
│   ├── memo_datasheets_datacards.md # Gebru 2021 + Pushkarna FAccT 2022
│   ├── memo_contamination.md      # Chen et al. EMNLP 2025
│   ├── memo_llm_judge.md          # Gu et al. 2024–2025
│   ├── memo_dpo.md                # Rafailov et al. NeurIPS 2023
│   ├── memo_simpo_orpo.md         # Meng + Hong — algorithm choice justification
│   ├── memo_prometheus2.md        # Kim et al. 2024
│   └── memo_preference_leakage.md # Li et al. 2025
│
├── src/
│   ├── dataset/
│   │   ├── trace_restructurer.py
│   │   ├── probe_expander.py
│   │   ├── synthesizer.py
│   │   ├── contamination_check.py
│   │   └── partitioner.py
│   └── evaluation/
│       ├── scoring_evaluator.py   # Auto-grades any agent output
│       └── ablation_harness.py    # Bootstrap CI harness
│
├── tenacious_bench_v0.1/
│   ├── train/      # 159 DPO preference pairs
│   ├── dev/        # 57 preference pairs
│   └── held_out/   # 52 tasks — final evaluation partition
│
├── training/
│   ├── training_run_seed42.log    # Real T4 training log (60 steps)
│   └── loss_curve.png             # Real DPO loss curve
│
└── TRP1_week11_DPO_CORRECT.ipynb  # Reproducible Colab notebook
```

---

## Dataset Composition

| Source | Tasks | Share |
|--------|-------|-------|
| trace_derived | 72 | 30% |
| probe_expanded | 71 | 30% |
| llm_synthesized | 71 | 30% |
| hand_authored | 24 | 10% |
| **Total** | **238** | |

| Partition | Count | Purpose |
|-----------|-------|---------|
| train/ | 159 | DPO preference pairs |
| dev/ | 57 | Validation during training |
| held_out/ | 52 | Sealed evaluation partition |

---

## Scoring Rubric (Six Dimensions)

| Dimension | Weight | How Checked |
|-----------|--------|-------------|
| signal_confidence_compliance | 0.25 | Rule-based signal parsing |
| icp_segment_correctness | 0.20 | Keyword + reference classifier |
| bench_capacity_honesty | 0.20 | Regex + bench_summary.json |
| tone_compliance | 0.15 | LLM judge (different model family) |
| booking_link_present | 0.10 | Exact string match |
| banned_phrase_check | 0.10 | Case-insensitive search |

Inter-rater agreement: **Cohen's κ = 0.91** (30-task subset, 24h re-label protocol)

---

## Training (Path B — DPO)

| Setting | Value |
|---------|-------|
| Algorithm | DPO (Rafailov et al., NeurIPS 2023) |
| Base model | unsloth/Qwen3-1.7B |
| Quantization | None — 16-bit LoRA (fp16) |
| LoRA rank | r=16, alpha=32 |
| β | 0.1 |
| Training pairs | 159 |
| Steps | 60 (3 epochs, batch 8) |
| Hardware | Google Colab T4 (free) |
| Framework | Unsloth + TRL PatchDPOTrainer |

---

## Quick Start

```bash
git clone https://github.com/Meseretbolled/Sales-Agent-Evaluation-Bench.git
cd Sales-Agent-Evaluation-Bench
pip install -r requirements.txt

# Score an agent output against a task
python3 src/evaluation/scoring_evaluator.py \
  --task tenacious_bench_v0.1/dev/TB-HA-E-000.json \
  --output "Your agent output here"
```

---

## Week 10 Seed

| Metric | Value |
|--------|-------|
| Total traces | 149 |
| Adversarial probes | 30 |
| Failure taxonomy categories | 10 |

Source: [github.com/Meseretbolled/conversion-engine](https://github.com/Meseretbolled/conversion-engine)

---

## Status

- [x] Act I — Audit memo, schema, scoring evaluator
- [x] Act II — 238 tasks, contamination checks, partitioned, datasheet
- [x] Act III — Path B declared, 159 DPO pairs, methodology_rationale
- [x] Act IV — DPO training on Colab T4, Delta A +0.1904 (p=0.0000)
- [x] Act V — Model on HuggingFace, community engagement (τ²-Bench issue), blog post published

---

## Blog Post

[Why Your Sales Agent Fails in Ways No Benchmark Can See — And What I Built to Fix It](https://medium.com/@meseretbolled/why-your-sales-agent-fails-in-ways-no-benchmark-can-see-and-what-i-built-to-fix-it-73d7e41ada7d)

---

## Author

Meseret Bolled — [github.com/Meseretbolled](https://github.com/Meseretbolled)
