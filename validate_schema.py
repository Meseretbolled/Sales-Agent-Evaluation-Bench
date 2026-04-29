import json
import jsonschema

# Load your schema
schema = json.load(open("schema.json"))

# Extract the task schema portion
task_schema = schema["task_schema"]

# Write a dummy task to validate
dummy_task = {
    "task_id": "TB-HA-E-000",
    "version": "0.1.0",
    "source_mode": "hand_authored",
    "difficulty": "easy",
    "segment_under_test": "segment_2_mid_market_restructure",
    "dimensions_under_test": ["signal_confidence_compliance", "booking_link_present"],
    "input": {
        "hiring_signal_brief": {
            "company": "Snap",
            "generated_at": "2026-04-15T09:00:00Z",
            "layoff_signal": {
                "within_120_days": True,
                "laid_off_count": 1000,
                "percentage": 10,
                "date": "2026-04-15",
                "confidence": "high"
            },
            "ai_maturity": {
                "score": 0,
                "raw_score": 0.0,
                "confidence": "low",
                "phrasing_mode": "omit",
                "summary": "No public AI signal."
            },
            "job_signal": {
                "total_open_roles": 5,
                "ai_roles": 0,
                "confidence": "medium"
            }
        },
        "bench_state": {
            "python": 7, "go": 3, "data": 9,
            "ml": 5, "infra": 4, "frontend": 6, "fullstack_nestjs": 2
        },
        "prospect_context": {
            "name": "Alex Smith",
            "title": "CTO",
            "company": "Snap",
            "email": "alex@snap.com"
        },
        "conversation_history": []
    },
    "expected_rubric": {
        "signal_confidence_compliance": True,
        "icp_segment_correctness": True,
        "bench_capacity_honesty": True,
        "tone_compliance_min": 4,
        "booking_link_present": True,
        "banned_phrase_check": True,
        "overall_pass": True
    },
    "ground_truth_segment": "segment_2_mid_market_restructure",
    "week10_trace_ref": None,
    "week10_probe_ref": None,
    "authoring_notes": "Dummy validation task. Snap layoff 1,000 on April 15 2026. Single high-confidence signal. Easy difficulty."
}

# Validate
try:
    jsonschema.validate(instance=dummy_task, schema=task_schema)
    print("✅ Validation PASSED — dummy task is valid against schema")
    
    # Save validated task
    import os
    os.makedirs("tenacious_bench_v0.1/dev", exist_ok=True)
    with open("tenacious_bench_v0.1/dev/TB-HA-E-000.json", "w") as f:
        json.dump(dummy_task, f, indent=2)
    print("✅ Saved to tenacious_bench_v0.1/dev/TB-HA-E-000.json")
    
except jsonschema.ValidationError as e:
    print(f"❌ Validation FAILED: {e.message}")
    print(f"   At path: {list(e.path)}")
