# 🏆 Tenacious-Bench: B2B Sales Agent Fine-Tuning 🚀

[![Hugging Face Model](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Model-blue)](https://huggingface.co/meseretbolled/Tenacious-Qwen-DPO-Stable)
[![Hugging Face Dataset](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Dataset-yellow)](https://huggingface.co/datasets/meseretbolled/tenacious-bench-v0.1)

## 📖 Project Overview
Tenacious-Bench is a specialized evaluation suite and fine-tuning pipeline designed to solve the **"Sales Hallucination"** problem in B2B AI agents. While base models struggle with empathetic outreach following layoffs, our "Tenacious" agent is trained to be signal-aware, support-focused, and 100% jargon-free.

---

## 📂 Project Structure
```text
tenacious-bench/
├── src/
│   ├── dataset/
│   │   ├── contamination_check.py   # Strict 8-gram sequence audit engine
│   │   ├── curate_dataset.py         # Signal-locked partitioning logic (50/30/20)
│   │   ├── prepare_training_data.py # DeepSeek-based preference pair generator
│   │   └── ...
│   ├── training/
│   │   └── dpo_train.py             # Stable HF LoRA trainer for Colab T4
│   └── eval/
│       └── heldout_eval.py          # Post-training grader (1-5 rubrics)
├── tenacious_bench_v0.1/            # THE DATASET (238 Sealed Tasks)
│   ├── train/                       # 119 training contexts
│   ├── dev/                         # 67 validation contexts
│   └── held_out/                    # 52 secret "Final Exam" contexts
├── .env                             # Configuration and API keys (PRIVATE)
├── DATASHEET.md                     # Academic data methodology
├── memo_to_ceo_cfo.md               # Business case for deployment
├── ablation_results.json            # Quantitative performance lift
└── held_out_traces.jsonl            # Raw inference results for submission
```

---

## 📊 The Benchmark: Tenacious-Bench v0.1
We built a "Sealed" benchmark of **238 High-Fidelity Tasks** using a multi-LLM synthesis pipeline.

- **Version:** 0.1.0
- **Total Tasks:** 238 (Clean, Sealed)
- **Domain:** B2B Sales (Empathy-driven outreach following layoffs/funding)
- **Partitions:** 
  - Train: 119 tasks
  - Dev (Validation): 67 tasks
  - Held-out (Sealed): 52 tasks

### 📈 Results (Delta A Analysis)
| Evaluation Criteria | Base Model (Qwen 1.5B) | Tenacious-Tuned (DPO) | Delta |
| :--- | :--- | :--- | :--- |
| **Hallucination Rate** | 100% (Fake names/stats) | **0.0%** (Grounded) | **-100%** |
| **Persona Compliance**| 1.2 / 5.0 | **4.1 / 5.0** | **+241%** |

---

## 🚀 How to Run the Pipeline

### 1. Prerequisites
Ensure you have Python 3.10+ and an **OpenRouter API Key** in your `.env` file.
```bash
pip install -r requirements.txt # (Transfomers, TRL, PEFT, Datasets)
```

### 2. Verify the Academic Seal
Before training, run the contamination audit to ensure 0.0% overlap between folders.
```bash
python3 src/dataset/contamination_check.py
```

### 3. Generate Preference Pairs
Transform the 136 contexts into "Chosen vs Rejected" pairs for DPO.
```bash
python3 src/dataset/prepare_training_data.py
```

### 4. Execute Fine-Tuning (Colab)
1. Upload `preferences_train.jsonl` and `src/training/dpo_train.py` to Google Colab.
2. Ensure you are using a **T4 GPU** or higher.
3. Run the training cell (Standard 60 steps for 3.5 epochs).

### 5. Final Evaluation
Run your fine-tuned model against the secret 17-task held-out set to generate your final report.
```bash
python3 src/eval/heldout_eval.py
```

---

## ⚖️ License
Open for academic and evaluation use under the Week 11 TRP1 protocol.

---