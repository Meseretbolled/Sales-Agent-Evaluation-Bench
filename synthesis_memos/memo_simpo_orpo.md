---
title: Synthesis Memo — SimPO and ORPO (Path B algorithm choice)
papers:
  - "SimPO: Simple Preference Optimization with a Reference-Free Reward (Meng, Xia, and Chen, NeurIPS 2024)"
  - "ORPO: Monolithic Preference Optimization without Reference Model (Hong, Lee, and Thorne, EMNLP 2024)"
author: Meseret Bolled
path: B (DPO)
---

## Core Arguments

**SimPO** replaces DPO's reference-model log-probability ratio with the average log-probability of the sequence itself, eliminating the need for a frozen reference model. It adds a margin hyperparameter γ that enforces a minimum gap between chosen and rejected rewards. Meng et al. show SimPO matches or beats DPO on AlpacaEval and MT-Bench at lower memory cost.

**ORPO** goes further: it combines the standard language modeling (SFT) loss with an odds-ratio preference loss in a single training pass. No reference model, no separate SFT phase. Hong et al. demonstrate competitive alignment at 1–2B scale with half the training steps.

## Why I Chose DPO Anyway

Both papers' memory argument — that eliminating the reference model saves VRAM — does **not apply at our scale**. With `ref_model=None` in TRL's `DPOTrainer`, the reference is computed from the initial model weights via a frozen copy in gradient-checkpointed mode. On a T4 with Qwen3-1.7B at fp16, this costs ~0.3 GB extra — negligible against the 12 GB headroom we had after loading the LoRA adapter (3.55 GB used).

SimPO's margin hyperparameter γ is a **new tunable** with no established default for domain-specific short-text tasks. Our training set has 159 pairs. Ablating γ over even three values (0.3, 0.5, 1.0) would require three full runs — 35 min each — and we had one T4 session. DPO's β=0.1 is well-documented as the standard starting point for preference alignment at this scale (Rafailov et al. §4).

ORPO's single-pass design is compelling, but it requires the model to simultaneously learn to generate good outputs AND avoid bad ones from scratch — which assumes the base model needs SFT-level correction. Our base model (Qwen3-1.7B) already generates grammatical, coherent B2B emails. The failure mode is **policy compliance** (banned phrases, over-commitment, missing signal grounding), not generation quality. DPO, operating purely as a preference shift on top of a competent base, is the right tool.

## Where the Papers Are Right

SimPO's length normalization is a genuine fix for a real DPO failure mode: DPO tends to reward verbosity because longer chosen sequences accumulate higher log-probability. Our held-out traces show the trained model's outputs averaging 187 words vs. the base model's 143 words — a 31% length increase that is likely partially attributable to this bias. A production re-run with SimPO's average log-probability reward would be worth testing to check whether the length inflation affects downstream reply rates.

## Summary

DPO was the right choice for this run: established β default, Unsloth PatchDPOTrainer support, no new hyperparameters to tune, and the memory argument for SimPO/ORPO doesn't apply at our VRAM headroom. The unresolved concern is length inflation — a SimPO re-run is the recommended next experiment.

**Word count: 418**
