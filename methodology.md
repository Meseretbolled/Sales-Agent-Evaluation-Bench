# Methodology
## Tenacious-Bench v0.1 — Path Choice, Partitioning, and Contamination Protocol

**Author:** Meseret Bolled  
**Date:** Week 11  
**Repo:** github.com/Meseretbolled/Sales-Agent-Evaluation-Bench

---

## 1. Path Declaration

**Chosen path: Path B — DPO/SimPO preference-tuned judge or critic**

**Backbone:** Qwen/Qwen2.5-1.5B-Instruct  
**Algorithm:** Direct Preference Optimization (DPO)  
**Training tool:** HuggingFace TRL stable trainer (not Unsloth — see rationale below)

---

## 2. Path Justification from Week 10 Evidence

The challenge specification states that path choice must be justified against Week 10 evidence. Path B is the correct choice for the following reasons.

**The dominant failure mode in Week 10 was inconsistency, not raw quality.** The Week 10 conversion engine produced outputs that were sometimes correct and sometimes wrong on the same failure category without the agent being able to detect the difference. Specific evidence:

**Failure category: Signal Over-claiming (Probes 5–8, probe_library.md)**  
Trigger rate: 20–30% of outbound emails. The agent got this right when the outreach_composer.py honesty constraints were populated correctly, and wrong when they weren't — the same logical path, inconsistent execution. This is exactly the failure mode DPO addresses: training the model to prefer grounded outputs over confident hallucinations.

**Failure category: Bench Over-commitment (Probes 9–12, probe_library.md)**  
All 4 probes in this category are MANUAL — the agent cannot tell when it is over-committing. This is not a generation-quality failure (Path A); it is an inconsistency failure. The model needs to prefer "route to human" over "confirm capacity" when bench state doesn't support the request.

**Training data alignment:**  
The preferences_train.jsonl dataset contains 159 (prompt, chosen, rejected) pairs where:
- `chosen`: correct Tenacious-voice output grounded in the hiring signal
- `rejected`: a hallucinated, over-confident, or banned-phrase output for the same prompt

This preference structure is exactly what DPO is designed to learn from.

**Why not Path A (SFT)?**  
Path A would be appropriate if the failure mode were generation quality — the model producing grammatically poor or stylistically off outputs. The Week 10 evidence does not support this. The base model can produce fluent, professional email copy. It fails on consistency: sometimes hallucinating, sometimes not, for identical failure categories. SFT on correct examples alone would not address the inconsistency problem.

**Why not Path C (PRM)?**  
A process reward model requires multi-step traces with step-level annotations. The Week 10 conversion engine produces single-output email drafts, not multi-step reasoning chains. PRM is appropriate for mathematical reasoning or code generation where intermediate steps can be independently verified. It is not the right fit for single-output email generation.

---

## 3. Training Details

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Base model | Qwen/Qwen2.5-1.5B-Instruct | Fits Colab T4 (16GB VRAM) in 4-bit; small enough for cost-flat deployment |
| Algorithm | DPO (Rafailov et al., NeurIPS 2023) | Matches preference data structure; well-supported in TRL |
| LoRA rank | 16 | Standard for tone-style tasks; higher ranks overfit on 159 pairs |
| LoRA alpha | 32 | 2× rank — standard DPO recommendation |
| Target modules | q_proj, k_proj, v_proj, o_proj | Attention layers capture tone/style |
| Max seq length | 1024 | Sufficient for hiring_signal_brief + email output |
| Training steps | 60 (~3.5 epochs on 159 pairs) | Loss converges by step 40; verified in training_run.log |
| Learning rate | 1e-4 | Conservative; DPO is sensitive to LR overshoot |
| Beta (DPO) | 0.1 | Default; not tuned — dataset too small for beta search |
| Hardware | Colab T4 (free tier) | $0.00 cost |

**Why HF TRL stable trainer over Unsloth:**  
Unsloth optimizes for SFT throughput via manual backpropagation kernels. DPO requires access to the reference model log-probabilities, which Unsloth's kernel optimizations do not support cleanly on T4 hardware in 4-bit mode. Three initial attempts resulted in CUDA out-of-memory errors due to dual-model memory requirements (policy + reference). The HF TRL DPOTrainer with BFloat16 fallback to float32 for the LoRA computation layers resolved the memory issue with no training speed penalty at 60 steps.

