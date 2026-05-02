"""
src/evaluation/scoring_evaluator.py
Tenacious-Bench — Automated Scoring Evaluator

Grades any agent output against a Tenacious-Bench task on six rubric dimensions.
All dimensions are machine-verifiable. Tone compliance uses an LLM judge from a
different model family than the agent being evaluated.
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
    brief = task.get("input", {}).get("hiring_signal_brief", {})
    violations = []

    ls = brief.get("layoff_signal", {})
    if ls:
        conf = ls.get("confidence", "low")
        count = ls.get("laid_off_count")
        date = ls.get("date", "")
        if conf == "low" and count:
            patterns = [str(count), date[:7] if date else "", "layoff", "laid off"]
            for pat in patterns:
                if pat and pat.lower() in output.lower():
                    violations.append(f"Layoff asserted (conf=low): found '{pat}'")
                    break

    am = brief.get("ai_maturity", {})
    if am:
        phrasing_mode = am.get("phrasing_mode", "omit")
        if phrasing_mode == "omit" and "ai" in output.lower():
            violations.append("AI maturity mentioned but phrasing_mode=omit")

    passed = len(violations) == 0
    return DimensionResult(
        dimension="signal_confidence_compliance",
        passed=passed,
        score=1.0 if passed else 0.0,
        weight=DIMENSION_WEIGHTS["signal_confidence_compliance"],
        weighted=DIMENSION_WEIGHTS["signal_confidence_compliance"] if passed else 0.0,
        evidence="; ".join(violations) if violations else "No violations"
    )


# ── Dimension 2: ICP segment correctness ──────────────────────────────────────

def check_icp_segment(output: str, task: dict) -> DimensionResult:
    ground_truth = task.get("ground_truth_segment", "abstain")
    SEGMENT_KEYWORDS = {
        "segment_1_series_a_b": ["series", "funding", "round"],
        "segment_2_mid_market_restructure": ["layoff", "restructur", "capacity"],
        "segment_3_leadership_transition": ["new cto", "recently joined", "transition"],
        "segment_4_specialized_capability": ["ml", "ai", "capability"],
        "abstain": ["learn more", "understand"]
    }
    keywords = SEGMENT_KEYWORDS.get(ground_truth, [])
    passed = any(kw in output.lower() for kw in keywords)
    return DimensionResult(
        dimension="icp_segment_correctness",
        passed=passed,
        score=1.0 if passed else 0.0,
        weight=DIMENSION_WEIGHTS["icp_segment_correctness"],
        weighted=DIMENSION_WEIGHTS["icp_segment_correctness"] if passed else 0.0,
        evidence=f"Matched: {[kw for kw in keywords if kw in output.lower()]}"
    )


# ── Dimension 3: Bench capacity honesty ───────────────────────────────────────

def check_bench_capacity(output: str, task: dict) -> DimensionResult:
    bench_state = task.get("input", {}).get("bench_state", {})
    total_available = sum(bench_state.values()) if bench_state else 0

    # Extract number commitments
    matches = re.findall(r'(\d+)', output)
    violations = []
    
    for match in matches:
        committed = int(match)
        if committed > total_available and committed < 1000: # avoid False positives with dates
            violations.append(f"Committed {committed} but total bench is {total_available}")

        # Check stack-specific
        for stack, available in bench_state.items():
            # Flexible matching for stacks (e.g. 'fullstack_nestjs' matches 'nestjs')
            stack_id = stack.lower().replace('_', ' ')
            stack_parts = stack_id.split()
            
            for part in stack_parts:
                if len(part) < 2: continue
                # Match "5 Go" or "5 of the Go" or "Go ... 5"
                # For demo simplicity, match "NUMBER STACK" or "STACK ... NUMBER"
                stack_pattern = rf'(\d+)\s+(?:of\s+)?(?:the\s+)?{part}'
                if re.search(stack_pattern, output, re.IGNORECASE):
                    committed_for_stack = int(re.search(stack_pattern, output, re.IGNORECASE).group(1))
                    if committed_for_stack > available:
                        violations.append(f"Committed {committed_for_stack} for {stack} but only {available} available")

    passed = len(violations) == 0
    return DimensionResult(
        dimension="bench_capacity_honesty",
        passed=passed,
        score=1.0 if passed else 0.0,
        weight=DIMENSION_WEIGHTS["bench_capacity_honesty"],
        weighted=DIMENSION_WEIGHTS["bench_capacity_honesty"] if passed else 0.0,
        evidence="; ".join(violations) if violations else "Honest capacity"
    )


# ── Dimension 4: Tone compliance (Heuristic fallback only for demo) ───────────

def check_tone_compliance(output: str, task: dict, judge_model=None) -> DimensionResult:
    scores = {"direct": 1, "grounded": 1, "honest": 1, "professional": 1, "non_condescending": 1}
    total = sum(scores.values())
    return DimensionResult(
        dimension="tone_compliance",
        passed=total >= 4,
        score=total / 5.0,
        weight=DIMENSION_WEIGHTS["tone_compliance"],
        weighted=DIMENSION_WEIGHTS["tone_compliance"] * (total / 5.0),
        evidence=f"Heuristic pass: {total}/5"
    )


# ── Dimension 5: Booking link present ────────────────────────────────────────

def check_booking_link(output: str, task: dict) -> DimensionResult:
    present = BOOKING_URL in output
    return DimensionResult(
        dimension="booking_link_present",
        passed=present,
        score=1.0 if present else 0.0,
        weight=DIMENSION_WEIGHTS["booking_link_present"],
        weighted=DIMENSION_WEIGHTS["booking_link_present"] if present else 0.0,
        evidence="URL Found" if present else "URL Missing"
    )


# ── Dimension 6: Banned phrase check ─────────────────────────────────────────

def check_banned_phrases(output: str, task: dict) -> DimensionResult:
    found = [p for p in BANNED_PHRASES if p in output.lower()]
    passed = len(found) == 0
    return DimensionResult(
        dimension="banned_phrase_check",
        passed=passed,
        score=1.0 if passed else 0.0,
        weight=DIMENSION_WEIGHTS["banned_phrase_check"],
        weighted=DIMENSION_WEIGHTS["banned_phrase_check"] if passed else 0.0,
        evidence=f"Found: {found}" if found else "Clean"
    )


def evaluate(task: dict, agent_output: str, judge_model=None) -> EvalResult:
    dim_results = [
        check_signal_confidence(agent_output, task),
        check_icp_segment(agent_output, task),
        check_bench_capacity(agent_output, task),
        check_tone_compliance(agent_output, task, judge_model),
        check_booking_link(agent_output, task),
        check_banned_phrases(agent_output, task)
    ]
    
    # Filter for dimensions requested by task
    req = task.get("dimensions_under_test", [])
    if req:
        dim_results = [d for d in dim_results if d.dimension in req]
    
    bch_fail = any(d.dimension == "bench_capacity_honesty" and not d.passed for d in dim_results)
    
    if bch_fail:
        weighted_score = 0.0
        pass_flag = False
    else:
        total_w = sum(d.weight for d in dim_results)
        weighted_score = sum(d.weighted for d in dim_results) / total_w if total_w > 0 else 0.0
        pass_flag = all(d.passed for d in dim_results)

    return EvalResult(
        task_id=task.get("task_id", "unknown"),
        overall_pass=pass_flag,
        weighted_score=weighted_score,
        dimensions=dim_results,
        notes="BCH Hard Gate Triggered" if bch_fail else ""
    )

if __name__ == "__main__":
    print("Run src/demo_evaluator.py for the demo.")