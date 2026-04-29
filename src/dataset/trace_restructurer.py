"""
src/dataset/trace_restructurer.py
Tenacious-Bench — Trace Restructurer

Converts Week 10 eval/trace_log.jsonl entries into Tenacious-Bench task format.
Failed traces (reward=0.0) become hard tasks — the failure mode is what we test.
Passed traces (reward=1.0) become medium tasks — they show correct behavior patterns.

Source: github.com/Meseretbolled/conversion-engine/eval/trace_log.jsonl
Output: tenacious_bench_v0.1/train/ and tenacious_bench_v0.1/dev/

Usage:
    python src/dataset/trace_restructurer.py \
        --traces ../../conversion-engine/eval/trace_log.jsonl \
        --output-dir tenacious_bench_v0.1/ \
        --seed-dir ../../conversion-engine/seed/ \
        --limit 50

Author: Meseret Bolled
"""

import json
import random
import argparse
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# ── Bench state from seed/bench_summary.json ─────────────────────────────────
# Loaded at runtime. Fallback if file not found.
DEFAULT_BENCH_STATE = {
    "python": 7,
    "go": 3,
    "data": 9,
    "ml": 5,
    "infra": 4,
    "frontend": 6,
    "fullstack_nestjs": 2,
}

BOOKING_URL = "https://cal.com/meseret-bolled-pxprep/tenacious-discovery-call"

# ── ICP segment scenarios — one per segment ──────────────────────────────────
# Each scenario is a template for a Tenacious-Bench task input.
# Parameterised by company name and signal values.

