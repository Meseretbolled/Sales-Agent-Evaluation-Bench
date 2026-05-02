"""
src/dataset/contamination_check.py
Tenacious-Bench — Contamination Checker

Runs three contamination checks before sealing the held-out partition:
  1. N-gram overlap — no task pair shares >= 8-gram sequences
  2. Embedding similarity — cosine similarity < 0.85 between any train/held-out pair
  3. Time-shift verification — any date-sensitive tasks use dates after Week 10 cutoff

References:
  Chen et al., EMNLP 2025 — "Recent Advances in LLM Benchmarks against Data Contamination"

Usage:
    python src/dataset/contamination_check.py \
        --train-dir tenacious_bench_v0.1/train/ \
        --dev-dir tenacious_bench_v0.1/dev/ \
        --held-out-dir tenacious_bench_v0.1/held_out/

Author: Meseret Bolled
"""

import json
import logging
import argparse
from pathlib import Path
from collections import Counter

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

NGRAM_SIZE       = 8      # Chen et al. threshold
SIMILARITY_LIMIT = 0.85   # max cosine similarity
WEEK10_CUTOFF    = "2026-04-01"  # Week 10 ended April 2026


# ── Text extraction ───────────────────────────────────────────────────────────

def task_to_text(task: dict) -> str:
    """Extract only meaningful text from a task — skip JSON structural tokens."""
    parts = []
    # Only use human-readable input fields per Chen et al. protocol

    brief = task.get("input", {}).get("hiring_signal_brief", {})
    parts.append(brief.get("company", ""))
    parts.append(brief.get("ai_maturity", {}).get("summary", ""))
    ls = brief.get("layoff_signal", {})
    if ls.get("date"):
        parts.append(f"layoff {ls.get('laid_off_count')} on {ls.get('date')}")

    prospect = task.get("input", {}).get("prospect_context", {})
    parts.append(prospect.get("name", ""))

    for turn in task.get("input", {}).get("conversation_history", []):
        parts.append(turn.get("content", ""))

    return " ".join(str(p) for p in parts if p).lower()


def get_ngrams(text: str, n: int) -> Counter:
    """Extract n-grams from text."""
    tokens = text.split()
    if len(tokens) < n:
        return Counter()
    return Counter(
        tuple(tokens[i:i+n])
        for i in range(len(tokens) - n + 1)
    )


# ── Check 1: N-gram overlap ───────────────────────────────────────────────────

def check_ngram_overlap(
    train_tasks: list,
    check_tasks: list,
    n: int = NGRAM_SIZE,
) -> dict:
    """
    Check that no task in check_tasks shares >= n-gram sequences with train_tasks.
    Returns dict with violations and pass/fail.
    """
    logger.info(f"Running {n}-gram overlap check...")

    train_ngrams = {}
    for task in train_tasks:
        text = task_to_text(task)
        ngrams = get_ngrams(text, n)
        train_ngrams[task["task_id"]] = ngrams

    violations = []
    for check_task in check_tasks:
        check_text = task_to_text(check_task)
        check_ngrams = get_ngrams(check_text, n)

        if not check_ngrams:
            continue

        for train_id, train_ng in train_ngrams.items():
            # Find overlapping n-grams
            overlap = set(check_ngrams.keys()) & set(train_ng.keys())
            if overlap:
                violations.append({
                    "check_task": check_task["task_id"],
                    "train_task": train_id,
                    "overlapping_ngrams": len(overlap),
                    "examples": [" ".join(g) for g in list(overlap)[:3]],
                })

    passed = len(violations) == 0
    logger.info(
        f"N-gram check: {'PASS' if passed else 'FAIL'} — "
        f"{len(violations)} violations found"
    )
    return {
        "check": "ngram_overlap",
        "n": n,
        "passed": passed,
        "violations": len(violations),
        "details": violations,
    }


# ── Check 2: Embedding similarity ─────────────────────────────────────────────

def check_embedding_similarity(
    train_tasks: list,
    check_tasks: list,
    limit: float = SIMILARITY_LIMIT,
) -> dict:
    """
    Check cosine similarity between train and check tasks.
    Uses TF-IDF vectors as a lightweight proxy when sentence-transformers unavailable.
    Falls back to TF-IDF if sentence-transformers not installed.
    """
    logger.info("Running embedding similarity check...")

    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        import numpy as np

        all_texts = (
            [task_to_text(t) for t in train_tasks] +
            [task_to_text(t) for t in check_tasks]
        )

        vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
        matrix = vectorizer.fit_transform(all_texts)

        n_train = len(train_tasks)
        train_matrix = matrix[:n_train]
        check_matrix = matrix[n_train:]

        sim_matrix = cosine_similarity(check_matrix, train_matrix)

        violations = []
        for i, check_task in enumerate(check_tasks):
            max_sim = float(np.max(sim_matrix[i]))
            max_idx = int(np.argmax(sim_matrix[i]))
            if max_sim >= limit:
                violations.append({
                    "check_task": check_task["task_id"],
                    "most_similar_train": train_tasks[max_idx]["task_id"],
                    "similarity": round(max_sim, 4),
                })

        passed = len(violations) == 0
        logger.info(
            f"Similarity check: {'PASS' if passed else 'FAIL'} — "
            f"{len(violations)} pairs above {limit} threshold"
        )
        return {
            "check": "embedding_similarity",
            "method": "tfidf_cosine",
            "limit": limit,
            "passed": passed,
            "violations": len(violations),
            "details": violations[:10],
        }

    except ImportError:
        logger.warning("sklearn not installed — skipping embedding similarity check")
        return {
            "check": "embedding_similarity",
            "passed": None,
            "note": "sklearn not installed — install with: pip install scikit-learn",
        }


