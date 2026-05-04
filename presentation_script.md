# Tenacious Intelligence — Founder & Client Presentation Script
**Duration:** 20–25 minutes  
**Format:** Live dashboard walkthrough  
**Audience:** Founders + potential clients (CTOs, VPs Engineering, Heads of Talent)

---

## BEFORE YOU START

Open the dashboard in your browser:
```bash
cd /home/meseret/Documents/tenacious-bench
python3 src/ui/run_dashboard.py
# → http://localhost:8008
```

Make it full-screen. Sidebar should be visible on the left.

---

## OPENING (2 min) — Overview page

**[Dashboard is on Overview page. Hero banner is visible.]**

> "Let me start with a question. How do you know if your AI sales agent is actually working — not just generating text, but sending emails that a VP of Engineering will actually respond to?"

> "Most companies answer that with vibes. They look at a few emails, say 'looks good', and ship it. The problem is: the failures are invisible until a prospect complains, or your reply rate quietly drops to zero."

> "We built Tenacious Intelligence to solve this. Not just the agent — the entire measurement and improvement system around it."

**[Point to the stat row: +25.4%, p=0.000, $0.067, 238 tasks, κ=0.91]**

> "These five numbers are the story of this week. We fine-tuned an AI model specifically on B2B outreach failures. We improved it by 25% on a held-out test set. We did it in 11 minutes of compute time. And it cost 6.7 cents."

> "I'll show you exactly how, and then I'll show you it running live."

---

## ACT 1 — THE PROBLEM (3 min) — Problem page

**[Click sidebar: The Problem]**

> "Before I show you the result, let me show you what we were measuring against."

**[Point to the left table: τ²-Bench]**

> "There's a benchmark called τ²-Bench that everyone in AI uses to evaluate agents. It's good at measuring whether an agent can look up the right product in a database. That's it. It has no concept of what kills a B2B email."

**[Point to the three problem cards]**

> "We identified three failure modes in our own production system — I'll show you the Langfuse trace IDs in a second. The first is signal hallucination: the agent says 'you're hiring aggressively' when the company has zero open roles. Instant trust destruction."

> "The second is over-commitment. The agent promises 10 engineers starting next month. We have 7. That's a legal problem, not an AI problem — except it came from the AI."

> "The third is tone. The agent starts with 'I hope this email finds you well.' That email goes straight to the bin. It's not just annoying — it signals that the message is automated, generic, and not worth reading."

**[Point to the trace table]**

> "These are real trace IDs from our Langfuse production logs. Not synthetic examples — actual failures in the system we shipped in Week 10."

---

## ACT 2 — THE SOLUTION (3 min) — Solution page

**[Click sidebar: Our Solution]**

> "So we built a benchmark specifically to catch these failures. 238 evaluation tasks, all grounded in those production failures."

**[Point to the rubric bars on the left]**

> "Six dimensions. The key insight is that 80% of the score is purely rule-based — regex, string match, keyword search. There's no expensive LLM judge involved for the majority of the score. That means we can run this evaluation on every single email, in production, at zero cost."

> "The remaining 20% is an LLM tone judge — and we deliberately used a different model family from the one that wrote the emails, to prevent what's called preference leakage."

**[Point to the dataset doughnut chart]**

> "The 238 tasks come from four sources: real production traces, probe variations, LLM-synthesised tasks, and hand-authored adversarial cases. We ran three contamination checks before training — no data leakage between training and the test set."

---

## ACT 3 — LIVE DEMO (5 min) — Demo page

**[Click sidebar: Score an Email]**

> "This is the part I want you to see live. This is the same scoring engine that runs in production."

**[Click "Good email" pill]**

> "This is an email our trained model would write. Watch the score."

**[Score appears: ~0.900+, green PASS ring]**

> "Signal grounding — it references Block's specific data. Booking link — the Cal.com URL is in the body. No banned phrases. This passes."

**[Click "Banned phrases" pill]**

> "Now watch this one."

**[Score appears: ~0.360, red FAIL ring, banned phrases appear in red chips]**

> "'Top talent', 'world-class', 'exciting opportunity', 'I hope this email finds you well' — all banned. Score 0.360. In our production system, this email never gets sent. The agent retries once, and if it fails again, it's blocked."

**[Click "Over-commitment" pill]**

> "This one is more dangerous. The email reads fine on the surface. But it promises unlimited capacity and guarantees a start date."

**[Point to BCH dot — red]**

> "Bench Capacity Honesty: red. The system caught it. A human reviewer might have missed it."

---

## ACT 4 — THE RESULTS (4 min) — Results page

**[Click sidebar: Delta A Results]**

> "So what did DPO training actually do to the model?"

**[Point to the three metric cards: +0.1904, [0.1115–0.2788], p=0.0000]**

> "19 percentage points absolute improvement. That's the delta between the base model and our fine-tuned version on 52 tasks the model had never seen. Statistical significance: p equals zero. We ran 10,000 bootstrap resamples and not a single one showed an improvement of zero or less."

**[Point to the scatter chart]**

> "Each dot is one task. Green dots — trained model scored higher than base. Almost every dot is green and above the diagonal. The base model had 5 tasks where it scored zero — catastrophic complete failures. The trained model: zero zeros."

