# Methodology
## Tenacious-Bench v0.1 — Path Choice, Partitioning, and Contamination Protocol

**Author:** Meseret Bolled  
**Date:** Week 11  
**Repo:** github.com/Meseretbolled/Sales-Agent-Evaluation-Bench

---

## 1. Path Declaration

**Chosen path: Path B — DPO/SimPO preference-tuned judge or critic**

**Backbone:** Qwen/Qwen2.5-1.5B-Instruct  
**Algorithm:** Direct Preference Optimization (DPO) as defined in **Rafailov et al. (§3.2, 2023)**.  
**Training tool:** HuggingFace TRL stable trainer (not Unsloth — see rationale below).

---

## 2. Path Justification from Week 10 Evidence

The challenge specification states that path choice must be justified against Week 10 evidence. Path B is the correct choice for the following reasons.

**The dominant failure mode in Week 10 was inconsistency, not raw quality.** Specific evidence from the following Week 10 trace IDs:
1. **9f1bceea-557f-4086-b5f0-ddebed571544**: Demonstrates failure to correctly calibrate signal confidence.
2. **3bb05cae-be14-405a-866c-7355eccde196**: Shows tone mirroring of aggressive prospect language.
3. **daa216a6-933f-4020-a5cc-796efad365fb**: Shows misclassification of a Series B layoff disqualifier.

**Failure category: Signal Over-claiming (Probes 5–8, probe_library.md)**  
Trigger rate: 20–30% of outbound emails. This is exactly the failure mode DPO addresses: training the model to prefer grounded outputs over confident hallucinations, leveraging the DPO objective (Rafailov et al. §3, Eq. 7).

**Failure category: Bench Over-commitment (Probes 9–12, probe_library.md)**  
The agent cannot tell when it is over-committing. The model needs to prefer "route to human" over "confirm capacity" when bench state doesn't support the request.

---

## 3. Training Details

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Base model | Qwen/Qwen2.5-1.5B-Instruct | Fits Colab T4 (16GB VRAM) in 4-bit |
| Algorithm | DPO (Rafailov et al., §3.2, 2023) | Matches preference data structure |
| LoRA rank | 16 | Standard for tone-style tasks |
| Learning rate | 1e-4 | Conservative; avoids LR overshoot |
| Beta (DPO) | 0.1 | Default KL-divergence penalty |

---

## 4. Dataset Partitioning Protocol

**Total tasks: 238**  
**Partitions:** train (119, ~50%) / dev (67, ~28%) / held_out (52, ~22%)

**Partitioning method:** Stratified by `icp_segment` and `source_mode`, following recommendations in **Gebru et al. (§3, 2021)** for balanced composition.

---

## 5. Contamination-Check Protocol

Three checks run before any task enters the held-out partition. Script: `src/dataset/contamination_check.py`. 

**Preference leakage prevention (Li et al., 2025):**  
The model used to generate task candidates is never used as the judge. This rotation policy is enforced in `src/dataset/synthesizer.py`.

---

## 6. Inter-Rater Agreement Protocol

Following **Pushkarna et al. (§4, 2022)**, we implemented a 24-hour gap self-agreement protocol.

**Protocol Steps:**
1. Annotate a sample of 30 tasks from the `dev/` partition.
2. Wait **24 hours** to minimize memory bias.
3. Re-annotate the same 30 tasks.
4. Calculate Cohen's Kappa ($k$) for each dimension.

### Post-Revision Agreement Table (Table 1)

| Dimension | Initial Kappa | Post-Revision Kappa | Action Taken |
|-----------|---------------|----------------------|--------------|
| Signal Confidence | 0.72 | **0.88** | Added "Ask" phrasing rules |
| Bench Capacity | 0.85 | **0.95** | Hard-coded integer extraction |
| Tone Markers | 0.64 | **0.82** | Refined TMC rubric definitions |
| **Combined** | 0.74 | **0.88** | |

---

## 7. Cost Discipline

| Phase | Model | Cost |
|-------|-------|------|
| Task synthesis | deepseek/deepseek-chat | ~$0.036 |
| Judge filtering | qwen/qwen3-next-80b | ~$0.023 |
| Training (Colab T4) | — | $0.00 |
| **Total** | | **~$1.56 of $10.00 budget** |