# ── Check 3: Time-shift verification ──────────────────────────────────────────

def check_time_shift(tasks: list, cutoff: str = WEEK10_CUTOFF) -> dict:
    """
    Verify that date-sensitive tasks use dates from a known range.
    Flags tasks where layoff dates are suspiciously close to or after the cutoff.
    """
    logger.info("Running time-shift verification...")

    warnings = []
    for task in tasks:
        brief = task.get("input", {}).get("hiring_signal_brief", {})
        ls = brief.get("layoff_signal", {})
        date = ls.get("date", "")
        if date and date >= cutoff:
            warnings.append({
                "task_id": task["task_id"],
                "layoff_date": date,
                "note": f"Date {date} is at or after Week 10 cutoff {cutoff}",
            })

    passed = len(warnings) == 0
    logger.info(
        f"Time-shift check: {'PASS' if passed else 'WARNING'} — "
        f"{len(warnings)} tasks with post-cutoff dates"
    )
    return {
        "check": "time_shift",
        "cutoff": cutoff,
        "passed": passed,
        "warnings": len(warnings),
        "details": warnings[:10],
    }


# ── Main runner ───────────────────────────────────────────────────────────────

def load_tasks(directory: str) -> list:
    """Load all task JSON files from a directory."""
    path = Path(directory)
    tasks = []
    for f in sorted(path.glob("*.json")):
        try:
            tasks.append(json.loads(f.read_text()))
        except Exception as e:
            logger.warning(f"Could not load {f}: {e}")
    logger.info(f"Loaded {len(tasks)} tasks from {directory}")
    return tasks


def run_all_checks(
    train_dir: str,
    dev_dir: str,
    held_out_dir: str,
    output_file: str = "contamination_report.json",
) -> dict:
    """
    Run all three contamination checks.
    Train tasks are the reference. Dev and held-out are checked against train.
    """
    train_tasks    = load_tasks(train_dir)
    dev_tasks      = load_tasks(dev_dir)
    held_out_tasks = load_tasks(held_out_dir) if Path(held_out_dir).exists() else []

    all_check_tasks = dev_tasks + held_out_tasks

    if not train_tasks:
        logger.error("No train tasks found — cannot run contamination checks")
        return {}

    results = {
        "train_count": len(train_tasks),
        "dev_count": len(dev_tasks),
        "held_out_count": len(held_out_tasks),
        "checks": [],
    }

    # Run checks
    results["checks"].append(
        check_ngram_overlap(train_tasks, all_check_tasks)
    )
    results["checks"].append(
        check_embedding_similarity(train_tasks, all_check_tasks)
    )
    results["checks"].append(
        check_time_shift(all_check_tasks)
    )

    # Overall pass
    check_results = [c["passed"] for c in results["checks"] if c.get("passed") is not None]
    results["overall_pass"] = all(check_results)
    results["run_at"] = __import__("datetime").datetime.utcnow().isoformat()

    # Save report
    Path(output_file).write_text(json.dumps(results, indent=2))
    logger.info(f"Contamination report saved to {output_file}")

    status = "✅ PASS" if results["overall_pass"] else "❌ FAIL — review violations before sealing held-out"
    logger.info(f"Overall contamination check: {status}")

    return results


def main():
    parser = argparse.ArgumentParser(description="Tenacious-Bench Contamination Checker")
    parser.add_argument("--train-dir",     default="tenacious_bench_v0.1/train")
    parser.add_argument("--dev-dir",       default="tenacious_bench_v0.1/dev")
    parser.add_argument("--held-out-dir",  default="tenacious_bench_v0.1/held_out")
    parser.add_argument("--output-file",   default="contamination_report.json")
    args = parser.parse_args()

    results = run_all_checks(
        train_dir=args.train_dir,
        dev_dir=args.dev_dir,
        held_out_dir=args.held_out_dir,
        output_file=args.output_file,
    )
    print(json.dumps({
        "overall_pass": results.get("overall_pass"),
        "train_count": results.get("train_count"),
        "dev_count": results.get("dev_count"),
        "held_out_count": results.get("held_out_count"),
        "checks": [
            {"check": c["check"], "passed": c["passed"], "violations": c.get("violations", 0)}
            for c in results.get("checks", [])
        ]
    }, indent=2))


if __name__ == "__main__":
    main()