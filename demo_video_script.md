# The "100/100" Video Script: Tenacious-Bench v0.1
**Duration: Max 6 Minutes | Author: Meseret Bolled**

---

## **Minute 1: The Benchmark Gap (Contrast)**
**[Screen: Show audit_memo.md]**
"Hi everyone. For Tenacious-Bench, I audited existing models against the specific pathologies of B2B sales. While benchmarks like **τ²-Bench retail** measure inventory accuracy, they miss the 'Honesty Gap.' In my Audit Memo, I contrast τ²-Bench with my framework: we don't just check search logic; we enforce a **BCH Hard-Gate** for bench-capacity honesty. I’ve grounded this in 8 specific Week 10 probes and 5 distinct traces showing signal over-claims."

---

## **Minute 2: Dataset & Datasheet (25 pts)**
**[Screen: Open Hugging Face & DATASHEET.md]**
"Moving to the Hugging Face hub, here is the `tenacious-bench-v0.1` folder. You can see the stratified partitions across train, dev, and held-out. In the **Datasheet**, I’ve implemented all **Gebru and Pushkarna** sections. Crucially, look at **Section 8: Limitations and Biases**. I’ve explicitly documented US-centric and Tech-sector biases and linked them to caveats in Section 5—Usage. This ensures anyone using the model knows exactly when it might fail."

---

## **Minute 3: End-to-End Scoring (25 pts)**
**[Screen: Open terminal with code ready]**
"Let’s see the evaluator in action. I’ll run my live demo script."

**[Action: Run command]**
`PYTHONPATH=. python3 src/demo_evaluator.py`

"Notice Test 1: the agent hallucinated capacity for 'Go' engineers. My evaluator caught it and triggered the **BCH Hard-Gate**, dropping the score to zero. In Test 2, you see a calibrated agent being honest, which scores a perfect 1.0. This isn't keyword matching; it's a proximity-based logic gate."

---

## **Minute 4: Ablation & Traceability (25 pts)**
**[Screen: Open ablation_results.json and held_out_traces.jsonl]**
"Results: my DPO-tuned model shows a **+58.1% absolute lift** over the Week 10 baseline. If you look at `ablation_results.json`, you see the numeric claim. Now, if I open `held_out_traces.jsonl`, we can trace that number directly back to the raw model output. This visible traceability is core to my methodology."

---

## **Minute 5: Public Hubs & Ethics (15 pts)**
**[Screen: Show Medium Blog & GitHub Issue #292]**
"I’ve published a 1,600-word analysis on **Medium** detailing the DPO pivot. Also, I filed **Issue #292** on the official τ²-Bench repo to share results on bench-capacity pathologies. For my inter-rater agreement, I used a **24-hour gap** as specified by Pushkarna et al., achieving a post-revision Kappa of 0.91—proving this rubric is stable."

---

## **Minute 6: Path Rationale (10 pts)**
**[Screen: Show methodology.md]**
"Finally, why Path B? In `methodology.md`, I justify the DPO choice against Week 10 traces like `9f1bceea`, citing **Rafailov et al. (§3.2)**. DPO was the only way to fix inconsistency without losing fluency. Tenacious-Bench v0.1 is now live, sealed, and calibrated. Thank you."

---

### **Preparation Checklist:**
1.  **Command:** Have `PYTHONPATH=. python3 src/demo_evaluator.py` in your history.
2.  **File Path:** Have `audit_memo.md` and `methodology.md` open in VS Code.
3.  **Browser:** Tabs ready for HF Hub and Medium.
