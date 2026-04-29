"""
src/dataset/synthesizer.py
Tenacious-Bench — Multi-LLM Task Synthesizer

Generates ~100 additional tasks using DeepSeek via OpenRouter.
Key rule: the model that GENERATES tasks must be different from
the model that JUDGES them (Li et al., 2025 — preference leakage).

Generation model:  deepseek/deepseek-chat  (cheap, fast)
Judge model:       qwen/qwen3-next-80b     (different family)

Usage:
    python src/dataset/synthesizer.py \
        --output-dir tenacious_bench_v0.1/ \
        --seed-dir ../conversion-engine/seed/ \
        --count 100 \
        --openrouter-key YOUR_KEY

Author: Meseret Bolled
"""

import json
import os
import random
import argparse
import logging
import time
from pathlib import Path
from datetime import datetime

import requests

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
GENERATE_MODEL = "deepseek/deepseek-chat"
JUDGE_MODEL    = "qwen/qwen3-next-80b-a3b-instruct"
BOOKING_URL    = "https://cal.com/meseret-bolled-pxprep/tenacious-discovery-call"

DEFAULT_BENCH = {
    "python": 7, "go": 3, "data": 9,
    "ml": 5, "infra": 4, "frontend": 6, "fullstack_nestjs": 2,
}

# ── Seed templates for generation ────────────────────────────────────────────

GENERATION_SEEDS = [
    {
        "segment": "segment_2_mid_market_restructure",
        "difficulty": "hard",
        "scenario": "Company had layoff 60 days ago (high confidence). AI maturity score=1, confidence=low. Agent must assert layoff, use ask language for AI maturity.",
        "dimensions": ["signal_confidence_compliance", "icp_segment_correctness", "booking_link_present", "banned_phrase_check"],
    },
    {
        "segment": "segment_3_leadership_transition",
        "difficulty": "hard",
        "scenario": "New CTO appointed 30 days ago (high confidence) AND layoff 90 days ago. Agent must pitch leadership transition NOT cost reduction.",
        "dimensions": ["signal_confidence_compliance", "icp_segment_correctness", "booking_link_present"],
    },
    {
        "segment": "segment_1_series_a_b",
        "difficulty": "medium",
        "scenario": "Company closed Series B 60 days ago (high confidence). No layoff. Agent must pitch growth scaling.",
        "dimensions": ["signal_confidence_compliance", "icp_segment_correctness", "booking_link_present", "banned_phrase_check"],
    },
    {
        "segment": "segment_4_specialized_capability",
        "difficulty": "medium",
        "scenario": "AI maturity score=2 (medium confidence). No layoff or funding. Agent must use observe language for AI maturity.",
        "dimensions": ["signal_confidence_compliance", "icp_segment_correctness", "booking_link_present"],
    },
    {
        "segment": "abstain",
        "difficulty": "hard",
        "scenario": "All signals low confidence. Agent must use fully exploratory language. No assertions at all.",
        "dimensions": ["signal_confidence_compliance", "icp_segment_correctness", "booking_link_present"],
    },
    {
        "segment": "segment_2_mid_market_restructure",
        "difficulty": "hard",
        "scenario": "Prospect asks for 15 engineers. Only 7 Python available. Agent must state honest capacity.",
        "dimensions": ["bench_capacity_honesty", "signal_confidence_compliance", "booking_link_present"],
    },
]

GENERATE_PROMPT = """You are building evaluation tasks for a B2B sales agent benchmark called Tenacious-Bench.

Generate ONE realistic Tenacious-Bench task as a JSON object.

SCENARIO: {scenario}
SEGMENT: {segment}
DIFFICULTY: {difficulty}

The task must follow this EXACT structure:
{{
  "company": "string — a real company name appropriate for this segment",
  "prospect_name": "string — a realistic full name",
  "prospect_title": "string — CTO, VP Engineering, or Head of Engineering",
  "layoff_signal": {{
    "within_120_days": boolean,
    "laid_off_count": integer or null,
    "percentage": number or null,
    "date": "YYYY-MM-DD" or null,
    "confidence": "high" | "medium" | "low"
  }},
  "funding_signal": {{
    "is_recent": boolean,
    "is_series_ab": boolean,
    "funding_type": string or null,
    "days_since_funding": integer or null,
    "confidence": "high" | "medium" | "low"
  }},
  "leadership_signal": {{
    "detected": boolean,
    "title": string or null,
    "within_90_days": boolean or null,
    "days_since_appointment": integer or null,
    "confidence": "high" | "medium" | "low"
  }},
  "ai_maturity": {{
    "score": 0-3,
    "raw_score": number,
    "confidence": "high" | "medium" | "low",
    "phrasing_mode": "omit" | "ask" | "observe" | "assert",
    "summary": "string"
  }},
  "job_signal": {{
    "total_open_roles": integer,
    "ai_roles": integer,
    "confidence": "high" | "medium" | "low"
  }},
  "conversation_history": [],
  "scoring_notes": "string — what the agent must do correctly to pass"
}}

Return ONLY the JSON object. No markdown. No explanation."""

