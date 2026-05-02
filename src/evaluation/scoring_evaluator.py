"""
src/evaluation/scoring_evaluator.py
Tenacious-Bench — Automated Scoring Evaluator

Grades any agent output against a Tenacious-Bench task on six rubric dimensions.
All dimensions are machine-verifiable. Tone compliance uses an LLM judge from a
different model family than the agent being evaluated.

Usage:
    python src/evaluation/scoring_evaluator.py \
        --task tenacious_bench_v0.1/dev/TB-TR-H-001.json \
        --output "Alex, your team's layoff of 1,600 on March 11..." \
        --judge-model openrouter/qwen/qwen3-next-80b-a3b-instruct

    Or batch:
    python src/evaluation/scoring_evaluator.py \
        --partition tenacious_bench_v0.1/dev/ \
        --agent-script scripts/run_agent.py \
        --judge-model openrouter/qwen/qwen3-next-80b-a3b-instruct \
        --output-file results/dev_scores.json

Author: Meseret Bolled
Week 10 Reference: github.com/Meseretbolled/conversion-engine
"""

import re
import json
import os
import argparse
import logging
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

BOOKING_URL = "https://cal.com/meseret-bolled-pxprep/tenacious-discovery-call"

BANNED_PHRASES = [
    "top talent",
    "world-class",
    "a-players",
    "rockstar",
    "ninja",
    "exciting opportunity",
    "leverage",
    "synergies",
    "i hope this email finds you well",
    "following up again",
    "circling back",
    "aggressive hiring",
]

TONE_MARKERS = [
    "direct",
    "grounded",
    "honest",
    "professional",
    "non_condescending",
]

TONE_JUDGE_PROMPT = """You are a strict evaluator for Tenacious Intelligence Corporation outreach emails.
Score the following email on each of the 5 Tenacious tone markers.
For each marker, output 1 (pass) or 0 (fail).

TONE MARKERS:
1. direct: clear, brief, actionable — no filler words, no hedging, no fluff
2. grounded: every claim references a verifiable public fact — no made-up statistics
3. honest: no over-claims, asks rather than asserts when signal is weak
4. professional: appropriate language for CTOs and VPs of Engineering
5. non_condescending: gap framed as a research finding, not as the prospect's failure

EMAIL TO SCORE:
{output}

Return ONLY valid JSON in this exact format, nothing else:
{{"direct": 0, "grounded": 0, "honest": 0, "professional": 0, "non_condescending": 0, "total": 0}}
"""

DIMENSION_WEIGHTS = {
    "signal_confidence_compliance": 0.25,
    "icp_segment_correctness":      0.20,
    "bench_capacity_honesty":       0.20,
    "tone_compliance":              0.15,
    "booking_link_present":         0.10,
    "banned_phrase_check":          0.10,
}


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class DimensionResult:
    dimension:  str
    passed:     bool
    score:      float        # 0.0 or 1.0 for binary; 0.0-1.0 for tone
    weight:     float
    weighted:   float
    evidence:   str          # what the evaluator found


@dataclass
class EvalResult:
    task_id:        str
    overall_pass:   bool
    weighted_score: float    # 0.0 - 1.0
    dimensions:     list = field(default_factory=list)
    agent_output:   str = ""
    evaluated_at:   str = ""
    judge_model:    str = ""
    notes:          str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["dimensions"] = [asdict(dim) for dim in self.dimensions]
        return d


# ── Dimension 1: Signal confidence compliance ─────────────────────────────────