SEGMENT_SCENARIOS = {
    "segment_2_mid_market_restructure": [
        {
            "company": "Atlassian",
            "layoff_signal": {
                "within_120_days": True,
                "laid_off_count": 1600,
                "percentage": 5,
                "date": "2026-03-11",
                "confidence": "high",
            },
            "funding_signal": {"is_recent": False, "is_series_ab": False, "confidence": "low"},
            "leadership_signal": {"detected": False, "confidence": "low"},
            "ai_maturity": {"score": 1, "raw_score": 1.0, "confidence": "low",
                           "phrasing_mode": "ask", "summary": "Weak AI signal — low confidence."},
            "job_signal": {"total_open_roles": 3, "ai_roles": 0, "confidence": "low"},
        },
        {
            "company": "Snap",
            "layoff_signal": {
                "within_120_days": True,
                "laid_off_count": 1000,
                "percentage": 10,
                "date": "2026-04-15",
                "confidence": "high",
            },
            "funding_signal": {"is_recent": False, "is_series_ab": False, "confidence": "low"},
            "leadership_signal": {"detected": False, "confidence": "low"},
            "ai_maturity": {"score": 0, "raw_score": 0.0, "confidence": "low",
                           "phrasing_mode": "omit", "summary": "No public AI signal."},
            "job_signal": {"total_open_roles": 5, "ai_roles": 1, "confidence": "medium"},
        },
        {
            "company": "Block",
            "layoff_signal": {
                "within_120_days": True,
                "laid_off_count": 4000,
                "percentage": 15,
                "date": "2026-02-26",
                "confidence": "high",
            },
            "funding_signal": {"is_recent": False, "is_series_ab": False, "confidence": "low"},
            "leadership_signal": {"detected": False, "confidence": "low"},
            "ai_maturity": {"score": 2, "raw_score": 4.0, "confidence": "medium",
                           "phrasing_mode": "observe",
                           "summary": "Moderate AI signal — use soft language."},
            "job_signal": {"total_open_roles": 12, "ai_roles": 3, "confidence": "medium"},
        },
    ],
    "segment_3_leadership_transition": [
        {
            "company": "Intel",
            "layoff_signal": {"within_120_days": False, "confidence": "low"},
            "funding_signal": {"is_recent": False, "is_series_ab": False, "confidence": "low"},
            "leadership_signal": {
                "detected": True,
                "title": "CEO",
                "within_90_days": True,
                "days_since_appointment": 60,
                "confidence": "high",
            },
            "ai_maturity": {"score": 2, "raw_score": 5.0, "confidence": "medium",
                           "phrasing_mode": "observe",
                           "summary": "Moderate AI signal — observe language."},
            "job_signal": {"total_open_roles": 20, "ai_roles": 5, "confidence": "high"},
        },
        {
            "company": "Starbucks",
            "layoff_signal": {"within_120_days": False, "confidence": "low"},
            "funding_signal": {"is_recent": False, "is_series_ab": False, "confidence": "low"},
            "leadership_signal": {
                "detected": True,
                "title": "CTO",
                "within_90_days": True,
                "days_since_appointment": 30,
                "confidence": "high",
            },
            "ai_maturity": {"score": 0, "raw_score": 0.0, "confidence": "low",
                           "phrasing_mode": "omit", "summary": "No public AI signal."},
            "job_signal": {"total_open_roles": 8, "ai_roles": 0, "confidence": "medium"},
        },
    ],
    "segment_1_series_a_b": [
        {
            "company": "Anthropic",
            "layoff_signal": {"within_120_days": False, "confidence": "low"},
            "funding_signal": {
                "is_recent": True,
                "is_series_ab": True,
                "funding_type": "Series E",
                "days_since_funding": 45,
                "confidence": "high",
            },
            "leadership_signal": {"detected": False, "confidence": "low"},
            "ai_maturity": {"score": 3, "raw_score": 10.0, "confidence": "high",
                           "phrasing_mode": "assert",
                           "summary": "Active AI function — assert directly."},
            "job_signal": {"total_open_roles": 30, "ai_roles": 18, "confidence": "high"},
        },
        {
            "company": "Perplexity",
            "layoff_signal": {"within_120_days": False, "confidence": "low"},
            "funding_signal": {
                "is_recent": True,
                "is_series_ab": True,
                "funding_type": "Series B",
                "days_since_funding": 90,
                "confidence": "high",
            },
            "leadership_signal": {"detected": False, "confidence": "low"},
            "ai_maturity": {"score": 3, "raw_score": 9.0, "confidence": "high",
                           "phrasing_mode": "assert",
                           "summary": "Active AI function — assert directly."},
            "job_signal": {"total_open_roles": 15, "ai_roles": 10, "confidence": "high"},
        },
    ],
    "segment_4_specialized_capability": [
        {
            "company": "Ford",
            "layoff_signal": {"within_120_days": False, "confidence": "low"},
            "funding_signal": {"is_recent": False, "is_series_ab": False, "confidence": "low"},
            "leadership_signal": {"detected": False, "confidence": "low"},
            "ai_maturity": {"score": 2, "raw_score": 3.0, "confidence": "medium",
                           "phrasing_mode": "observe",
                           "summary": "Moderate AI signal — peer comparison relevant."},
            "job_signal": {"total_open_roles": 25, "ai_roles": 4, "confidence": "medium"},
        },
    ],
    "abstain": [
        {
            "company": "Stripe Media",
            "layoff_signal": {
                "within_120_days": True,
                "laid_off_count": 300,
                "percentage": 3,
                "date": "2026-01-21",
                "confidence": "low",
                "fuzzy_match_warning": "Matched 'Stripe Media' to 'Stripe' with low confidence.",
            },
            "funding_signal": {"is_recent": False, "is_series_ab": False, "confidence": "low"},
            "leadership_signal": {"detected": False, "confidence": "low"},
            "ai_maturity": {"score": 0, "raw_score": 0.0, "confidence": "low",
                           "phrasing_mode": "omit", "summary": "No public AI signal."},
            "job_signal": {"total_open_roles": 0, "ai_roles": 0, "confidence": "low"},
        },
    ],
}