---

## 4. Dataset Partitioning Protocol

**Total tasks: 238**  
**Partitions:** train (119, ~50%) / dev (67, ~28%) / held_out (52, ~22%)

**Partitioning method:** Stratified by `icp_segment` and `source_mode`. Each partition contains a proportional representation of all five ICP segments and all four source modes (trace_derived, probe_expanded, llm_synthesized, hand_authored, programmatic).

**Stratification rationale:** An unstratified random split risks placing all "abstain" tasks in train and no "abstain" tasks in held_out, which would make the held-out evaluation unrepresentative.

**Held-out sealing:** The held_out partition is:
- Stored in `tenacious_bench_v0.1/held_out/` which is listed in `.gitignore`
- Not referenced by any training or evaluation script until the final held-out evaluation pass
- Not used in any judge calibration or inter-rater agreement sampling
- Released only after the leaderboard is published

---

## 5. Contamination-Check Protocol

Three checks run before any task enters the held-out partition. Script: `src/dataset/contamination_check.py`. Results: `contamination_report.json`.

**Check 1: N-gram overlap**  
No held-out task may share an 8-gram sequence with any training task on the `input.hiring_signal_brief.company` + signal date fields. Threshold: 0 violations. Result: 0 violations (see contamination_report.json).

**Check 2: Embedding similarity**  
TF-IDF cosine similarity between any held-out task input and any training task input must be below 0.85. Result: 0 violations above threshold (see contamination_report.json).

**Check 3: Time-shift verification**  
All event dates in signal briefs are anchored to real events from before the April 1, 2026 cut-off. No synthetic future dates. Result: 0 time-shift warnings (see contamination_report.json).

**Preference leakage prevention (Li et al., 2025):**  
The model used to generate task candidates (DeepSeek deepseek-chat via OpenRouter) is never used as the judge. The judge model is Qwen qwen3-next-80b-a3b-instruct — a different model family. This rotation policy is enforced in `src/dataset/synthesizer.py` via the `GENERATE_MODEL` and `JUDGE_MODEL` constants.

---

## 6. Training Data Preparation

Training data format: DPO preference pairs `{prompt, chosen, rejected}` in JSONL.

- `prompt`: Full hiring_signal_brief + instruction passed to the agent
- `chosen`: Correct Tenacious-voice output (grounded, confidence-calibrated, no banned phrases)
- `rejected`: An output with at least one of: hallucinated signal, wrong phrasing posture, banned phrase, over-committed capacity

Preference pairs were generated in two ways:
1. **Trace-derived (from Week 10):** 53 pairs where `chosen` is the corrected version of a Week 10 trace output and `rejected` is the original failing output
2. **Synthesized (DeepSeek + Qwen judge):** 106 pairs generated by `src/dataset/prepare_training_data.py`

Training data was not used as judge calibration examples. The 30-task inter-rater agreement sample was drawn from `dev/` only.

---

## 7. Week 10 Trace IDs Used

The following Week 10 trace IDs from `trace_log.jsonl` were used as seeds for trace-derived tasks:

- Traces from companies: Block, Zapier, Figma, Atlassian, Snap, Stripe, Airbnb, HashiCorp (see evidence_graph.json for company → task_id mapping)
- Total trace-derived tasks: ~53 (22% of 238 total)
- Methodology: `src/dataset/trace_restructurer.py` parses the raw trace, extracts the (signal_brief, agent_output) pair, and generates a (prompt, chosen, rejected) triple where `rejected` is the base model output and `chosen` is the corrected version passing all 6 rubric dimensions.

---

## 8. Cost Discipline

Per the challenge specification, compute cost is a graded observable. Full charge log in `cost_log.md`.

| Phase | Model | Cost |
|-------|-------|------|
| Task synthesis (DeepSeek) | deepseek/deepseek-chat | ~$0.036 |
| Judge filtering (Qwen) | qwen/qwen3-next-80b | ~$0.023 |
| Training (Colab T4) | — | $0.00 |
| Held-out eval (TMC judge) | claude-sonnet-4-5 (eval tier only) | ~$1.50 |
| **Total** | | **~$1.56 of $10.00 budget** |