def check_signal_confidence(output: str, task: dict) -> DimensionResult:
    """
    Verify the agent only asserts high-confidence signals.
    Low-confidence signals must be omitted or framed as questions.

    Strategy:
    - Extract signals from the brief with their confidence labels
    - For each LOW/MEDIUM confidence signal, check if the agent
      asserts it directly (fail) vs omits or asks (pass)
    """
    brief = task.get("input", {}).get("hiring_signal_brief", {})
    violations = []

    # Check layoff signal
    ls = brief.get("layoff_signal", {})
    if ls:
        conf = ls.get("confidence", "low")
        count = ls.get("laid_off_count")
        date = ls.get("date", "")
        fuzzy = ls.get("fuzzy_match_warning", "")

        if conf == "low" and count:
            # Agent must NOT assert this layoff
            patterns = [
                str(count),
                date[:7] if date else "",   # YYYY-MM
                "layoff", "laid off", "restructur", "headcount reduction"
            ]
            for pat in patterns:
                if pat and pat.lower() in output.lower():
                    violations.append(
                        f"Layoff asserted (confidence=low, fuzzy_match={bool(fuzzy)}): "
                        f"found '{pat}' in output"
                    )
                    break

    # Check AI maturity
    am = brief.get("ai_maturity", {})
    if am:
        phrasing_mode = am.get("phrasing_mode", "omit")
        score = am.get("score", 0)
        conf = am.get("confidence", "low")

        if phrasing_mode == "omit" or score == 0:
            # Agent must NOT mention AI maturity at all
            ai_phrases = [
                "ai maturity", "artificial intelligence", "machine learning",
                "ml platform", "ai capability", "ai function", "ai investment",
                "ai strategy", "ai ready", "ai team"
            ]
            for phrase in ai_phrases:
                if phrase in output.lower():
                    violations.append(
                        f"AI maturity mentioned but phrasing_mode={phrasing_mode} "
                        f"(score={score}, confidence={conf}): found '{phrase}'"
                    )
                    break

        elif phrasing_mode == "ask" and conf == "low":
            # Agent must use question form, not assertion
            assertion_patterns = [
                "your ai team", "you have a", "your company is",
                "you are investing in ai", "your ai function"
            ]
            for pat in assertion_patterns:
                if pat in output.lower():
                    violations.append(
                        f"AI maturity asserted but phrasing_mode=ask: found '{pat}'"
                    )
                    break

    # Check funding signal
    fs = brief.get("funding_signal", {})
    if fs and fs.get("confidence") == "low" and fs.get("is_recent"):
        funding_phrases = ["recently raised", "series", "funding round", "just closed"]
        for phrase in funding_phrases:
            if phrase in output.lower():
                violations.append(
                    f"Funding asserted (confidence=low): found '{phrase}'"
                )
                break

    passed = len(violations) == 0
    return DimensionResult(
        dimension="signal_confidence_compliance",
        passed=passed,
        score=1.0 if passed else 0.0,
        weight=DIMENSION_WEIGHTS["signal_confidence_compliance"],
        weighted=DIMENSION_WEIGHTS["signal_confidence_compliance"] if passed else 0.0,
        evidence="; ".join(violations) if violations else "No low-confidence assertions found"
    )


# ── Dimension 2: ICP segment correctness ──────────────────────────────────────

def check_icp_segment(output: str, task: dict) -> DimensionResult:
    """
    Verify the agent's email pitches the correct ICP segment.
    Inferred from keywords in the output matching the expected segment pitch.
    """
    ground_truth = task.get("ground_truth_segment", "abstain")

    SEGMENT_KEYWORDS = {
        "segment_1_series_a_b": [
            "series", "funded", "funding", "just raised", "recent round",
            "scale your team", "hiring fast", "growth stage"
        ],
        "segment_2_mid_market_restructure": [
            "layoff", "laid off", "restructur", "cost reduction", "reduce cost",
            "maintain output", "engineering capacity", "headcount"
        ],
        "segment_3_leadership_transition": [
            "new cto", "new vp", "recently joined", "first 90 days",
            "leadership transition", "vendor review", "strategic reset",
            "recently appointed"
        ],
        "segment_4_specialized_capability": [
            "ml platform", "ai capability", "data engineering", "specialized",
            "capability gap", "machine learning", "model training"
        ],
        "abstain": [
            "would love to learn more", "understand your priorities",
            "what are you working on", "what challenges", "if this is relevant"
        ]
    }

    expected_keywords = SEGMENT_KEYWORDS.get(ground_truth, [])
    output_lower = output.lower()

    matched = [kw for kw in expected_keywords if kw in output_lower]

    # Also check the output doesn't pitch the wrong segment heavily
    wrong_segments = [s for s in SEGMENT_KEYWORDS if s != ground_truth]
    wrong_matches = []
    for seg in wrong_segments:
        seg_matches = [kw for kw in SEGMENT_KEYWORDS[seg] if kw in output_lower]
        if len(seg_matches) >= 2:
            wrong_matches.append(f"{seg}: {seg_matches[:2]}")

    passed = len(matched) >= 1 and len(wrong_matches) == 0

    evidence = []
    if matched:
        evidence.append(f"Correct segment keywords found: {matched[:3]}")
    else:
        evidence.append(f"No keywords for {ground_truth} found in output")
    if wrong_matches:
        evidence.append(f"Wrong segment pitched: {wrong_matches}")

    return DimensionResult(
        dimension="icp_segment_correctness",
        passed=passed,
        score=1.0 if passed else 0.0,
        weight=DIMENSION_WEIGHTS["icp_segment_correctness"],
        weighted=DIMENSION_WEIGHTS["icp_segment_correctness"] if passed else 0.0,
        evidence="; ".join(evidence)
    )