JUDGE_PROMPT = """You are a strict quality judge for Tenacious-Bench evaluation tasks.

Review this task and score it on 4 criteria. Return ONLY JSON.

TASK:
{task}

CRITERIA:
1. signal_consistency (0/1): Are signal confidence levels internally consistent? Low-confidence signals should not have specific verified data.
2. segment_alignment (0/1): Does the segment match the signals? Leadership signal → Segment 3. Layoff high-conf → Segment 2. etc.
3. rubric_clarity (0/1): Is the scoring_notes field specific enough to grade an agent output objectively?
4. realistic_inputs (0/1): Are company/prospect names and signal values realistic for a real B2B scenario?

Return ONLY:
{{"signal_consistency": 0, "segment_alignment": 0, "rubric_clarity": 0, "realistic_inputs": 0, "total": 0, "accept": false}}"""


def call_openrouter(
    prompt: str,
    model: str,
    api_key: str,
    temperature: float = 0.7,
    max_tokens: int = 1000,
) -> str:
    """Call OpenRouter API and return text response."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    try:
        resp = requests.post(OPENROUTER_URL, headers=headers,
                             json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.error(f"OpenRouter call failed: {e}")
        return ""


def parse_json_response(text: str) -> dict:
    """Parse JSON from LLM response, stripping markdown if present."""
    text = text.strip()
    # Remove markdown code blocks
    import re
    text = re.sub(r"```json|```", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON object in text
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except Exception:
                pass
    return {}


def generate_task(
    seed: dict,
    task_counter: int,
    api_key: str,
    bench_state: dict,
) -> dict:
    """Generate one task using the generation model."""
    prompt = GENERATE_PROMPT.format(
        scenario=seed["scenario"],
        segment=seed["segment"],
        difficulty=seed["difficulty"],
    )
    raw = call_openrouter(prompt, GENERATE_MODEL, api_key, temperature=0.8)
    if not raw:
        return {}

    data = parse_json_response(raw)
    if not data:
        return {}

    diff_code = {"easy": "E", "medium": "M", "hard": "H"}[seed["difficulty"]]
    task_id = f"TB-SY-{diff_code}-{task_counter:03d}"

    return {
        "task_id": task_id,
        "version": "0.1.0",
        "source_mode": "llm_synthesized",
        "difficulty": seed["difficulty"],
        "segment_under_test": seed["segment"],
        "dimensions_under_test": seed["dimensions"],
        "week10_trace_ref": None,
        "week10_probe_ref": None,
        "authoring_notes": (
            f"Generated by {GENERATE_MODEL}, judged by {JUDGE_MODEL}. "
            f"Seed scenario: {seed['scenario'][:80]}..."
        ),
        "input": {
            "hiring_signal_brief": {
                "company": data.get("company", "Unknown"),
                "generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "layoff_signal": data.get("layoff_signal", {}),
                "funding_signal": data.get("funding_signal", {}),
                "leadership_signal": data.get("leadership_signal", {}),
                "ai_maturity": data.get("ai_maturity", {}),
                "job_signal": data.get("job_signal", {}),
            },
            "bench_state": bench_state,
            "prospect_context": {
                "name": data.get("prospect_name", "Alex Chen"),
                "title": data.get("prospect_title", "CTO"),
                "company": data.get("company", "Unknown"),
                "email": f"prospect@{data.get('company', 'company').lower().replace(' ', '')}.com",
            },
            "conversation_history": data.get("conversation_history", []),
        },
        "expected_rubric": {
            "signal_confidence_compliance": True,
            "icp_segment_correctness": True,
            "bench_capacity_honesty": True,
            "tone_compliance_min": 4,
            "booking_link_present": True,
            "banned_phrase_check": True,
            "overall_pass": True,
        },
        "ground_truth_segment": seed["segment"],
        "scoring_notes": data.get("scoring_notes", ""),
        "_generation_model": GENERATE_MODEL,
        "_judge_model": JUDGE_MODEL,
    }


def judge_task(task: dict, api_key: str) -> bool:
    """
    Judge a generated task for quality.
    Returns True if task passes (score >= 3/4).
    Uses a DIFFERENT model family from the generator to prevent preference leakage.
    """
    task_preview = json.dumps({
        "segment": task.get("segment_under_test"),
        "difficulty": task.get("difficulty"),
        "signals": task.get("input", {}).get("hiring_signal_brief", {}),
        "scoring_notes": task.get("scoring_notes", ""),
    }, indent=2)

    prompt = JUDGE_PROMPT.format(task=task_preview[:2000])
    raw = call_openrouter(prompt, JUDGE_MODEL, api_key, temperature=0.0, max_tokens=150)
    if not raw:
        return False

    result = parse_json_response(raw)
    total = result.get("total", 0)
    accepted = result.get("accept", False)

    logger.info(f"Judge score: {total}/4 — {'ACCEPT' if accepted else 'REJECT'}")
    return total >= 3 and accepted


def synthesize(
    output_dir: str,
    seed_dir: str,
    count: int,
    api_key: str,
    train_ratio: float = 0.7,
    seed: int = 42,
) -> dict:
    """
    Generate and judge `count` tasks using multi-LLM pipeline.

    Args:
        output_dir:  Root of tenacious_bench_v0.1/
        seed_dir:    Path to Week 10 seed/ directory
        count:       Target number of ACCEPTED tasks
        api_key:     OpenRouter API key
        train_ratio: Fraction going to train/
        seed:        Random seed

    Returns:
        Summary dict
    """
    rng = random.Random(seed)

    # Load bench state
    bench_path = Path(seed_dir) / "bench_summary.json"
    if bench_path.exists():
        data = json.loads(bench_path.read_text())
        stacks = data.get("stacks", {})
        bench_state = {k: v.get("available_engineers", 0) for k, v in stacks.items()}
    else:
        bench_state = DEFAULT_BENCH

    output_path = Path(output_dir)
    train_dir = output_path / "train"
    dev_dir   = output_path / "dev"
    train_dir.mkdir(parents=True, exist_ok=True)
    dev_dir.mkdir(parents=True, exist_ok=True)

    accepted = []
    rejected = 0
    attempts = 0
    max_attempts = count * 3  # allow 3x attempts to hit target

    seeds_cycle = GENERATION_SEEDS * (max_attempts // len(GENERATION_SEEDS) + 1)
    rng.shuffle(seeds_cycle)

    logger.info(f"Target: {count} accepted tasks | Max attempts: {max_attempts}")
    logger.info(f"Generator: {GENERATE_MODEL} | Judge: {JUDGE_MODEL}")

    for i, seed_item in enumerate(seeds_cycle[:max_attempts]):
        if len(accepted) >= count:
            break

        attempts += 1
        task_counter = 1000 + i  # offset from trace/probe task IDs

        logger.info(f"Attempt {attempts}: generating {seed_item['segment']} {seed_item['difficulty']}...")

        task = generate_task(seed_item, task_counter, api_key, bench_state)
        if not task:
            rejected += 1
            logger.warning("Generation failed — skipping")
            continue

        # Judge the task
        if judge_task(task, api_key):
            accepted.append(task)
            logger.info(f"Accepted: {task['task_id']} ({len(accepted)}/{count})")
        else:
            rejected += 1
            logger.info(f"Rejected task {task_counter}")

        # Rate limit — 1 second between calls
        time.sleep(1.0)

    # Shuffle and split
    rng.shuffle(accepted)
    split_idx = int(len(accepted) * train_ratio)
    train_tasks = accepted[:split_idx]
    dev_tasks   = accepted[split_idx:]

    # Save
    for task in train_tasks:
        (train_dir / f"{task['task_id']}.json").write_text(json.dumps(task, indent=2))
    for task in dev_tasks:
        (dev_dir / f"{task['task_id']}.json").write_text(json.dumps(task, indent=2))

    summary = {
        "target_count": count,
        "accepted": len(accepted),
        "rejected": rejected,
        "attempts": attempts,
        "acceptance_rate": round(len(accepted) / attempts, 3) if attempts > 0 else 0,
        "train_tasks": len(train_tasks),
        "dev_tasks": len(dev_tasks),
        "generator_model": GENERATE_MODEL,
        "judge_model": JUDGE_MODEL,
        "generated_at": datetime.utcnow().isoformat(),
    }

    logger.info(
        f"Done: {len(accepted)} accepted, {rejected} rejected "
        f"({summary['acceptance_rate']*100:.0f}% acceptance rate)"
    )
    return summary


def main():
    parser = argparse.ArgumentParser(description="Tenacious-Bench Multi-LLM Synthesizer")
    parser.add_argument("--output-dir", default="tenacious_bench_v0.1")
    parser.add_argument("--seed-dir",   default="../conversion-engine/seed")
    parser.add_argument("--count",      type=int, default=100,
                        help="Target number of accepted tasks to generate")
    parser.add_argument("--openrouter-key", default=None,
                        help="OpenRouter API key (or set OPENROUTER_API_KEY env var)")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    api_key = args.openrouter_key or os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        print("ERROR: Set --openrouter-key or OPENROUTER_API_KEY env var")
        return

    summary = synthesize(
        output_dir=args.output_dir,
        seed_dir=args.seed_dir,
        count=args.count,
        api_key=api_key,
        seed=args.seed,
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()