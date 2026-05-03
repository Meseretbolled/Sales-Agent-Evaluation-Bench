---
title: Synthesis Memo — Datasheets for Datasets + Data Cards
papers:
  - "Datasheets for Datasets (Gebru et al., 2021)"
  - "Data Cards: Purposeful and Transparent Dataset Documentation (Pushkarna et al., FAccT 2022)"
author: Meseret Bolled
path: B (DPO)
---

## Core Argument

Gebru et al. propose a standardized questionnaire for dataset documentation covering seven sections: motivation, composition, collection process, preprocessing, uses, distribution, and maintenance. The underlying assumption is that dataset creators and downstream consumers are **different parties** — a research lab releases a dataset; practitioners download and use it. The datasheet bridges the information gap between them.

Pushkarna et al. extend this with **layered detail** (telescopic = executive summary, periscopic = practitioner-level, microscopic = full technical audit), arguing that a flat datasheet loses readers at the wrong abstraction level depending on their role.

## Where I Disagree

Gebru's "Intended Use" section asks: *"What tasks is the dataset intended to be used for?"* and *"Has the dataset been used for any tasks already?"* — framed as if the creator is handing off to an unknown consumer.

For Tenacious-Bench, **the creator is the consumer**. We built this dataset specifically to evaluate our own Week 10 conversion engine on Tenacious-specific failure modes. There is no third-party download scenario at launch. Gebru's framing forces an answer like "general B2B sales evaluation" when the true intended use is narrower: *auditing one agent on one company's outreach policy*.

This matters because it changes which warnings are load-bearing. Gebru's template warns about population bias for external generalization. For an internal audit dataset, the relevant warning is **distribution shift over time** — the Tenacious style guide changes quarterly, so tasks authored against v2 may not reflect v3 norms. That warning doesn't appear in Gebru's seven sections.

## How I Applied This

`datasheet.md` in this repo adds an eighth section not in Gebru's template: **Temporal Validity**. It states the style guide version (v2, dated April 2026) and flags that the held-out partition should be re-seeded when the guide is revised. Pushkarna's telescopic layer (executive summary) is the `README.md` summary; the microscopic layer is `schema.json` plus the per-task `scoring_notes` fields.

The one Pushkarna design choice I did **not** adopt: their "periscopic" layer includes fairness and demographic impact analysis. For a B2B outreach dataset where the prospect is a fictional company, demographic fairness analysis is not load-bearing — and completing it would have been documentation theater rather than a genuine quality signal.

**Word count: 342**
