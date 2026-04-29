# Methodology — Tenacious-Bench Training Path

**Author:** Meseret Bolled
**Date:** April 2026
**Repository:** github.com/Meseretbolled/tenacious-bench
**Week 10 Reference:** github.com/Meseretbolled/conversion-engine

---

## 1. Path Selection

### Chosen Path: Path B — Preference Optimization (SimPO / ORPO)

**Path B trains the model to distinguish correct outputs from incorrect ones using chosen/rejected pairs.**

The three available paths were:

| Path | Method | Fixes |
|---|---|---|
| A — SFT | Supervised fine-tuning on correct examples | Generation quality: tone drift, weak phrasing |
| B — DPO/SimPO/ORPO | Preference optimization from chosen/rejected pairs | Inconsistency: agent cannot detect when it is wrong |
| C — Process Reward Model | Step-level reward model on trajectories | Trajectory failures: locally correct steps compounding into bad endings |

### Justification from Week 10 Evidence

Three pieces of Week 10 evidence point to Path B:

**Evidence 1 — Write action precision (42% error rate)**
In the τ²-Bench evaluation (tenacious_method_v3, 30 tasks), the agent scored 56.7% pass@1. Analysis of the 13 failures — including sim_id=a553180f (task_id=11, reward=0.0, 82.6s), sim_id=89337dd1 (task_id=34, reward=0.0, 75.6s), and sim_id=ef2ad255 (task_id=66, reward=0.0, 89.3s) — showed that read actions succeeded at 88.2% but write actions failed at 42%. The agent correctly retrieved information but chose wrong parameters when committing. This is inconsistency — the agent does not reliably detect when its write action is wrong. Path B preference pairs train the model to prefer the correct parameter choice over the incorrect one.

**Evidence 2 — Signal over-claiming (Probe 26)**
Probe 26 demonstrated the agent asserting a low-confidence layoff signal. The company "Stripe Media" matched to "Stripe" with confidence=low in layoffs.fyi. The unpatched agent asserted the layoff directly. The bug was fixed in `icp_classifier.py` (added low-confidence disqualifier). But the failure mode — asserting unverified signals — recurred in other probes (5, 6, 7). The pattern is consistent: the agent does not detect when it is about to over-claim. Path B trains the model to prefer emails that omit low-confidence signals (chosen) over emails that assert them (rejected).

**Evidence 3 — ICP priority conflict (Probe 2)**
Probe 2 showed the agent classifying a company as Segment 2 when it should be Segment 3 — the layoff check ran before the leadership check. The bug was fixed in `_classify_from_raw()`. The underlying pattern: when two signals conflict, the agent does not reliably pick the correct priority. Path B preference pairs can encode the priority rule directly — correct segment classification (chosen) vs wrong classification (rejected).

### Why Not Path A

Path A (SFT) fixes generation quality. My Week 10 emails are already grounded and use correct tone markers. The style guide honesty constraints are working — the agent does not produce low-quality prose. Generation quality is not the bottleneck.

### Why Not Path C

Path C (Process Reward Model) requires step-level annotations — for each trajectory, each intermediate step must be labeled as good or bad. My 150 traces contain only final reward labels (0.0 or 1.0) and termination reason. They do not contain step-level annotations. Path C needs at minimum 500-1000 annotated trajectories to train a reliable PRM. With 150 traces and limited annotation capacity, Path C is not feasible this week.

---

## 2. Training Algorithm Selection

### Chosen Algorithm: SimPO (Simple Preference Optimization)

**SimPO** (Meng, Xia, and Chen, NeurIPS 2024) is reference-free — it does not require a reference model during training. This means it fits on Colab T4 (16GB VRAM) with a Qwen 3.5 2B backbone. Standard DPO requires loading both the training model and a frozen reference copy simultaneously, which doubles VRAM usage.

ORPO (Hong, Lee, and Thorne, EMNLP 2024) is an alternative — it combines SFT and preference optimization in one pass. If SimPO shows instability on the small dataset (< 150 training pairs), ORPO will be tried as a fallback.

---

## 3. Training Data Format

### Chosen/Rejected Pair Construction

Each training example is a pair:

```json
{
  "prompt": "<task input — hiring signal brief + prospect context>",
  "chosen": "<correct agent output — asserts only high-confidence signals, correct segment, no banned phrases, includes booking link>",
  "rejected": "<incorrect agent output — asserts low-confidence signal, or wrong segment, or over-commits bench>"
}
```

**Chosen examples come from:**
- Discovery transcripts in `seed/discovery_transcripts/` — 5 human-authored examples of correct outreach behavior
- Passed traces (reward=1.0) from `eval/trace_log.jsonl` — 109 examples
- Corrected probe outputs — the fixed versions of Probe 2, Probe 26, and Probe 5 bugs