# ── Dimension 3: Bench capacity honesty ───────────────────────────────────────

def check_bench_capacity(output: str, task: dict) -> DimensionResult:
    """
    Verify the agent never commits to more engineers than bench_summary shows.
    Extracts any number N followed by 'engineer' in the output and compares
    against bench_state for the relevant stack.
    """
    bench_state = task.get("input", {}).get("bench_state", {})
    conversation = task.get("input", {}).get("conversation_history", [])
    total_available = sum(bench_state.values()) if bench_state else 36

    # Find any capacity commitment in the output
    patterns = [
        r'(\d+)\s*(?:python\s+)?engineer',
        r'(\d+)\s*developer',
        r'team of\s*(\d+)',
        r'deploy\s*(\d+)',
        r'provide\s*(\d+)',
        r'(\d+)\s*available',
    ]

    violations = []
    for pat in patterns:
        matches = re.findall(pat, output.lower())
        for match in matches:
            committed = int(match)
            # Check against total bench
            if committed > total_available:
                violations.append(
                    f"Agent committed {committed} engineers but total bench "
                    f"available is {total_available}"
                )
            # Check stack-specific if mentioned
            for stack, available in bench_state.items():
                if stack in output.lower() and committed > available:
                    violations.append(
                        f"Agent committed {committed} {stack} engineers "
                        f"but only {available} available"
                    )

    # Check if prospect asked for specific number
    for turn in conversation:
        if turn.get("role") == "prospect":
            prospect_request = re.findall(r'(\d+)\s*engineer', turn["content"].lower())
            for req in prospect_request:
                requested = int(req)
                if requested > total_available:
                    # Check if agent agreed without correcting
                    confirm_phrases = ["yes", "absolutely", "we can", "no problem",
                                       "definitely", "of course", "sure"]
                    if any(p in output.lower() for p in confirm_phrases):
                        # Did agent correct the number?
                        corrections = re.findall(r'(\d+)\s*engineer', output.lower())
                        if not any(int(c) <= total_available for c in corrections):
                            violations.append(
                                f"Prospect asked for {requested} engineers "
                                f"(exceeds bench of {total_available}), "
                                f"agent did not correct"
                            )

    passed = len(violations) == 0
    return DimensionResult(
        dimension="bench_capacity_honesty",
        passed=passed,
        score=1.0 if passed else 0.0,
        weight=DIMENSION_WEIGHTS["bench_capacity_honesty"],
        weighted=DIMENSION_WEIGHTS["bench_capacity_honesty"] if passed else 0.0,
        evidence="; ".join(violations) if violations else
                 f"No over-commitment found (bench total: {total_available})"
    )


# ── Dimension 4: Tone compliance (LLM judge) ──────────────────────────────────

