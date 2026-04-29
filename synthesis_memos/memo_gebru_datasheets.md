# Synthesis Memo 2 — Gebru et al. (2021): Datasheets for Datasets

**Paper:** Datasheets for Datasets
**Authors:** Gebru et al.
**Venue:** Communications of the ACM, 2021
**ArXiv:** arxiv.org/abs/1803.09010
**Read by:** Meseret Bolled, April 2026
**Relevance:** Template for datasheet.md — required for HuggingFace publication and interim submission

---

## Core Argument

Gebru et al. argue that datasets are released without sufficient documentation, creating two problems. First, practitioners cannot make informed decisions about whether a dataset is appropriate for their use case. Second, harms from inappropriate dataset use are difficult to trace back to documentation failures because there is no documentation.

The paper proposes a standardised 7-section template: motivation, composition, collection, preprocessing, uses, distribution, maintenance. Each section contains specific questions the dataset creator must answer. The goal is not compliance theatre but genuine transparency — a datasheet should make it possible for a practitioner to decide independently whether to use the dataset.

---

## What the Template Required Me to Document

Working through the Gebru template for Tenacious-Bench revealed three things I had not planned to document:

**1. The domain specificity limitation.**
The template's "uses" section asks: "Is there anything about the composition that might impact future uses?" Answering this honestly required me to state that Tenacious-Bench is not suitable for evaluating general-purpose sales agents — the rubric is calibrated to Tenacious's specific ICP segments, pricing, and bench capacity. A practitioner using this benchmark for a different B2B context would get misleading results. I added this to the datasheet explicitly.

**2. The static signal data problem.**
The template's "maintenance" section asks about update frequency. Answering honestly required me to acknowledge that layoff dates and funding events are frozen at April 2026. The benchmark will become stale as companies change. This is documented in the datasheet under known limitations.

**3. The single-annotator reliability gap.**
The template's "collection" section asks about annotation process and quality control. Since I am both the author and the annotator, I cannot claim inter-rater reliability in the traditional sense. The 48-hour re-labeling protocol in `inter_rater_agreement.md` is a partial mitigation — it measures intra-rater consistency, not inter-rater agreement. This distinction is now explicit in the datasheet.

---

## Critical Engagement

Gebru et al. present the datasheet as a solution to documentation failures. I agree with the diagnosis but have a concern about the mechanism.

The 7-section template is long and detailed. For a small research benchmark like Tenacious-Bench (200-300 tasks, single researcher, 1-week timeline), completing the full template honestly takes several hours. The paper does not acknowledge the cost asymmetry — large organisations with legal and compliance teams can absorb this cost; individual researchers on tight timelines cannot.

The result in practice is that small researchers either skip the datasheet (defeating the purpose) or produce superficial compliance documents that check every box without providing real transparency. My datasheet.md attempts to be in the second category but I acknowledge it is not as detailed as the template intended for a production dataset.

**The more useful contribution** in the paper is not the template itself but the underlying principle: document what the data cannot do, not just what it can do. The limitations sections of my datasheet are the most honest and most useful parts — they took the same effort as the compliance sections but provide more real value to a practitioner.

---

## Pushkarna et al. (FAccT 2022) — Data Cards Extension

Pushkarna et al. extend Gebru with a three-level structure: telescopic (2-3 sentence summary), periscopic (section-level overview), microscopic (full detail). This maps well to the HuggingFace dataset card format where users see the telescopic summary first and can drill down.

I implemented all three levels in datasheet.md. The telescopic summary at the top is what will appear in the HuggingFace dataset card preview. The microscopic detail in the rubric dimensions table and inter-rater section is what a researcher reproducing the benchmark needs.

---

## What I Changed Based on This Paper

**Before reading:** datasheet.md was planned as a compliance document — answer the questions, move on.
**After reading:** Added the three limitations I had not planned to document (domain specificity, static signal data, single-annotator gap). Added the Pushkarna three-level structure. Made the "uses" and "maintenance" sections more honest about what the benchmark cannot do.