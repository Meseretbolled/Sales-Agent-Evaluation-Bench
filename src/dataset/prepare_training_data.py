import json
import os
import glob
import time
import logging
from pathlib import Path

import requests

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
# Using a fast, cheap model for generation as required per Act III cost discipline
GENERATE_MODEL = "deepseek/deepseek-chat"

def call_openrouter(prompt: str, api_key: str, temperature: float = 0.5) -> dict:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": GENERATE_MODEL,
        "messages": [
            {"role": "system", "content": "You are a B2B sales email generating LLM."},
            {"role": "user", "content": prompt}
        ],
        "temperature": temperature,
        "response_format": {"type": "json_object"},
    }
    try:
        resp = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=20)
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"].strip()
        import re
        content = re.sub(r"```json|```", "", content).strip()
        return json.loads(content)
    except Exception as e:
        logger.error(f"LLM request error: {e}")
        return {}


def process_partition(partition_name: str, api_key: str):
    input_dir = f"tenacious_bench_v0.1/{partition_name}"
    output_file = f"preferences_{partition_name}.jsonl"
    
    task_files = glob.glob(f"{input_dir}/*.json")
    if not task_files:
        logger.warning(f"No tasks found in {input_dir}")
        return

    logger.info(f"Generating preference pairs (SimPO) for {len(task_files)} tasks in {partition_name}...")
    
    success_count = 0
    existing_ids = set()
    if os.path.exists(output_file):
        with open(output_file, "r") as f:
            for line in f:
                if line.strip():
                    existing_ids.add(json.loads(line).get("task_id"))
                    
    with open(output_file, "a") as out_f:
        for i, filepath in enumerate(task_files):
            with open(filepath, "r") as f:
                task = json.load(f)
                
            if task.get("task_id") in existing_ids:
                continue
            
            # 1. Format the standard agent prompt
            agent_input = task.get("input", {})
            prompt = (
                "Generate a B2B sales outreach/reply based on this prospect context:\n"
                f"{json.dumps(agent_input, indent=2)}\n"
            )
            
            # 2. Instruct the LLM to generate the Preference Pair (Chosen vs Rejected)
            behavior_rule = task.get("expected_behavior", "") or task.get("scoring_notes", "")
            if not behavior_rule:
                behavior_rule = "Maintain professional Tenacious tone. 120 words max. Grounded on signals."
            
            simpo_generation_prompt = f"""You are generating preference tuning data (SimPO/DPO) for a B2B sales agent.
Given the prospect's context and the behavior rule:

PROSPECT CONTEXT: {json.dumps(agent_input)}
BEHAVIOR RULE: {behavior_rule}

Return a single JSON object containing:
- "chosen": A perfectly formatted email following the rule exactly, under 120 words. No "bench" jargon.
- "rejected": A bad email that intentionally violates the rule (e.g., condescending, ignores weak confidence signals by asserting aggressive hiring, uses banned words 'world-class/A-players', or is too long).

Return ONLY valid JSON block cleanly parseable:
{{
    "chosen": "email draft here...",
    "rejected": "bad draft here..."
}}"""
            
            # Fire LLM call
            result = call_openrouter(simpo_generation_prompt, api_key)
            if "chosen" in result and "rejected" in result:
                record = {
                    "task_id": task.get("task_id", ""),
                    "prompt": prompt,
                    "chosen": result["chosen"],
                    "rejected": result["rejected"]
                }
                out_f.write(json.dumps(record) + "\n")
                out_f.flush()
                success_count += 1
                if (success_count + len(existing_ids)) % 10 == 0:
                    logger.info(f"  Processed {success_count + len(existing_ids)} valid pairs from {partition_name}...")
            else:
                logger.warning(f"  Failed parsing valid pair for {task.get('task_id')}")

            time.sleep(1.0) # rate limiting

    logger.info(f"Done building {output_file}: {success_count} pairs saved.")


if __name__ == "__main__":
    # Automatically extracts API key without needing manual terminal export
    if os.path.exists(".env"):
        for line in open(".env"):
            if "OPENROUTER_API_KEY" in line:
                os.environ["OPENROUTER_API_KEY"] = line.split("=")[1].strip()
                
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        logger.error("Set OPENROUTER_API_KEY environment variable. We need a dev-tier model to generate pairs.")
        exit(1)
        
    process_partition("train", api_key)
    process_partition("dev", api_key)

