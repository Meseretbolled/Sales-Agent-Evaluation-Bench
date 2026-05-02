# The Tenacious Agent: Killing Hallucinations in B2B Sales with DPO

## 1. The Gap: Why existing benchmarks fail for B2B Sales
General benchmarks like τ²-Bench or AgentBench test for logic, but they fail to capture the **nuance of B2B empathy**. In the real world, a sales agent that hallucinates a "team of 20 John Does" after a company just laid off 50% of its staff isn't just wrong—it's a reputation-killer. We identified a specialized gap: the inability of base models to handle "Signal-Aware" outreach under pressure.

## 2. The Audit Method: How we found the failures
Using the Week 10 seed traces, we applied "Adversarial Probing." We specifically targeted the model's ego. By asking for more resources than the agent's internal "bench" actually held, we forced the model into a Choice: **Logic (Truth) vs. Helpfulness (Hallucination)**. Base models chose the latter 100% of the time.

## 3. The Dataset: Building Tenacious-Bench v0.1
We built 136 clean, sealed tasks using the "Scenario Factory":
- **Multi-LLM Synthesis:** DeepSeek created the scenarios, and Qwen 3 (80B) judged the quality. 
- **Contamination Protocol:** We used a strict 8-gram sequence checker to reach 0.0% overlap between Train and Held-out sets, following the Chen et al. (2025) seal.
- **Signal Signatures:** We locked tasks by company+signal to prevent "logic leakage."

## 4. The Training Experiment: DPO on Qwen 2.5
We chose **Direct Preference Optimization (DPO)** on a Qwen 2.5-1.5B backbone. 
- **Path:** We bypassed Unsloth for a stable HF `trl` trainer on a T4 GPU.
- **The "Safet Mode":** We overcame hardware BFloat16 limitations by using targeted float32 computation for the 4-bit LoRA adapter.
- **Result:** After just 60 steps (3.5 epochs), the model stopped hallucinating names and adopted the "Tenacious" professional persona.

## 5. The Result: A 241% improvement
Our evaluation on the sealed 20% held-out set showed a massive delta. While the base model scored a 1.2/5 (Filing on tone and truth), the DPO-tuned agent reached a **4.1/5**. 
- **Delta B:** Training successfully beat prompt-engineering by "hardcoding" the jargon-free policy into the model weights, making it 15% more token-efficient.

## 6. What's Next?
The future of Tenacious-Bench is real-time signal integration. We’ve proven that we can train a model to be honest; now we just need it to be faster... [CONTINUE WITH YOUR OWN INSIGHTS]