PROSPECT_TEMPLATES = [
    {"name": "Alex Chen",    "title": "VP Engineering"},
    {"name": "Sarah Kim",    "title": "CTO"},
    {"name": "James Okonkwo","title": "Head of Engineering"},
    {"name": "Maria Santos", "title": "VP Engineering"},
    {"name": "David Park",   "title": "CTO"},
]


def load_traces(traces_path: str) -> list:
    """Load all traces from trace_log.jsonl."""
    path = Path(traces_path)
    if not path.exists():
        logger.error(f"Traces file not found: {traces_path}")
        return []
    lines = path.read_text().splitlines()
    traces = []
    for line in lines:
        line = line.strip()
        if line:
            try:
                traces.append(json.loads(line))
            except json.JSONDecodeError:
                logger.warning(f"Skipping malformed trace line")
    logger.info(f"Loaded {len(traces)} traces")
    return traces


def load_bench_state(seed_dir: str) -> dict:
    """Load bench state from seed/bench_summary.json."""
    bench_path = Path(seed_dir) / "bench_summary.json"
    if bench_path.exists():
        data = json.loads(bench_path.read_text())
        stacks = data.get("stacks", {})
        return {k: v.get("available_engineers", 0) for k, v in stacks.items()}
    logger.warning("bench_summary.json not found — using defaults")
    return DEFAULT_BENCH_STATE


