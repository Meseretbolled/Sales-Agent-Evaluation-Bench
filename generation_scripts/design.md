# Generation Pipeline Design

## 1. Multi-LLM Routing Policy

| Stage | Model Type | Purpose |
|------|------------|--------|
| Seed generation | Frontier (GPT/Claude) | High-quality hard tasks |
| Expansion | Cheap (Qwen / DeepSeek) | Variants + scaling |
| Judge filtering | Cheap judge | High-volume filtering |
| Calibration | Eval-tier model | 50-task spot check |

⚠️ Eval-tier models are NEVER used during bulk generation.

---

## 2. Judge Scoring Dimensions

Each task is scored on:

- Coherence (1–5)
- Verifiability (1–5)
- Rubric Clarity (1–5)

### Inclusion Threshold:
- Coherence ≥ 4
- Verifiability ≥ 4
- Rubric Clarity ≥ 4

Tasks failing any dimension are dropped.

---

## 3. Pairwise Deduplication Logic

When multiple synthesis paths generate similar tasks:

1. Compute embedding similarity
2. If similarity > 0.90:
   - Run pairwise judge comparison
   - Select task with:
     - Higher rubric clarity
     - Higher failure-mode diagnostic value

---

## 4. Source Mode Distribution

- Trace-derived: 30%
- Programmatic: 30%
- Multi-LLM synthesis: 25%
- Adversarial: 15%

Each task includes:
```json
"source_mode": "trace-derived"