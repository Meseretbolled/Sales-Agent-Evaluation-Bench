"""
src/dataset/partitioner.py
Tenacious-Bench — Dataset Partitioner

Splits all generated tasks into three partitions:
  train/     50% — used to fine-tune the LoRA adapter
  dev/       30% — used for iteration during training
  held_out/  20% — sealed until final evaluation (gitignored)

Stratified by:
  - source_mode  (trace_derived, probe_expanded, llm_synthesized, hand_authored)
  - difficulty   (easy, medium, hard)
  - segment      (4 segments + abstain)

This ensures each partition has representative coverage of all task types.

Usage:
    python src/dataset/partitioner.py \
        --input-dir tenacious_bench_v0.1/ \
        --train-ratio 0.5 \
        --dev-ratio 0.3 \
        --seed 42

Author: Meseret Bolled
"""

import json
import random
import shutil
import argparse
import logging
from pathlib import Path
from collections import defaultdict
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def load_all_tasks(input_dir: str) -> list:
    """Load all tasks from train/ and dev/ (not held_out — that is sealed)."""
    all_tasks = []
    base = Path(input_dir)
    for subdir in ["train", "dev"]:
        subpath = base / subdir
        if subpath.exists():
            for f in sorted(subpath.glob("*.json")):
                try:
                    task = json.loads(f.read_text())
                    all_tasks.append(task)
                except Exception as e:
                    logger.warning(f"Could not load {f}: {e}")
    logger.info(f"Loaded {len(all_tasks)} total tasks for partitioning")
    return all_tasks


def stratified_split(
    tasks: list,
    train_ratio: float,
    dev_ratio: float,
    seed: int,
) -> tuple:
    """
    Stratified split by (source_mode, difficulty, segment).
    Ensures each partition has representative coverage.
    """
    rng = random.Random(seed)

    # Group tasks by stratum
    strata = defaultdict(list)
    for task in tasks:
        key = (
            task.get("source_mode", "unknown"),
            task.get("difficulty", "medium"),
            task.get("segment_under_test", "unknown"),
        )
        strata[key].append(task)

    train, dev, held_out = [], [], []

    for key, group in strata.items():
        rng.shuffle(group)
        n = len(group)
        n_train    = max(1, int(n * train_ratio))
        n_dev      = max(1, int(n * dev_ratio))
        n_held_out = n - n_train - n_dev

        # Ensure held_out gets at least 1 if group has >= 3 tasks
        if n >= 3 and n_held_out < 1:
            n_dev -= 1
            n_held_out = 1

        train.extend(group[:n_train])
        dev.extend(group[n_train:n_train + n_dev])
        held_out.extend(group[n_train + n_dev:])

        logger.info(
            f"Stratum {key}: {n} tasks → "
            f"{len(group[:n_train])} train, "
            f"{len(group[n_train:n_train+n_dev])} dev, "
            f"{len(group[n_train+n_dev:])} held_out"
        )

    return train, dev, held_out


def save_partition(tasks: list, directory: Path, clear_first: bool = True):
    """Save tasks to a partition directory."""
    if clear_first and directory.exists():
        shutil.rmtree(directory)
    directory.mkdir(parents=True, exist_ok=True)

    for task in tasks:
        out_file = directory / f"{task['task_id']}.json"
        out_file.write_text(json.dumps(task, indent=2))

    logger.info(f"Saved {len(tasks)} tasks to {directory}")


def partition(
    input_dir: str,
    train_ratio: float = 0.5,
    dev_ratio: float = 0.3,
    seed: int = 42,
) -> dict:
    """
    Partition all tasks into train/dev/held_out.

    held_out is 1 - train_ratio - dev_ratio = 20% by default.
    held_out is gitignored and never touched during training.
    """
    held_out_ratio = round(1.0 - train_ratio - dev_ratio, 2)
    logger.info(
        f"Partitioning: train={train_ratio:.0%} "
        f"dev={dev_ratio:.0%} held_out={held_out_ratio:.0%}"
    )

    all_tasks = load_all_tasks(input_dir)
    if not all_tasks:
        logger.error("No tasks found")
        return {}

    train, dev, held_out = stratified_split(all_tasks, train_ratio, dev_ratio, seed)

    base = Path(input_dir)
    save_partition(train,    base / "train",    clear_first=True)
    save_partition(dev,      base / "dev",      clear_first=True)
    save_partition(held_out, base / "held_out", clear_first=True)

    # Print summary by dimension
    def summarize(tasks, label):
        by_difficulty = defaultdict(int)
        by_segment = defaultdict(int)
        by_source = defaultdict(int)
        for t in tasks:
            by_difficulty[t.get("difficulty", "?")] += 1
            by_segment[t.get("segment_under_test", "?")] += 1
            by_source[t.get("source_mode", "?")] += 1
        return {
            "count": len(tasks),
            "by_difficulty": dict(by_difficulty),
            "by_segment": dict(by_segment),
            "by_source": dict(by_source),
        }

    summary = {
        "total_tasks": len(all_tasks),
        "train": summarize(train, "train"),
        "dev": summarize(dev, "dev"),
        "held_out": summarize(held_out, "held_out"),
        "ratios": {"train": train_ratio, "dev": dev_ratio, "held_out": held_out_ratio},
        "seed": seed,
        "partitioned_at": datetime.utcnow().isoformat(),
        "note": "held_out/ is gitignored — never touch until final evaluation",
    }

    logger.info(
        f"Partition complete: {len(train)} train, "
        f"{len(dev)} dev, {len(held_out)} held_out"
    )
    return summary


def main():
    parser = argparse.ArgumentParser(description="Tenacious-Bench Partitioner")
    parser.add_argument("--input-dir",    default="tenacious_bench_v0.1")
    parser.add_argument("--train-ratio",  type=float, default=0.5)
    parser.add_argument("--dev-ratio",    type=float, default=0.3)
    parser.add_argument("--seed",         type=int, default=42)
    args = parser.parse_args()

    summary = partition(
        input_dir=args.input_dir,
        train_ratio=args.train_ratio,
        dev_ratio=args.dev_ratio,
        seed=args.seed,
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()