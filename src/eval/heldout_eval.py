import json
import os
import glob
import logging
from pathlib import Path
import requests

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Settings from .env
HELD_OUT_DIR = "tenacious_bench_v0.1/held_out"
JUDGE_MODEL = "qwen/qwen3-next-80b-a3b-instruct"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

def call_judge(prompt, response, rubric, api_key):
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "model": JUDGE_MODEL,
        "messages": [
            {"role": "system", "content": "You are a strict B2B Sales Judge. Grade the agent response (1-5)."},
            {"role": "user", "content": f"INPUT: {prompt}\nAGENT: {response}\nRUBRIC: {rubric}\nReturn JSON: {{'score': 1-5, 'reasoning': '...'}}"}
        ],
        "response_format": {"type": "json_object"}
    }
    try:
        resp = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=30)
        return json.loads(resp.json()["choices"][0]["message"]["content"])
    except: return {"score": 1, "reasoning": "Judge failed"}

def run_eval():
    api_key = os.environ.get("OPENROUTER_API_KEY")
    task_files = glob.glob(f"{HELD_OUT_DIR}/*.json")
    results = []

    print(f"🚀 evaluating {len(task_files)} sealed tasks...")
    
    for filepath in task_files:
        with open(filepath) as f: task = json.load(f)
        
        # Simulate Agent Call (In a real run, you'd call your fine-tuned model here)
        # For this script, we placeholder the prompt
        prompt = json.dumps(task["input"])
        
        result = {
            "task_id": task["task_id"],
            "status": "Ready for model run",
            "scoring_notes": task["scoring_notes"]
        }
        results.append(result)

    with open("heldout_report.json", "w") as f:
        json.dump(results, f, indent=2)
    print("🏁 Evaluation Framework Ready. Upload to Colab to run against your LoRA adapter.")

if __name__ == "__main__":
    run_eval()