**Rejected examples come from:**
- Failed traces (reward=0.0) from `eval/trace_log.jsonl` — 41 examples
- Pre-fix probe outputs — the buggy agent outputs before Week 10 bug fixes
- Synthesized bad outputs — DeepSeek-generated outputs that deliberately assert low-confidence signals or use banned phrases

### Rejection Policy

A rejected example must differ from its chosen pair on at least one rubric dimension. If chosen and rejected are too similar (cosine similarity > 0.7), the pair is discarded — the signal is too weak to train from.

---

## 4. Training Configuration

### Model

**Qwen 3.5 2B** via Unsloth on Google Colab T4 (free tier, 16GB VRAM).

Rationale: LIMA (Zhou et al., NeurIPS 2023) showed that 1,000 high-quality training examples on a small model outperform larger models trained on noisy data. With ~125 training tasks, the 2B model is the right size — large enough to generalise, small enough to avoid memorisation.

### LoRA Configuration

```python
r = 16              # rank — higher = more capacity, more VRAM
lora_alpha = 16     # scaling factor
lora_dropout = 0.05 # regularisation
target_modules = ["q_proj", "k_proj", "v_proj", "o_proj",
                  "gate_proj", "up_proj", "down_proj"]
bias = "none"
```

Rationale: rank 16 is the Unsloth recommendation for Qwen 3.5 with a small dataset. QLoRA 4-bit is not used — Unsloth Qwen 3.5 guide recommends 16-bit for datasets under 500 examples.

### Training Hyperparameters

```python
learning_rate = 2e-4       # standard for SimPO on small datasets
num_train_epochs = 1       # LIMA recommendation for < 200 examples
per_device_train_batch_size = 4
gradient_accumulation_steps = 4
warmup_ratio = 0.1
beta = 2.5                 # SimPO temperature parameter
gamma = 0.5                # SimPO length normalisation
max_seq_length = 2048
```

Rationale for 1 epoch: with 125 training pairs, more than 1-2 epochs risks memorisation. The validation loss on dev/ will be monitored — training stops if val loss begins rising.

### Overfitting Prevention

Three measures:
1. **Low epoch count** — 1 epoch, max 2
2. **Early stopping** — monitor dev/ loss every 50 steps, stop if rising for 2 consecutive checkpoints
3. **Low rank** — LoRA r=16 limits model capacity

---

## 5. Evaluation Protocol

### Baseline Score

Before training, run the unmodified Week 10 agent (tenacious_method_v3, qwen3-next-80b-instruct) against the held_out/ partition using `scoring_evaluator.py`. Record the pass rate per dimension. This is the pre-training baseline.

### Delta Measurement

After training, run the LoRA-adapted model against the same held_out/ partition. Record the pass rate per dimension.

```
Delta A = post-training pass rate − pre-training baseline pass rate
```

A positive Delta A on the target failure mode (signal confidence compliance) is the primary success criterion.

### Target Outcome

- Primary: signal_confidence_compliance pass rate improves by >= +10pp on held_out/
- Secondary: icp_segment_correctness pass rate improves by >= +5pp
- Constraint: tone_compliance and booking_link_present must not degrade

---

## 6. Contamination Check Results

Three checks run before sealing held_out/. Results recorded in `contamination_report.json`.

| Check | Method | Threshold | Result |
|---|---|---|---|
| N-gram overlap | 8-gram exact match | 0 shared 8-grams | Pending |
| Embedding similarity | TF-IDF cosine | < 0.85 | Pending |
| Time-shift verification | Layoff date check | Pre-April 2026 | Pending |

Results will be updated after the full dataset is generated and partitioned.

---

## 7. Cost Log Reference

All API charges are tracked in `cost_log.md`. The total API budget for dataset generation is $3-5. Training on Colab T4 is free. Held-out evaluation uses eval-tier model (Claude Sonnet 4.6) capped at $2-3.

---

## 8. References

- Rafailov et al. (2023). Direct Preference Optimization. NeurIPS 2023. arxiv.org/abs/2305.18290
- Meng, Xia, Chen (2024). SimPO: Simple Preference Optimization with a Reference-Free Reward. NeurIPS 2024. arxiv.org/abs/2405.14734
- Hong, Lee, Thorne (2024). ORPO: Monolithic Preference Optimization. EMNLP 2024. arxiv.org/abs/2403.07691
- Zhou et al. (2023). LIMA: Less Is More for Alignment. NeurIPS 2023. arxiv.org/abs/2305.11206
- Li et al. (2025). Preference Leakage: A Contamination Problem in LLM-as-a-Judge. arxiv.org/abs/2502.01534
- Liu et al. (2024). Best Practices and Lessons Learned on Synthetic Data. COLM 2024. arxiv.org/abs/2404.07503
- Chen et al. (2025). Recent Advances in LLM Benchmarks against Data Contamination. EMNLP 2025. arxiv.org/abs/2411.03923