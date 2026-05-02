import json
import os
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

REPORT_FILE = "contamination_report.json"
BASE_DIR = Path("tenacious_bench_v0.1")

def purge():
    if not os.path.exists(REPORT_FILE):
        logger.error(f"{REPORT_FILE} not found. Run contamination_check.py first.")
        return

    with open(REPORT_FILE, "r") as f:
        report = json.load(f)

    to_delete = set()

    # Collect violations from all checks (including time_shift warnings)
    for check in report.get("checks", []):
        if check.get("passed") is False:
            # Check both 'details' (for overlap) and 'warnings' (for time_shift)
            for detail in check.get("details", []):
                task_id = detail.get("check_task") or detail.get("task_id")
                if task_id:
                    to_delete.add(task_id)
            
            # The time_shift check uses a different structure for warnings sometimes
            for warning in check.get("details", []):
                tid = warning.get("task_id")
                if tid:
                    to_delete.add(tid)

    logger.info(f"Found {len(to_delete)} tasks to purge due to contamination.")

    deleted_count = 0
    for task_id in to_delete:
        # Check dev and held_out
        for folder in ["dev", "held_out"]:
            filepath = BASE_DIR / folder / f"{task_id}.json"
            if filepath.exists():
                os.remove(filepath)
                logger.info(f"Deleted: {filepath}")
                deleted_count += 1

    logger.info(f"Purge complete. Deleted {deleted_count} file instances.")

if __name__ == "__main__":
    purge()