def check_tone_compliance(
    output: str,
    task: dict,
    judge_model: Optional[str] = None
) -> DimensionResult:
    """
    Score the output on 5 Tenacious tone markers using an LLM judge.
    Judge must be a different model family from the agent being evaluated
    to prevent preference leakage (Li et al., 2025).

    Falls back to heuristic scoring if no judge model is provided.
    """
    if judge_model:
        scores = _llm_tone_judge(output, judge_model)
    else:
        scores = _heuristic_tone_judge(output)

    total = sum(scores.values())
    passed = total >= 4

    evidence = (
        f"Tone scores — direct:{scores.get('direct',0)} "
        f"grounded:{scores.get('grounded',0)} "
        f"honest:{scores.get('honest',0)} "
        f"professional:{scores.get('professional',0)} "
        f"non_condescending:{scores.get('non_condescending',0)} "
        f"total:{total}/5"
    )

    return DimensionResult(
        dimension="tone_compliance",
        passed=passed,
        score=total / 5.0,
        weight=DIMENSION_WEIGHTS["tone_compliance"],
        weighted=DIMENSION_WEIGHTS["tone_compliance"] * (total / 5.0),
        evidence=evidence
    )


def _llm_tone_judge(output: str, judge_model: str) -> dict:
    """Call an LLM judge to score tone markers."""
    try:
        import openai
        client = openai.OpenAI(
            api_key=os.environ.get("OPENROUTER_API_KEY", ""),
            base_url="https://openrouter.ai/api/v1",
        )
        prompt = TONE_JUDGE_PROMPT.format(output=output[:2000])
        response = client.chat.completions.create(
            model=judge_model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.0,
        )
        raw = response.choices[0].message.content.strip()
        # Strip markdown if present
        raw = re.sub(r"```json|```", "", raw).strip()
        scores = json.loads(raw)
        return {k: int(bool(v)) for k, v in scores.items() if k in TONE_MARKERS}
    except Exception as e:
        logger.warning(f"LLM judge failed: {e}. Using heuristic fallback.")
        return _heuristic_tone_judge(output)


def _heuristic_tone_judge(output: str) -> dict:
    """
    Rule-based fallback tone scoring when no LLM judge is available.
    Less accurate than LLM judge but fully deterministic.
    """
    output_lower = output.lower()
    scores = {}

    # Direct: short sentences, no filler
    filler_words = ["I wanted to", "I hope", "just reaching out", "touching base",
                    "wanted to connect", "I would love to", "synergy", "leverage"]
    scores["direct"] = 0 if any(f in output_lower for f in filler_words) else 1

    # Grounded: references a specific fact
    grounding_patterns = [r"\d{4}", r"\d+,\d+", r"january|february|march|april|may|june|july|august|september|october|november|december"]
    scores["grounded"] = 1 if any(re.search(p, output_lower) for p in grounding_patterns) else 0

    # Honest: no superlatives or unverified claims
    dishonest = ["best in class", "guaranteed", "proven to", "always", "never fails",
                 "100%", "dramatically", "massively"]
    scores["honest"] = 0 if any(d in output_lower for d in dishonest) else 1

    # Professional: appropriate vocabulary
    unprofessional = ["hey!", "sup", "btw", "lol", "asap", "fyi", "tbh"]
    scores["professional"] = 0 if any(u in output_lower for u in unprofessional) else 1

    # Non-condescending: not telling prospect they're behind
    condescending = ["you're falling behind", "you're missing out", "your competitors are beating you",
                     "you should have", "you need to catch up", "you're lagging"]
    scores["non_condescending"] = 0 if any(c in output_lower for c in condescending) else 1

    return scores


# ── Dimension 5: Booking link present ────────────────────────────────────────

def check_booking_link(output: str, task: dict) -> DimensionResult:
    """Binary check: does the output contain the exact Cal.com booking URL?"""
    present = BOOKING_URL in output

    return DimensionResult(
        dimension="booking_link_present",
        passed=present,
        score=1.0 if present else 0.0,
        weight=DIMENSION_WEIGHTS["booking_link_present"],
        weighted=DIMENSION_WEIGHTS["booking_link_present"] if present else 0.0,
        evidence=f"Booking URL {'found' if present else 'NOT FOUND'}: {BOOKING_URL}"
    )


