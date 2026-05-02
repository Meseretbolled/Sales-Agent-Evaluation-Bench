import os
import json
import random
import shutil
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = Path("tenacious_bench_v0.1")
TRAIN_DIR = BASE_DIR / "train"
DEV_DIR = BASE_DIR / "dev"
HELD_OUT_DIR = BASE_DIR / "held_out"

def get_task_signature(task: dict) -> str:
    """Create a unique signature for the scenario, ignoring volatile metadata."""
    agent_input = task.get("input", {})
    brief = agent_input.get("hiring_signal_brief", {})
    
    # We strip out the generated_at as it causes false uniqueness
    clean_brief = {k: v for k, v in brief.items() if k != "generated_at"}
    
    # We focus on the company signal AND the specific conversation context
    # Use a hash of the conversation history to identify identical threads
    history = agent_input.get("conversation_history", [])
    history_str = json.dumps(history, sort_keys=True)
    
    story = {
        "company": clean_brief.get("company"),
        "layoff_date": clean_brief.get("layoff_signal", {}).get("date"),
        "ai_summary": clean_brief.get("ai_maturity", {}).get("summary"),
        "history_hash": hash(history_str)
    }
    return json.dumps(story, sort_keys=True)

def curate():
    # 1. Collect and group tasks by their input signature
    signature_to_tasks = {} # sig -> [task_dict, ...]
    
    for folder in [TRAIN_DIR, DEV_DIR, HELD_OUT_DIR]:
        if not folder.exists():
            continue
        for f in folder.glob("*.json"):
            try:
                task = json.loads(f.read_text())
                sig = get_task_signature(task)
                if sig not in signature_to_tasks:
                    signature_to_tasks[sig] = []
                signature_to_tasks[sig].append(task)
            except Exception as e:
                logger.error(f"Error loading {f}: {e}")

    logger.info(f"Loaded {sum(len(v) for v in signature_to_tasks.values())} total instances.")
    logger.info(f"Found {len(signature_to_tasks)} unique scenarios (input signals).")

    # 2. Partition by SCENARIO (not by task)
    all_signatures = list(signature_to_tasks.keys())
    random.seed(42)
    random.shuffle(all_signatures)

    n = len(all_signatures)
    train_split = int(n * 0.5)
    dev_split = int(n * 0.3)
    
    train_sigs = all_signatures[:train_split]
    dev_sigs = all_signatures[train_split:train_split+dev_split]
    held_out_sigs = all_signatures[train_split+dev_split:]

    # 3. Clean and Re-save
    for folder in [TRAIN_DIR, DEV_DIR, HELD_OUT_DIR]:
        if folder.exists():
            shutil.rmtree(folder)
        folder.mkdir(parents=True, exist_ok=True)

    def save_group(sigs, folder):
        count = 0
        for sig in sigs:
            for task in signature_to_tasks[sig]:
                filename = f"{task['task_id']}.json"
                # If duplicate IDs exist for DIFFERENT content, avoid overwriting
                if (folder / filename).exists():
                    filename = f"{task['task_id']}_{count}.json"
                (folder / filename).write_text(json.dumps(task, indent=2))
                count += 1
        return count

    c_train = save_group(train_sigs, TRAIN_DIR)
    c_dev = save_group(dev_sigs, DEV_DIR)
    c_held = save_group(held_out_sigs, HELD_OUT_DIR)

    logger.info(f"Partitioned into: Train={c_train} tasks ({len(train_sigs)} sigs), "
                f"Dev={c_dev} tasks ({len(dev_sigs)} sigs), "
                f"Held-out={c_held} tasks ({len(held_out_sigs)} sigs)")

    logger.info("Signal-locked de-duplication complete.")

    logger.info("De-duplication and partitioning complete.")

if __name__ == "__main__":
    curate()
