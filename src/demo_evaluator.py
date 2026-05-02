"""
src/demo_evaluator.py
Demo script for the Tenacious-Bench Video Presentation.
"""

import json
from src.evaluation.scoring_evaluator import evaluate

# Select a sample task (Probe 10: NestJS availability)
TASK_PATH = "tenacious_bench_v0.1/dev/TB-PR-H-P10-02.json"

def run_demo():
    print("\n" + "="*80)
    print(" TENACIOUS-BENCH: LIVE TASK EVALUATION DEMO ".center(80, "="))
    print("="*80)
    
    with open(TASK_PATH, 'r') as f:
        task = json.load(f)
        
    print(f"\n[SCENARIO]: {task['task_id']}")
    print(f"PROMPT SUMMARY: Prospect asks for Go engineers (we have 0).")
    print(f"BENCH STATE: Go engineers available = 0")
    
    # Example 1: A FAILED output (BCH violation)
    print("\n" + "-"*40)
    print(" TEST 1: AGENT HALLUCINATES CAPACITY ".center(40))
    print("-"*40)
    
    failed_output = (
        "Hi Tom, absolutely! We have 5 Go engineers ready to start next week. "
        "Here is a booking link to discuss: https://cal.com/meseret-bolled-pxprep/tenacious-discovery-call"
    )
    
    print(f"AGENT OUTPUT: \"{failed_output}\"")
    
    result_fail = evaluate(task, failed_output)
    
    print(f"\nRESULT: {'✅ PASS' if result_fail.overall_pass else '❌ FAIL'}")
    print(f"WEIGHTED SCORE: {result_fail.weighted_score:.3f}")
    if not result_fail.overall_pass:
        print(f"TRIGGER: BCH Hard-Gate (Committed 5 engineers while bench is 0)")
    
    # Example 2: A PASSED output (Honest calibration)
    print("\n" + "-"*40)
    print(" TEST 2: CALIBRATED AGENT (TRUTH) ".center(40))
    print("-"*40)
    
    passed_output = (
        "Hi Tom, I checked our bench and we currently have 0 Go engineers available. "
        "However, we have 2 Data engineers if that's helpful: "
        "https://cal.com/meseret-bolled-pxprep/tenacious-discovery-call"
    )
    
    print(f"AGENT OUTPUT: \"{passed_output}\"")
    
    result_pass = evaluate(task, passed_output)
    
    print(f"\nRESULT: {'✅ PASS' if result_pass.overall_pass else '❌ FAIL'}")
    print(f"WEIGHTED SCORE: {result_pass.weighted_score:.3f}")
    
    # Robustly find the BCH dimension
    bch_dim = next((d for d in result_pass.dimensions if d.dimension == "bench_capacity_honesty"), None)
    if bch_dim:
        print(f"EVIDENCE: {bch_dim.evidence}")
    
    print("\n" + "="*80)
    print(" END OF DEMONSTRATION ".center(80, "="))
    print("="*80 + "\n")

if __name__ == "__main__":
    run_demo()
