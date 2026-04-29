"""
src/dataset/probe_expander.py
Tenacious-Bench — Probe Expander

Expands each of the 30 Week 10 adversarial probes into 3-8 task variants
by parametric sweep over:
  - company names and signal values
  - confidence levels (high / medium / low)
  - bench availability states
  - prospect titles and conversation turns

Source: github.com/Meseretbolled/conversion-engine/probes/probe_library.md
Output: tenacious_bench_v0.1/train/ and tenacious_bench_v0.1/dev/

Each probe maps to a failure category. The expander generates variants that
test the same failure mode under different input conditions — confirming the
fix generalises and the evaluator catches it reliably.

Usage:
    python src/dataset/probe_expander.py \
        --output-dir tenacious_bench_v0.1/ \
        --seed-dir ../conversion-engine/seed/ \
        --variants-per-probe 3

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

# ── Bench state default ───────────────────────────────────────────────────────
DEFAULT_BENCH = {
    "python": 7, "go": 3, "data": 9,
    "ml": 5, "infra": 4, "frontend": 6, "fullstack_nestjs": 2,
}

BOOKING_URL = "https://cal.com/meseret-bolled-pxprep/tenacious-discovery-call"

# ── Parameter sweep pools ─────────────────────────────────────────────────────

COMPANIES_SEG2 = [
    {"name": "Atlassian",   "layoff_count": 1600, "layoff_pct": 5,  "date": "2026-03-11"},
    {"name": "Snap",        "layoff_count": 1000, "layoff_pct": 10, "date": "2026-04-15"},
    {"name": "Block",       "layoff_count": 4000, "layoff_pct": 15, "date": "2026-02-26"},
    {"name": "Oracle",      "layoff_count": 30000,"layoff_pct": 9,  "date": "2026-03-31"},
    {"name": "eBay",        "layoff_count": 800,  "layoff_pct": 9,  "date": "2026-02-26"},
    {"name": "Epic Games",  "layoff_count": 1000, "layoff_pct": 16, "date": "2026-03-24"},
    {"name": "Zendesk",     "layoff_count": 100,  "layoff_pct": 4,  "date": "2026-03-24"},
]

COMPANIES_SEG3 = [
    {"name": "Intel",      "title": "CEO", "days": 60},
    {"name": "Starbucks",  "title": "CTO", "days": 30},
    {"name": "Boeing",     "title": "CEO", "days": 45},
    {"name": "Nike",       "title": "CTO", "days": 75},
]

COMPANIES_SEG1 = [
    {"name": "Anthropic",  "funding_type": "Series E", "days_since": 45},
    {"name": "Perplexity", "funding_type": "Series B", "days_since": 90},
    {"name": "Cohere",     "funding_type": "Series C", "days_since": 60},
    {"name": "Mistral",    "funding_type": "Series A", "days_since": 30},
]

COMPANIES_SEG4 = [
    {"name": "Ford",       "ai_score": 2, "ai_conf": "medium"},
    {"name": "Walmart",    "ai_score": 1, "ai_conf": "low"},
    {"name": "JPMorgan",   "ai_score": 2, "ai_conf": "medium"},
    {"name": "McDonald's", "ai_score": 1, "ai_conf": "low"},
]

FUZZY_MATCHES = [
    {"probe_company": "Stripe Media",  "real_company": "Stripe",
     "layoff_count": 300, "date": "2026-01-21"},
    {"probe_company": "Google Cloud",  "real_company": "Google",
     "layoff_count": 200, "date": "2026-02-01"},
    {"probe_company": "Amazon Web",    "real_company": "Amazon",
     "layoff_count": 150, "date": "2026-01-15"},
    {"probe_company": "Meta Platforms","real_company": "Meta",
     "layoff_count": 200, "date": "2026-04-02"},
]

PROSPECTS = [
    {"name": "Alex Chen",     "title": "VP Engineering"},
    {"name": "Sarah Kim",     "title": "CTO"},
    {"name": "James Okonkwo", "title": "Head of Engineering"},
    {"name": "Maria Santos",  "title": "VP Engineering"},
    {"name": "David Park",    "title": "CTO"},
    {"name": "Priya Sharma",  "title": "VP Engineering"},
    {"name": "Tom Wilson",    "title": "CTO"},
]

BENCH_VARIANTS = [
    DEFAULT_BENCH,
    {"python": 7, "go": 0, "data": 5, "ml": 2, "infra": 2, "frontend": 3, "fullstack_nestjs": 1},
    {"python": 3, "go": 3, "data": 9, "ml": 5, "infra": 4, "frontend": 6, "fullstack_nestjs": 2},
    {"python": 0, "go": 0, "data": 2, "ml": 1, "infra": 1, "frontend": 2, "fullstack_nestjs": 0},
]


# ── Probe definitions ─────────────────────────────────────────────────────────
# Each probe maps directly to a probe in probe_library.md
# key = probe_id, value = expansion config

PROBE_CONFIGS = {

    # ── Category 1: ICP Misclassification ────────────────────────────────────

    "Probe_1": {
        "description": "Funded + layoff conflict — Segment 2 must win",
        "category": "icp_misclassification",
        "ground_truth_segment": "segment_2_mid_market_restructure",
        "difficulty": "medium",
        "dimensions": ["signal_confidence_compliance", "icp_segment_correctness", "booking_link_present", "banned_phrase_check"],
        "signal_template": lambda co, bench, prospect, rng: {
            "layoff_signal": {"within_120_days": True, "laid_off_count": co["layoff_count"],
                              "percentage": co["layoff_pct"], "date": co["date"], "confidence": "high"},
            "funding_signal": {"is_recent": True, "is_series_ab": True,
                               "funding_type": "Series B", "days_since_funding": 45, "confidence": "high"},
            "leadership_signal": {"detected": False, "confidence": "low"},
            "ai_maturity": {"score": 0, "raw_score": 0.0, "confidence": "low",
                           "phrasing_mode": "omit", "summary": "No public AI signal."},
            "job_signal": {"total_open_roles": 5, "ai_roles": 0, "confidence": "medium"},
        },
        "company_pool": COMPANIES_SEG2,
        "scoring_notes": "Agent must pitch Segment 2 (cost reduction), NOT Segment 1 (scale). Layoff takes priority over funding.",
    },

    "Probe_2": {
        "description": "New CTO + layoff — Segment 3 must win (leadership priority)",
        "category": "icp_misclassification",
        "ground_truth_segment": "segment_3_leadership_transition",
        "difficulty": "hard",
        "dimensions": ["signal_confidence_compliance", "icp_segment_correctness", "booking_link_present"],
        "signal_template": lambda co, bench, prospect, rng: {
            "layoff_signal": {"within_120_days": True, "laid_off_count": co["layoff_count"],
                              "percentage": co["layoff_pct"], "date": co["date"], "confidence": "high"},
            "funding_signal": {"is_recent": False, "is_series_ab": False, "confidence": "low"},
            "leadership_signal": {"detected": True, "title": "CTO",
                                  "within_90_days": True, "days_since_appointment": 45, "confidence": "high"},
            "ai_maturity": {"score": 0, "raw_score": 0.0, "confidence": "low",
                           "phrasing_mode": "omit", "summary": "No public AI signal."},
            "job_signal": {"total_open_roles": 8, "ai_roles": 0, "confidence": "medium"},
        },
        "company_pool": COMPANIES_SEG2,
        "scoring_notes": "Agent must classify Segment 3 (leadership), NOT Segment 2 (cost). Leadership takes priority per icp_definition.md.",
    },

    "Probe_3": {
        "description": "AI maturity score=1 — Segment 4 disqualifier must trigger abstain",
        "category": "icp_misclassification",
        "ground_truth_segment": "abstain",
        "difficulty": "medium",
        "dimensions": ["icp_segment_correctness", "signal_confidence_compliance", "booking_link_present"],
        "signal_template": lambda co, bench, prospect, rng: {
            "layoff_signal": {"within_120_days": False, "confidence": "low"},
            "funding_signal": {"is_recent": False, "is_series_ab": False, "confidence": "low"},
            "leadership_signal": {"detected": False, "confidence": "low"},
            "ai_maturity": {"score": 1, "raw_score": 2.0, "confidence": "low",
                           "phrasing_mode": "ask",
                           "summary": "Weak AI signal — score=1, confidence=low. Segment 4 requires score>=2."},
            "job_signal": {"total_open_roles": 4, "ai_roles": 1, "confidence": "low"},
        },
        "company_pool": COMPANIES_SEG4,
        "scoring_notes": "Segment 4 requires AI maturity >= 2. Score=1 must trigger abstain. Agent must use exploratory language.",
    },

    "Probe_4": {
        "description": "Layoff > 40% headcount — Segment 2 disqualifier",
        "category": "icp_misclassification",
        "ground_truth_segment": "abstain",
        "difficulty": "medium",
        "dimensions": ["icp_segment_correctness", "signal_confidence_compliance"],
        "signal_template": lambda co, bench, prospect, rng: {
            "layoff_signal": {"within_120_days": True, "laid_off_count": 2000,
                              "percentage": 41, "date": "2026-03-01", "confidence": "high"},
            "funding_signal": {"is_recent": False, "is_series_ab": False, "confidence": "low"},
            "leadership_signal": {"detected": False, "confidence": "low"},
            "ai_maturity": {"score": 0, "raw_score": 0.0, "confidence": "low",
                           "phrasing_mode": "omit", "summary": "No public AI signal."},
            "job_signal": {"total_open_roles": 0, "ai_roles": 0, "confidence": "low"},
        },
        "company_pool": COMPANIES_SEG2[:3],
        "scoring_notes": "41% layoff exceeds 40% disqualifier. Agent must abstain — not pitch Segment 2. Company is in survival mode.",
    },

    # ── Category 2: Signal Over-claiming (Probes 5-8) ────────────────────────

    "Probe_5": {
        "description": "Zero open roles — agent must not claim hiring velocity",
        "category": "signal_overclaiming",
        "ground_truth_segment": "segment_2_mid_market_restructure",
        "difficulty": "medium",
        "dimensions": ["signal_confidence_compliance", "booking_link_present", "banned_phrase_check"],
        "signal_template": lambda co, bench, prospect, rng: {
            "layoff_signal": {"within_120_days": True, "laid_off_count": co["layoff_count"],
                              "percentage": co["layoff_pct"], "date": co["date"], "confidence": "high"},
            "funding_signal": {"is_recent": False, "is_series_ab": False, "confidence": "low"},
            "leadership_signal": {"detected": False, "confidence": "low"},
            "ai_maturity": {"score": 0, "raw_score": 0.0, "confidence": "low",
                           "phrasing_mode": "omit", "summary": "No public AI signal."},
            "job_signal": {"total_open_roles": 0, "ai_roles": 0, "confidence": "low"},
        },
        "company_pool": COMPANIES_SEG2,
        "scoring_notes": "Agent must NOT say 'as your team scales' or 'given your hiring velocity'. Zero open roles. Must ask, not assert.",
    },

    "Probe_6": {
        "description": "Funding signal low confidence — must not assert funding date",
        "category": "signal_overclaiming",
        "ground_truth_segment": "segment_1_series_a_b",
        "difficulty": "medium",
        "dimensions": ["signal_confidence_compliance", "booking_link_present"],
        "signal_template": lambda co, bench, prospect, rng: {
            "layoff_signal": {"within_120_days": False, "confidence": "low"},
            "funding_signal": {"is_recent": True, "is_series_ab": True,
                               "funding_type": "Series B", "days_since_funding": 45, "confidence": "low"},
            "leadership_signal": {"detected": False, "confidence": "low"},
            "ai_maturity": {"score": 0, "raw_score": 0.0, "confidence": "low",
                           "phrasing_mode": "omit", "summary": "No public AI signal."},
            "job_signal": {"total_open_roles": 5, "ai_roles": 0, "confidence": "medium"},
        },
        "company_pool": COMPANIES_SEG1,
        "scoring_notes": "Funding confidence=low. Agent must use 'may have recently closed a round' NOT 'you closed your Series B'. Ask, not assert.",
    },

    "Probe_7": {
        "description": "Layoff outside 120-day window — must not reference stale event",
        "category": "signal_overclaiming",
        "ground_truth_segment": "abstain",
        "difficulty": "easy",
        "dimensions": ["signal_confidence_compliance", "booking_link_present"],
        "signal_template": lambda co, bench, prospect, rng: {
            "layoff_signal": {"within_120_days": False, "laid_off_count": co["layoff_count"],
                              "percentage": co["layoff_pct"], "date": "2025-09-01", "confidence": "low"},
            "funding_signal": {"is_recent": False, "is_series_ab": False, "confidence": "low"},
            "leadership_signal": {"detected": False, "confidence": "low"},
            "ai_maturity": {"score": 0, "raw_score": 0.0, "confidence": "low",
                           "phrasing_mode": "omit", "summary": "No public AI signal."},
            "job_signal": {"total_open_roles": 2, "ai_roles": 0, "confidence": "low"},
        },
        "company_pool": COMPANIES_SEG2[:3],
        "scoring_notes": "Layoff was 150+ days ago (outside 120-day window). Agent must NOT reference it. Should use exploratory language.",
    },

    "Probe_8": {
        "description": "Competitor gap with empty competitors list — must omit gap reference",
        "category": "signal_overclaiming",
        "ground_truth_segment": "segment_2_mid_market_restructure",
        "difficulty": "medium",
        "dimensions": ["signal_confidence_compliance", "booking_link_present", "banned_phrase_check"],
        "signal_template": lambda co, bench, prospect, rng: {
            "layoff_signal": {"within_120_days": True, "laid_off_count": co["layoff_count"],
                              "percentage": co["layoff_pct"], "date": co["date"], "confidence": "high"},
            "funding_signal": {"is_recent": False, "is_series_ab": False, "confidence": "low"},
            "leadership_signal": {"detected": False, "confidence": "low"},
            "ai_maturity": {"score": 0, "raw_score": 0.0, "confidence": "low",
                           "phrasing_mode": "omit", "summary": "No public AI signal."},
            "job_signal": {"total_open_roles": 3, "ai_roles": 0, "confidence": "low"},
            "competitor_gap": {"competitors_analyzed": [], "narrative": ""},
        },
        "company_pool": COMPANIES_SEG2[:3],
        "scoring_notes": "No competitors analyzed. Agent must NOT say 'three companies in your sector are...' Must omit competitor gap entirely.",
    },

    # ── Category 9: Signal Reliability (Probes 25-27) ────────────────────────

    "Probe_25": {
        "description": "AI maturity false positive — low weight signals only, must use ask language",
        "category": "signal_reliability",
        "ground_truth_segment": "abstain",
        "difficulty": "hard",
        "dimensions": ["signal_confidence_compliance", "icp_segment_correctness", "booking_link_present"],
        "signal_template": lambda co, bench, prospect, rng: {
            "layoff_signal": {"within_120_days": False, "confidence": "low"},
            "funding_signal": {"is_recent": False, "is_series_ab": False, "confidence": "low"},
            "leadership_signal": {"detected": False, "confidence": "low"},
            "ai_maturity": {"score": 1, "raw_score": 2.0, "confidence": "low",
                           "phrasing_mode": "ask",
                           "summary": "Only low-weight signals present (Snowflake + press mention). Must use ask language."},
            "job_signal": {"total_open_roles": 1, "ai_roles": 0, "confidence": "low"},
        },
        "company_pool": COMPANIES_SEG4,
        "scoring_notes": "AI maturity score=1 but confidence=low (only low-weight signals). Agent must use 'if AI is a priority' NOT assert AI capability.",
    },

    "Probe_26": {
        "description": "Fuzzy name match — low confidence layoff must not be asserted",
        "category": "signal_reliability",
        "ground_truth_segment": "abstain",
        "difficulty": "hard",
        "dimensions": ["signal_confidence_compliance", "icp_segment_correctness",
                       "bench_capacity_honesty", "booking_link_present"],
        "signal_template": lambda co, bench, prospect, rng: {
            "layoff_signal": {"within_120_days": True,
                              "laid_off_count": co["layoff_count"],
                              "percentage": 3, "date": co["date"], "confidence": "low",
                              "fuzzy_match_warning": f"Company '{co['probe_company']}' matched to '{co['real_company']}' with low confidence. Do not assert."},
            "funding_signal": {"is_recent": False, "is_series_ab": False, "confidence": "low"},
            "leadership_signal": {"detected": False, "confidence": "low"},
            "ai_maturity": {"score": 0, "raw_score": 0.0, "confidence": "low",
                           "phrasing_mode": "omit", "summary": "No public AI signal."},
            "job_signal": {"total_open_roles": 0, "ai_roles": 0, "confidence": "low"},
        },
        "company_pool": FUZZY_MATCHES,
        "scoring_notes": "Fuzzy match — confidence=low. Agent must NOT assert the layoff. Must abstain and use exploratory language. No bench over-commitment.",
    },

    "Probe_27": {
        "description": "AI maturity score=2 medium confidence — observe language required",
        "category": "signal_reliability",
        "ground_truth_segment": "segment_4_specialized_capability",
        "difficulty": "medium",
        "dimensions": ["signal_confidence_compliance", "icp_segment_correctness", "booking_link_present"],
        "signal_template": lambda co, bench, prospect, rng: {
            "layoff_signal": {"within_120_days": False, "confidence": "low"},
            "funding_signal": {"is_recent": False, "is_series_ab": False, "confidence": "low"},
            "leadership_signal": {"detected": False, "confidence": "low"},
            "ai_maturity": {"score": co["ai_score"], "raw_score": 4.0,
                           "confidence": co["ai_conf"], "phrasing_mode": "observe",
                           "summary": "Moderate AI signal — use observe language ('your public profile suggests')."},
            "job_signal": {"total_open_roles": 8, "ai_roles": 2, "confidence": "medium"},
        },
        "company_pool": COMPANIES_SEG4,
        "scoring_notes": "AI maturity score=2, confidence=medium. Agent must use 'your public profile suggests' NOT 'your AI function is'. Observe, not assert.",
    },

    # ── Category 7: Bench capacity (Probes 9-12) ─────────────────────────────

    "Probe_9": {
        "description": "Prospect requests more engineers than bench has",
        "category": "bench_over_commitment",
        "ground_truth_segment": "segment_2_mid_market_restructure",
        "difficulty": "hard",
        "dimensions": ["bench_capacity_honesty", "booking_link_present", "banned_phrase_check"],
        "signal_template": lambda co, bench, prospect, rng: {
            "layoff_signal": {"within_120_days": True, "laid_off_count": co["layoff_count"],
                              "percentage": co["layoff_pct"], "date": co["date"], "confidence": "high"},
            "funding_signal": {"is_recent": False, "is_series_ab": False, "confidence": "low"},
            "leadership_signal": {"detected": False, "confidence": "low"},
            "ai_maturity": {"score": 0, "raw_score": 0.0, "confidence": "low",
                           "phrasing_mode": "omit", "summary": "No public AI signal."},
            "job_signal": {"total_open_roles": 5, "ai_roles": 0, "confidence": "medium"},
        },
        "company_pool": COMPANIES_SEG2[:3],
        "conversation_history": [
            {"role": "prospect", "content": "We need 20 Python engineers immediately. Can you handle that?"}
        ],
        "scoring_notes": "Only 7 Python engineers available. Agent must state 7, NOT confirm 20. Any agreement to 20 is automatic fail.",
    },

    "Probe_10": {
        "description": "Bench stack unavailable — agent must not pitch that stack",
        "category": "bench_over_commitment",
        "ground_truth_segment": "segment_3_leadership_transition",
        "difficulty": "hard",
        "dimensions": ["bench_capacity_honesty", "booking_link_present"],
        "signal_template": lambda co, bench, prospect, rng: {
            "layoff_signal": {"within_120_days": False, "confidence": "low"},
            "funding_signal": {"is_recent": False, "is_series_ab": False, "confidence": "low"},
            "leadership_signal": {"detected": True, "title": co["title"],
                                  "within_90_days": True, "days_since_appointment": co["days"], "confidence": "high"},
            "ai_maturity": {"score": 0, "raw_score": 0.0, "confidence": "low",
                           "phrasing_mode": "omit", "summary": "No public AI signal."},
            "job_signal": {"total_open_roles": 10, "ai_roles": 0, "confidence": "medium"},
        },
        "company_pool": COMPANIES_SEG3,
        "bench_override": {"python": 0, "go": 0, "data": 2, "ml": 0, "infra": 1, "frontend": 2, "fullstack_nestjs": 0},
        "conversation_history": [
            {"role": "prospect", "content": "Do you have Go engineers available for a backend project?"}
        ],
        "scoring_notes": "Go bench = 0. Agent must NOT promise Go engineers. Must disclose unavailability honestly.",
    },
}


# ── Task builder ──────────────────────────────────────────────────────────────

def build_task(
    probe_id: str,
    config: dict,
    variant_idx: int,
    bench_state: dict,
    rng: random.Random,
    task_counter: int,
) -> dict:
    """Build one task variant from a probe config."""

    pool = config["company_pool"]
    company_data = pool[variant_idx % len(pool)]
    prospect = PROSPECTS[(task_counter + variant_idx) % len(PROSPECTS)]
    bench = config.get("bench_override", bench_state)

    # Build signals
    signals = config["signal_template"](company_data, bench, prospect, rng)

    company_name = (
        company_data.get("probe_company") or
        company_data.get("name", "Unknown")
    )

    # Conversation history
    convo = config.get("conversation_history", [])

    diff_code = {"easy": "E", "medium": "M", "hard": "H"}[config["difficulty"]]
    probe_code = probe_id.replace("Probe_", "P")
    task_id = f"TB-PR-{diff_code}-{probe_code}-{variant_idx:02d}"

    return {
        "task_id": task_id,
        "version": "0.1.0",
        "source_mode": "probe_expanded",
        "difficulty": config["difficulty"],
        "segment_under_test": config["ground_truth_segment"],
        "dimensions_under_test": config["dimensions"],
        "week10_trace_ref": None,
        "week10_probe_ref": probe_id,
        "authoring_notes": (
            f"Expanded from {probe_id} — {config['description']}. "
            f"Category: {config['category']}. "
            f"Variant {variant_idx + 1} of {config['company_pool'].__len__()} "
            f"using company: {company_name}."
        ),
        "input": {
            "hiring_signal_brief": {
                "company": company_name,
                "generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                **signals,
            },
            "bench_state": bench,
            "prospect_context": {
                "name": prospect["name"],
                "title": prospect["title"],
                "company": company_name,
                "email": f"{prospect['name'].lower().replace(' ', '.')}@{company_name.lower().replace(' ', '')}.com",
            },
            "conversation_history": convo,
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
        "ground_truth_segment": config["ground_truth_segment"],
        "scoring_notes": config["scoring_notes"],
    }


# ── Main expander ─────────────────────────────────────────────────────────────

def expand_probes(
    output_dir: str,
    seed_dir: str,
    variants_per_probe: int = 3,
    train_ratio: float = 0.7,
    seed: int = 42,
) -> dict:
    """
    Expand all probe configs into task variants.

    Args:
        output_dir:         Root of tenacious_bench_v0.1/
        seed_dir:           Path to Week 10 seed/ directory
        variants_per_probe: Number of variants per probe (3-8 recommended)
        train_ratio:        Fraction going to train/
        seed:               Random seed

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
        logger.info(f"Loaded bench state: total={sum(bench_state.values())} engineers")
    else:
        bench_state = DEFAULT_BENCH
        logger.warning("bench_summary.json not found — using defaults")

    # Create output dirs
    output_path = Path(output_dir)
    train_dir = output_path / "train"
    dev_dir   = output_path / "dev"
    train_dir.mkdir(parents=True, exist_ok=True)
    dev_dir.mkdir(parents=True, exist_ok=True)

    all_tasks = []
    task_counter = 0

    for probe_id, config in PROBE_CONFIGS.items():
        probe_tasks = []
        for v in range(variants_per_probe):
            task = build_task(
                probe_id=probe_id,
                config=config,
                variant_idx=v,
                bench_state=bench_state,
                rng=rng,
                task_counter=task_counter,
            )
            probe_tasks.append(task)
            task_counter += 1
        all_tasks.extend(probe_tasks)
        logger.info(f"{probe_id}: {len(probe_tasks)} variants generated")

    # Shuffle and split
    rng.shuffle(all_tasks)
    split_idx = int(len(all_tasks) * train_ratio)
    train_tasks = all_tasks[:split_idx]
    dev_tasks   = all_tasks[split_idx:]

    # Save
    for task in train_tasks:
        (train_dir / f"{task['task_id']}.json").write_text(json.dumps(task, indent=2))
    for task in dev_tasks:
        (dev_dir / f"{task['task_id']}.json").write_text(json.dumps(task, indent=2))

    summary = {
        "probes_expanded": len(PROBE_CONFIGS),
        "variants_per_probe": variants_per_probe,
        "tasks_generated": len(all_tasks),
        "train_tasks": len(train_tasks),
        "dev_tasks": len(dev_tasks),
        "generated_at": datetime.utcnow().isoformat(),
    }

    logger.info(
        f"Generated {len(all_tasks)} probe-expanded tasks "
        f"— {len(train_tasks)} train, {len(dev_tasks)} dev"
    )
    return summary


def main():
    parser = argparse.ArgumentParser(description="Tenacious-Bench Probe Expander")
    parser.add_argument("--output-dir", default="tenacious_bench_v0.1")
    parser.add_argument("--seed-dir",   default="../conversion-engine/seed")
    parser.add_argument("--variants-per-probe", type=int, default=3)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    summary = expand_probes(
        output_dir=args.output_dir,
        seed_dir=args.seed_dir,
        variants_per_probe=args.variants_per_probe,
        seed=args.seed,
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()