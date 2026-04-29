# Synthesis Memo 1 — Liu et al. (2024): Best Practices and Lessons Learned on Synthetic Data

**Paper:** Best Practices and Lessons Learned on Synthetic Data for Language Models
**Authors:** Liu et al.
**Venue:** COLM 2024
**ArXiv:** arxiv.org/abs/2404.07503
**Read by:** Meseret Bolled, April 2026
**Relevance:** Directly governs Tenacious-Bench dataset construction in Acts I and II

---

## Core Argument

Liu et al. make three central claims that directly shaped how I built Tenacious-Bench:

**1. Quality filters are more important than generation volume.**
The paper shows that generating 10,000 tasks and filtering to 1,000 high-quality ones consistently outperforms using all 10,000 unfiltered. The insight is counterintuitive — more data is not better if it introduces noise. This directly justified my judge-filter architecture: DeepSeek generates tasks, qwen3 judges them, and only tasks scoring 3/4 or higher enter the dataset.

**2. The generator and judge must be from different model families.**
Liu et al. document what they call "self-preference bias" — a model judging its own outputs will systematically rate them higher than a different model would. This is the same finding as Li et al. (2025) on preference leakage. My implementation uses deepseek/deepseek-chat as generator and qwen/qwen3-next-80b as judge — different architecture families — to prevent this.

**3. Diversity of seed templates matters more than quantity of generated tasks.**
The paper shows that generating many variants from few seeds produces a distribution collapse — the dataset covers only the modes the seed templates cover. This pushed me to use four authoring modes (trace-derived, probe-expanded, synthesized, hand-authored) rather than relying on synthesis alone.

---

## Critical Engagement

I agree with claims 1 and 3 but have a practical objection to claim 2 as applied to my situation.

The paper tests self-preference bias at scale — comparing GPT-4 judging GPT-4 outputs vs Claude judging them across thousands of tasks. At my scale (80 synthesized tasks), the variance from a single model judging its own outputs would likely be undetectable in the final pass rate. The contamination risk is real in principle but the practical impact at 80 tasks is low.

More importantly, the paper's recommendation assumes you can freely choose any judge model. In my case the judge model must be cheap enough to fit within a $3-5 budget. qwen3-next-80b at $0.60/M output tokens is already near the ceiling. If I had used a truly independent judge (Claude Sonnet 4.6 at $15/M output), the 80-task judge run would cost ~$0.72 — within budget but cutting into the eval-tier allocation.

The paper does not address the budget constraint regime. My mitigation — using different model families rather than different providers — is a reasonable approximation given the constraints.

---

## What I Changed Based on This Paper

**Before reading:** I planned to generate 200 tasks and use all of them.
**After reading:** I generate with a quality threshold (3/4 judge score). I use four source modes. I separate generator from judge at the model family level.

**Specific implementation change:** The judge prompt in `src/dataset/synthesizer.py` scores four criteria — signal_consistency, segment_alignment, rubric_clarity, realistic_inputs — directly inspired by Liu et al.'s multi-criteria filtering approach. Tasks must pass 3 of 4 to enter the dataset.

---

## One Finding I Disagree With

Liu et al. recommend against using real production traces as seed material, arguing they introduce distribution artifacts from the original task framing. For Tenacious-Bench, this recommendation is wrong to follow. My 41 failed traces are the most valuable data I have — they show exactly what the agent does wrong in production. Discarding them in favour of purely synthetic seeds would make the benchmark less grounded, not more. The domain mismatch (retail traces → B2B tasks) is a known limitation documented in the datasheet, not a contamination risk.