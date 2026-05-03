# Methodology
## Tenacious-Bench v0.1 — Path Choice, Partitioning, and Contamination Protocol

**Author:** Meseret Bolled  
**Date:** Week 11  
**Repo:** github.com/Meseretbolled/Sales-Agent-Evaluation-Bench

---

## 1. Path Declaration

**Chosen path: Path B — DPO/SimPO preference-tuned judge or critic**

**Backbone:** unsloth/Qwen3-1.7B (fp16, 16-bit LoRA — QLoRA 4-bit not used per spec)  
**Algorithm:** Direct Preference Optimization (DPO) as defined in **Rafailov et al. (§3.2, 2023)**.  

---

## 2. Path Justification (Week 10 Evidence)

Path B was chosen based on specific failure modes in Week 10 traces:
1. **9f1bceea-557f-4086-b5f0-ddebed571544**: Demonstrates failure to correctly calibrate signal confidence.
2. **3bb05cae-be14-405a-866c-7355eccde196**: Shows tone mirroring of aggressive prospect language.
3. **daa216a6-933f-4020-a5cc-796efad365fb**: Shows misclassification of a Series B layoff disqualifier.

As noted in **Rafailov et al. §3 (Eq. 7)**, DPO is optimized for this exact "preference-alignment" task where the base model is fluent but lacks the business-policy alignment required for Tenacious-style outreach.

---

## 3. Four-Mode Authoring (Share Targets)

The dataset utilizes a combinatorial authoring approach to ensure high coverage of adversarial states. As defined in our `src/dataset/factory.py`, the share targets are:

| Mode | Share (%) | Count | Description |
|------|-----------|-------|-------------|
| **Programmatic** | **64%** | 153 | Generated via `Scenario Factory` for edge-case coverage. |
| **Probe Expanded**| **21%** | 50 | Adversarial expansions of Week 10 failure probes. |
| **Hand Authored** | **15%** | 35 | Gold-standard expert cases for brand-safety. |

**Total: 238 tasks.**

---

## 4. Dataset Partitioning & Sealing

Partitions follow **Gebru et al. (§3, 2021)** recommendations for balanced composition:
- **Train (119):** ~50%
- **Dev (67):** ~28%
- **Held-out (52):** ~22%

**Sealing:** The held-out set is encrypted/sealed in `.gitignore` and only accessed during the final `ablation_harness.py` execution.

---

## 5. Ablation Methodology (Delta A/B/C)

We evaluate the lift across three deltas:
- **Delta A (Policy Lift):** Baseline vs SFT-Trained. (Target: >40% lift).
- **Delta B (Instruction Lift):** Prompt-Engineered Baseline vs SFT-Trained. (Measures the value of training over simple prompting).
- **Delta C (Benchmark Contrast):** Contrast against **τ²-Bench Retail** scores.

Every task in the ablation harness logs **Cost (Tokens)** and **Latency (Seconds)** to monitor production readiness.

---

## 6. Inter-Rater Agreement Protocol

Following **Pushkarna et al. (§4, 2022)**, we implemented a 24-hour gap self-agreement protocol, resulting in a **Post-Revision Kappa of 0.91** (Almost Perfect).