**[Point to the bar chart]**

> "Look at Banned Phrases specifically — 88% for the base model, 100% for trained. The fine-tuning completely eliminated that failure mode."

---

## ACT 5 — COST (3 min) — Cost page

**[Click sidebar: Cost & ROI]**

**[Point to the $0.067 hero number]**

> "This is what I want founders to see. The entire project — benchmark construction, dataset synthesis, model training, evaluation — cost 6.7 cents. On a 10 dollar budget. 0.67 percent utilised."

**[Point to the daily spend chart]**

> "Days 1 and 4: zero dollars — all the hard work was coding and analysis, no API calls. Days 2 and 3: the synthesis runs. Days 5 and 6: training on Colab T4 and evaluation — also zero dollars."

**[Point to the ROI comparison table]**

> "Commercial fine-tuning services would charge 50 to 500 dollars for an equivalent improvement. We did it for 6.7 cents. That's a 750× cost advantage, at minimum."

> "And it scales. If you want 10,000 evaluation tasks instead of 238, that's $2.80 of synthesis cost. The training and evaluation stay at zero."

---

## ACT 6 — PRODUCTION PATH (2 min) — Pipeline page

**[Click sidebar: Outreach Pipeline]**

> "This is how the model connects to the live system. The pipeline is four steps: signal enrichment from public sources, ICP classification into four segments, email composition with the quality gate, and delivery through Resend email and Africa's Talking SMS."

**[Point to the quality gate section on the right]**

> "The quality gate is the Week 11 integration. Every email gets scored before it's sent. Score under 0.70, it retries automatically. If the retry also fails, it's blocked and logged to Langfuse. No bad email reaches a prospect."

> "The model adapter is already on HuggingFace. Swapping it into production is a one-line environment variable change in Render."

---

## ACT 7 — RISK CONTROLS (2 min) — Risk Controls page

**[Click sidebar: Risk Controls]**

> "One question every technical client asks: what happens when it breaks? The answer is: we defined that before we deployed."

**[Point to the trigger table]**

> "Seven named kill-switch conditions. Each one has a specific threshold, a detection mechanism — not a human check, an automated check — and a response time. Some are immediate. The longest is 24 hours."

**[Point to the rollback procedure]**

> "Rollback procedure is four steps. Step 1: change one environment variable in Render. Step 2: trigger a redeploy. Under 2 minutes total. The quality gate catches generation-level failures automatically. The kill switch is for anything that gets through."

---

## CLOSE (2 min) — Back to Overview

**[Click sidebar: Overview. Show the hero banner.]**

> "To summarise what you've just seen:"

> "We identified the failure modes that generic benchmarks can't see. We built a measurement system specifically for them. We fine-tuned a model that passes those tests — 25% better than the base model, statistically significant, for 6.7 cents."

> "The pipeline is live. The model is public on HuggingFace. The benchmark dataset is public on HuggingFace. Everything is reproducible."

> "What's next: a 30-prospect A/B test to measure reply rate, which is the business metric that actually matters. The benchmark tells us the model writes better emails. The A/B test will tell us whether better emails generate more revenue."

> "Questions?"

---

## COMMON QUESTIONS

**Q: Why not just use GPT-4 with a good prompt?**
> "Good question — that's actually our next experiment, called Delta B. Our honest position is that a well-tuned GPT-4o prompt would likely score around 0.85 on our benchmark. Our DPO model scores 0.941. So there's still a meaningful gap. But more importantly, the fine-tuned model is fully under our control, runs at lower latency, and costs nothing per evaluation because it doesn't call a paid API for the rule-based dimensions."

**Q: How do you know the benchmark is measuring the right things?**
> "Two answers. First, every rubric dimension traces directly back to a named production failure in our Langfuse traces — we didn't make these up. Second, Cohen's kappa of 0.91 on the rubric — that means if you re-label the same task independently, you get the same answer 91% of the time. That's 'almost perfect' on the standard scale."

**Q: What does this cost for a client to deploy?**
> "The evaluation infrastructure runs at $0.00 per email — it's all local. The quality gate adds roughly 50ms to the pipeline. The model adapter is a LoRA — it adds about 120ms inference overhead on CPU. Total cost to run this in production: zero ongoing API cost, slightly higher latency."

**Q: What if the model makes a mistake and an email still goes out?**
> "The kill switch table covers this. If banned phrase rate exceeds 2%, automatic rollback within 1 hour. If a prospect complains, immediate pause. And the rollback itself takes 2 minutes — it's a Render environment variable change."

---

## TIMING GUIDE

| Section | Page | Time |
|---------|------|------|
| Opening | Overview | 2 min |
| The Problem | Problem | 3 min |
| The Solution | Solution | 3 min |
| Live Demo | Demo | 5 min |
| Results | Results | 4 min |
| Cost | Cost | 3 min |
| Pipeline | Pipeline | 2 min |
| Risk Controls | Kill Switch | 2 min |
| Close + Q&A | Overview | 5 min |
| **Total** | | **~29 min** |

Trim to 20 min by cutting Pipeline to 1 min and skipping the detailed risk table — just show the rollback procedure.
