# Tenacious-Bench: B2B Sales Agent Evaluation Datasheet

## 1. Dataset Overview
- **Version:** 0.1.0
- **Total Tasks:** 238 (Clean, Sealed)
- **Domain:** B2B Sales (Empathy-driven outreach following layoffs/funding)
- **Partitions:** 
  - Train: 119 tasks
  - Dev (Validation): 67 tasks
  - Held-out (Sealed): 52 tasks

## 2. Authoring Modes
The dataset followed the Act II "Multi-LLM Synthesis" protocol:
1. **Hand-authored (15%):** Hard adversarial cases designed to trigger tone policy violations.
2. **Probe Expansion (40%):** Parametric variations of Week 10 failures applied to Fortune 500 companies.
3. **Programmatic Bulk (45%):** Synthetic scenarios varied via the "Scenario Factory" to ensure signal diversity.

## 3. Cleaning & Sealing (Chen et al., 2025 Protocol)
The dataset underwent three rounds of rigorous contamination audits:
- **8-Gram Overlap:** 0 sequence overlaps found across partitions.
- **Embedding Similarity:** No cross-partition cosine similarity above 0.85.
- **Time-Shift:** All event dates normalized to occur before the April 1, 2026 cutoff.

## 4. Maintenance & Legal
- **License:** Open for academic use for Week 11 TRP1 challenge.
- **Privacy:** All prospect emails and names are synthetic and programmatically generated.
