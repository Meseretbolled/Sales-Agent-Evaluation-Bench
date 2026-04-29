## Dataset Partitioning Protocol

The dataset is split as follows:

- Training: 50%
- Dev: 30%
- Held-out: 20%

### Stratification

Each partition is stratified across:
- Failure modes (signal grounding, qualification, trajectory)
- Source modes (trace, programmatic, synthesis, adversarial)

This ensures balanced representation and prevents skewed evaluation.

---

## Contamination Checks

### 1. N-gram Overlap

- Threshold: < 8-gram overlap
- Flagged pairs: 17
- Action:
  - 12 dropped
  - 5 manually rewritten

Final status: PASS

---

### 2. Embedding Similarity

- Threshold: cosine similarity < 0.85
- Flagged pairs: 23
- Action:
  - 15 dropped
  - 8 retained after manual review (distinct semantics)

Final status: PASS

---

### 3. Time-shift Validation

- All public signals (layoffs, hiring) verified against timestamped sources
- Placeholder signals removed

Final status: PASS

---

## Final Status

All contamination checks passed. Held-out partition is:
- Non-overlapping
- Distributionally distinct
- Sealed from training

---

## Justification Summary

This protocol follows:
- Chen et al. (2025) for contamination resistance
- Liu et al. (2024) for synthetic data quality control

and is grounded in observed Week 10 failure modes.