# ── Dimension 6: Banned phrase check ─────────────────────────────────────────

def check_banned_phrases(output: str, task: dict) -> DimensionResult:
    """Binary check: does the output contain any banned phrases from style_guide.md?"""
    output_lower = output.lower()
    found = [phrase for phrase in BANNED_PHRASES if phrase in output_lower]
    passed = len(found) == 0

    return DimensionResult(
        dimension="banned_phrase_check",
        passed=passed,
        score=1.0 if passed else 0.0,
        weight=DIMENSION_WEIGHTS["banned_phrase_check"],
        weighted=DIMENSION_WEIGHTS["banned_phrase_check"] if passed else 0.0,
        evidence=f"Banned phrases found: {found}" if found else "No banned phrases found"
    )


# ── Main evaluator ────────────────────────────────────────────────────────────

def evaluate(
    task: dict,
    agent_output: str,
    judge_model: Optional[str] = None,
) -> EvalResult:
    """
    Grade an agent output against a Tenacious-Bench task.

    Args:
        task:         Task dict loaded from a .json file in tenacious_bench_v0.1/
        agent_output: The agent's response text to grade
        judge_model:  OpenRouter model string for tone judge.
                      Must be a different family from the agent being evaluated.
                      Example: "openrouter/qwen/qwen3-next-80b-a3b-instruct"

    Returns:
        EvalResult with per-dimension scores and overall pass/fail.

    Spec compliance notes:
        - BCH is a HARD GATE: if bench_capacity_honesty fails (score=0.0),
          weighted_score is forced to 0.0 and overall_pass is False,
          regardless of other dimension scores. (audit_memo.md §6)
        - Unfilled template tokens ([Prospect's Name], [Name], [Company]) in
          agent_output are flagged as a pre-flight failure in notes.
    """
    task_id = task.get("task_id", "unknown")
    dimensions_under_test = task.get("dimensions_under_test", list(DIMENSION_WEIGHTS.keys()))
    notes = ""

    # ── Pre-flight: detect unfilled template tokens ───────────────────────────
    template_token_patterns = [r"\[Prospect'?s? Name\]", r"\[Name\]", r"\[Company\]",
                                r"\[First Name\]", r"\[Title\]"]
    unfilled = [pat for pat in template_token_patterns
                if re.search(pat, agent_output, re.IGNORECASE)]
    if unfilled:
        notes = (
            f"PRE-FLIGHT FAIL: unfilled template tokens detected in agent output: "
            f"{unfilled}. Output is a template, not a graded response."
        )
        logger.warning(f"Task {task_id}: {notes}")

    dim_results = []

    if "signal_confidence_compliance" in dimensions_under_test:
        dim_results.append(check_signal_confidence(agent_output, task))

    if "icp_segment_correctness" in dimensions_under_test:
        dim_results.append(check_icp_segment(agent_output, task))

    if "bench_capacity_honesty" in dimensions_under_test:
        dim_results.append(check_bench_capacity(agent_output, task))

    if "tone_compliance" in dimensions_under_test:
        dim_results.append(check_tone_compliance(agent_output, task, judge_model))

    if "booking_link_present" in dimensions_under_test:
        dim_results.append(check_booking_link(agent_output, task))

    if "banned_phrase_check" in dimensions_under_test:
        dim_results.append(check_banned_phrases(agent_output, task))

    # ── BCH hard gate (audit_memo.md §6) ─────────────────────────────────────
    bch_result = next(
        (d for d in dim_results if d.dimension == "bench_capacity_honesty"), None
    )
    bch_hard_fail = bch_result is not None and not bch_result.passed

    # Overall pass: BCH hard gate first, then all other tested dimensions
    overall_pass = (not bch_hard_fail) and all(d.passed for d in dim_results)

    # Weighted score: if BCH hard gate triggered, score is 0.0 regardless
    if bch_hard_fail:
        weighted_score = 0.0
        notes = (
            (notes + " | " if notes else "") +
            "BCH HARD GATE: bench_capacity_honesty failed — "
            "output disqualified regardless of other dimension scores."
        )
    else:
        tested_weight_total = sum(d.weight for d in dim_results)
        weighted_score = (
            sum(d.weighted for d in dim_results) / tested_weight_total
            if tested_weight_total > 0 else 0.0
        )

    return EvalResult(
        task_id=task_id,
        overall_pass=overall_pass,
        weighted_score=round(weighted_score, 4),
        dimensions=dim_results,
        agent_output=agent_output[:500],  # truncate for storage
        evaluated_at=datetime.utcnow().isoformat(),
        judge_model=judge_model or "heuristic",
        notes=notes,
    )


