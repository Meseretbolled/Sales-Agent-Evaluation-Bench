# Tenacious-Bench v0.1

**A Domain-Specific Evaluation Benchmark for B2B Sales Agents**

---

## 🚀 Overview

Tenacious-Bench is a **custom evaluation benchmark** designed to measure performance of LLM-powered sales agents in **real-world B2B outreach workflows**.

Unlike generic benchmarks, this dataset captures **failure modes unique to sales systems**, including:

* Weak signal grounding
* Over-commitment of bench capacity
* Tone drift from brand voice
* Generic or template-based outreach

This benchmark is built from **Week 10 agent traces**, **synthetic data pipelines**, and **adversarial task design**.

---

## 🎯 Key Contributions

* 📊 **200–300 task dataset** across multiple failure dimensions
* 🧠 **LLM-as-a-judge scoring evaluator** (fully machine-verifiable)
* 🔄 **Multi-LLM synthesis pipeline** with judge filtering
* 🔒 **Contamination-resistant held-out split**
* 📄 **Full datasheet (Gebru + Pushkarna compliant)**

---

## 📂 Repository Structure

```
.
├── audit_memo.md
├── schema.json
├── src/
│   ├── dataset/
│   ├── evaluation/
│   └── training/
├── tenacious_bench_v0.1/
│   ├── train/
│   ├── dev/
│   └── held_out/
├── generation_scripts/
├── synthesis_memos/
├── methodology.md
├── methodology_rationale.md
├── datasheet.md
└── README.md
```

---

## 🧪 Dataset Composition

| Source Mode          | Share |
| -------------------- | ----- |
| Trace-derived        | ~30%  |
| Programmatic         | ~30%  |
| Multi-LLM synthesis  | ~25%  |
| Adversarial (manual) | ~15%  |

Each task includes:

* Structured input (prospect + signal brief)
* Candidate output
* Ground truth / constraints
* Scoring rubric

---

## ⚙️ Scoring Evaluator

The evaluator is **fully automated** and scores outputs on:

* Signal grounding
* Tone adherence
* Constraint satisfaction
* Structural correctness

Run:

```bash
python src/evaluation/scoring_evaluator.py
```

---

## 🧠 Methodology

We follow a **multi-LLM routed data construction pipeline**:

1. Generate seed tasks (frontier model)
2. Expand via parameterized templates
3. Generate variants (cheap LLMs)
4. Filter using LLM-as-a-judge
5. Deduplicate + contamination check

---

## 🔒 Contamination Prevention

* N-gram overlap < 8
* Embedding similarity < 0.85
* Time-shift validation for signals

---

## 📊 Evaluation

We measure:

* **Delta A:** Trained vs baseline
* **Delta B:** Trained vs prompt-only
* **Cost-quality tradeoff**

---

## 🛠 Setup

```bash
git clone <repo>
cd repo
pip install -r requirements.txt
```

---

## ▶️ Quickstart

Run evaluation on sample tasks:

```bash
python src/evaluation/scoring_evaluator.py --sample
```

---

## 📄 Datasheet

See `datasheet.md` for:

* Motivation
* Collection process
* Limitations
* Ethical considerations

---

## 📚 References

* Liu et al. (2024) — Synthetic Data
* Gebru et al. (2021) — Datasheets
* Chen et al. (2025) — Contamination
* Gu et al. — LLM-as-a-Judge

---

## 📌 Status

* [x] Audit + Schema
* [x] Dataset complete
* [ ] Training
* [ ] Evaluation
* [ ] Publication

---

## 🤝 Contributing

Contributions welcome for:

* New failure modes
* Additional adversarial tasks
* Improved scoring metrics

---

## 📜 License

CC-BY-4.0