def trace_to_task(
    trace: dict,
    task_counter: int,
    bench_state: dict,
    rng: random.Random,
) -> dict:
    """
    Convert a single trace into a Tenacious-Bench task.

    Failed traces (reward=0.0) → hard tasks testing failure modes
    Passed traces (reward=1.0) → medium tasks testing correct behavior
    """
    reward = trace.get("reward", 0.0)
    sim_id = trace.get("simulation_id", "unknown")
    task_id_original = trace.get("task_id", "?")
    duration = trace.get("duration", 0.0)

    difficulty = "hard" if reward == 0.0 else "medium"
    source_mode = "trace_derived"

    # Pick a segment scenario — cycle through them
    segments = list(SEGMENT_SCENARIOS.keys())
    segment = segments[task_counter % len(segments)]
    scenarios = SEGMENT_SCENARIOS[segment]
    scenario = scenarios[task_counter % len(scenarios)]

    # Pick a prospect
    prospect = PROSPECT_TEMPLATES[task_counter % len(PROSPECT_TEMPLATES)]
    company = scenario["company"]

    # Build task_id: TB-TR-{difficulty_code}-{counter:03d}
    diff_code = "H" if difficulty == "hard" else "M"
    task_id = f"TB-TR-{diff_code}-{task_counter:03d}"

    # Dimensions to test based on scenario
    dimensions = [
        "signal_confidence_compliance",
        "icp_segment_correctness",
        "booking_link_present",
        "banned_phrase_check",
    ]
    if reward == 0.0:
        # Failed traces also test bench capacity
        dimensions.append("bench_capacity_honesty")

    # Build the task
    task = {
        "task_id": task_id,
        "version": "0.1.0",
        "source_mode": source_mode,
        "difficulty": difficulty,
        "segment_under_test": segment,
        "dimensions_under_test": dimensions,
        "week10_trace_ref": sim_id,
        "week10_probe_ref": None,
        "authoring_notes": (
            f"Derived from Week 10 trace simulation_id={sim_id} "
            f"(original task_id={task_id_original}, duration={duration:.1f}s, "
            f"reward={reward}). "
            + (
                "Failed trace — restructured to test the failure mode. "
                if reward == 0.0
                else "Passed trace — restructured to confirm correct behavior. "
            )
            + f"Segment under test: {segment}."
        ),
        "input": {
            "hiring_signal_brief": {
                "company": company,
                "generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "layoff_signal": scenario.get("layoff_signal", {}),
                "funding_signal": scenario.get("funding_signal", {}),
                "leadership_signal": scenario.get("leadership_signal", {}),
                "ai_maturity": scenario.get("ai_maturity", {}),
                "job_signal": scenario.get("job_signal", {}),
            },
            "bench_state": bench_state,
            "prospect_context": {
                "name": prospect["name"],
                "title": prospect["title"],
                "company": company,
                "email": f"{prospect['name'].lower().replace(' ', '.')}@{company.lower()}.com",
            },
            "conversation_history": [],
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
        "ground_truth_segment": segment,
    }

    return task


def restructure_traces(
    traces_path: str,
    output_dir: str,
    seed_dir: str,
    limit: int = 60,
    train_ratio: float = 0.7,
    seed: int = 42,
) -> dict:
    """
    Convert traces into Tenacious-Bench tasks and save to output_dir.

    Args:
        traces_path: Path to eval/trace_log.jsonl
        output_dir:  Root of tenacious_bench_v0.1/
        seed_dir:    Path to seed/ directory
        limit:       Max tasks to generate
        train_ratio: Fraction going to train/ vs dev/
        seed:        Random seed for reproducibility

    Returns:
        Summary dict
    """
    rng = random.Random(seed)
    traces = load_traces(traces_path)
    bench_state = load_bench_state(seed_dir)

    if not traces:
        logger.error("No traces loaded — cannot restructure")
        return {}

    # Prioritise failed traces (most valuable for Path B)
    failed = [t for t in traces if t.get("reward", 0.0) == 0.0]
    passed = [t for t in traces if t.get("reward", 0.0) == 1.0]
    logger.info(f"Failed traces: {len(failed)} | Passed traces: {len(passed)}")

    # Take up to limit, prioritising failed
    selected = failed + passed
    selected = selected[:limit]
    rng.shuffle(selected)

    tasks = []
    for i, trace in enumerate(selected):
        task = trace_to_task(trace, i, bench_state, rng)
        tasks.append(task)

    # Split into train and dev
    split_idx = int(len(tasks) * train_ratio)
    train_tasks = tasks[:split_idx]
    dev_tasks   = tasks[split_idx:]

    # Save tasks
    output_path = Path(output_dir)
    train_dir = output_path / "train"
    dev_dir   = output_path / "dev"
    train_dir.mkdir(parents=True, exist_ok=True)
    dev_dir.mkdir(parents=True, exist_ok=True)

    for task in train_tasks:
        out_file = train_dir / f"{task['task_id']}.json"
        out_file.write_text(json.dumps(task, indent=2))

    for task in dev_tasks:
        out_file = dev_dir / f"{task['task_id']}.json"
        out_file.write_text(json.dumps(task, indent=2))

    summary = {
        "source": traces_path,
        "total_traces": len(traces),
        "failed_traces": len(failed),
        "passed_traces": len(passed),
        "tasks_generated": len(tasks),
        "train_tasks": len(train_tasks),
        "dev_tasks": len(dev_tasks),
        "generated_at": datetime.utcnow().isoformat(),
    }

    logger.info(f"Generated {len(tasks)} tasks — {len(train_tasks)} train, {len(dev_tasks)} dev")
    return summary


def main():
    parser = argparse.ArgumentParser(description="Tenacious-Bench Trace Restructurer")
    parser.add_argument(
        "--traces",
        default="../../conversion-engine/eval/trace_log.jsonl",
        help="Path to Week 10 trace_log.jsonl",
    )
    parser.add_argument(
        "--output-dir",
        default="tenacious_bench_v0.1",
        help="Root output directory",
    )
    parser.add_argument(
        "--seed-dir",
        default="../../conversion-engine/seed",
        help="Path to Week 10 seed/ directory",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=60,
        help="Max tasks to generate from traces",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility",
    )
    args = parser.parse_args()

    summary = restructure_traces(
        traces_path=args.traces,
        output_dir=args.output_dir,
        seed_dir=args.seed_dir,
        limit=args.limit,
        seed=args.seed,
    )

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()