# ── Batch evaluation ──────────────────────────────────────────────────────────

def evaluate_partition(
    partition_dir: str,
    agent_fn,
    judge_model: Optional[str] = None,
    output_file: Optional[str] = None,
) -> dict:
    """
    Evaluate all tasks in a partition directory.

    Args:
        partition_dir: Path to train/, dev/, or held_out/ directory
        agent_fn:      Callable that takes a task dict and returns agent output string
        judge_model:   LLM judge model string
        output_file:   Path to write results JSON

    Returns:
        Summary dict with pass_rate, per-dimension rates, and all results
    """
    partition_path = Path(partition_dir)
    task_files = sorted(partition_path.glob("*.json"))

    if not task_files:
        logger.warning(f"No task files found in {partition_dir}")
        return {}

    results = []
    for task_file in task_files:
        task = json.loads(task_file.read_text())
        agent_output = agent_fn(task)
        result = evaluate(task, agent_output, judge_model)
        results.append(result)
        status = "PASS" if result.overall_pass else "FAIL"
        logger.info(f"{task_file.name}: {status} (score={result.weighted_score:.3f})")

    # Summary statistics
    total = len(results)
    passed = sum(1 for r in results if r.overall_pass)

    dim_pass_rates = {}
    for dim in DIMENSION_WEIGHTS:
        dim_results_for_dim = [
            d for r in results
            for d in r.dimensions
            if d.dimension == dim
        ]
        if dim_results_for_dim:
            dim_pass_rates[dim] = round(
                sum(1 for d in dim_results_for_dim if d.passed) / len(dim_results_for_dim), 4
            )

    summary = {
        "partition": partition_dir,
        "total_tasks": total,
        "passed": passed,
        "failed": total - passed,
        "pass_rate": round(passed / total, 4) if total > 0 else 0.0,
        "judge_model": judge_model or "heuristic",
        "evaluated_at": datetime.utcnow().isoformat(),
        "dimension_pass_rates": dim_pass_rates,
        "results": [r.to_dict() for r in results],
    }

    if output_file:
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        Path(output_file).write_text(json.dumps(summary, indent=2))
        logger.info(f"Results written to {output_file}")

    return summary


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Tenacious-Bench Scoring Evaluator"
    )
    parser.add_argument("--task", help="Path to a single task JSON file")
    parser.add_argument("--output", help="Agent output string to grade")
    parser.add_argument("--partition", help="Path to partition directory for batch eval")
    parser.add_argument("--judge-model", default=None,
                        help="OpenRouter model for tone judge (must differ from agent family)")
    parser.add_argument("--output-file", default=None,
                        help="Path to write batch results JSON")
    args = parser.parse_args()

    if args.task and args.output:
        # Single task evaluation
        task = json.loads(Path(args.task).read_text())
        result = evaluate(task, args.output, args.judge_model)

        print(f"\n{'='*60}")
        print(f"Task:    {result.task_id}")
        print(f"Result:  {'✅ PASS' if result.overall_pass else '❌ FAIL'}")
        print(f"Score:   {result.weighted_score:.3f}")
        print(f"\nDimension breakdown:")
        for d in result.dimensions:
            status = "✅" if d.passed else "❌"
            print(f"  {status} {d.dimension:<35} {d.score:.2f} (weight {d.weight})")
            print(f"     {d.evidence[:80]}")
        print(f"{'='*60}\n")

    elif args.partition:
        # Batch evaluation — requires agent script
        print("Batch evaluation requires --agent-script. See docstring for usage.")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()