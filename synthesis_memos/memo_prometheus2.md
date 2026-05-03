---
title: Synthesis Memo — Prometheus 2
paper: "Prometheus 2: An Open Source Language Model Specialized in Evaluating Other Language Models (Kim et al., 2024)"
author: Meseret Bolled
path: B (DPO)
---

## Core Argument

Kim et al. train Prometheus 2 (7B and 8x7B variants) as a dedicated open-source judge by fine-tuning on a mixture of direct assessment and pairwise ranking preference data. The central claim is that a small model trained specifically to evaluate can match or exceed GPT-4-level judge quality on held-out rubrics, at a fraction of the cost. The key training insight: combining both assessment formats in a single training mixture produces a model that generalizes better than training on either format alone.

## Where I Disagree

Prometheus 2's architecture assumes the **rubric is the bottleneck**. The model is trained to apply arbitrary rubrics supplied at inference time. The paper's test rubrics are general (helpfulness, coherence, factuality) — domains where a 7B model already has strong priors.

For Tenacious-Bench, the rubric is **not** the bottleneck. The rubric itself is simple and mechanical: zero banned phrases, at least one hiring-signal reference, calendar link present, no over-commitment. A 7B judge applying this rubric doesn't need to understand the rubric — it needs to understand the **business context** embedded in the prospect's hiring signal brief. Trace `9f1bceea` failed not because the rubric was complex but because the model didn't recognize that referencing a Series B layoff as a buying signal violates Tenacious policy.

A Prometheus-style judge applied to our tasks would score the surface rubric correctly (no banned phrases ✓, has a calendar link ✓) while missing the policy violation. Our `scoring_evaluator.py` handles this by making the signal-grounding check **programmatic** — it literally checks whether the company name and at least one field from `hiring_signal_brief` appear in the output — rather than relying on a judge's policy comprehension.

## How I Applied This

Rather than training a Prometheus-style judge, I used Prometheus 2's core insight differently: **separate the easy checks from the hard ones**. The scoring evaluator gives 70% of the score to rule-based checks (banned phrases, signal mention, calendar link, no over-commitment) and only 30% to an LLM judge for tone scoring. This matches Prometheus 2's finding that structured rubric dimensions are more reliably evaluated than holistic quality — and it makes our evaluator reproducible without any model inference at all for the majority of the score.

The one Prometheus design I would adopt in a future iteration: their **feedback generation** training objective (model must also explain its score). Our current evaluator returns a weighted score with no explanation, which makes rubric debugging slow.

**Word count: 370**
