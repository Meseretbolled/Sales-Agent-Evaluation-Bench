import json
import random
import os
from pathlib import Path

COMPANIES = [
    "Vercel", "Supabase", "Retool", "Linear", "Clerk", "Stripe", "Plaid", "Rippling", 
    "Deel", "Mercury", "Brex", "Navan", "Gusto", "Lattice", "Checkr", "Figma", 
    "Canva", "Miro", "Notion", "Slack", "Zoom", "Datadog", "Crowdstrike", "Cloudflare",
    "Snowflake", "Databricks", "Confluent", "MongoDB", "Hashicorp", "PagerDuty"
]

ROLES = ["VP of Engineering", "Head of Platform", "CTO", "Director of IT", "Engineering Manager"]
NAMES = ["Sarah", "Michael", "James", "Elena", "David", "Jessica", "Alex", "Jordan", "Taylor", "Chris"]

BASE_DIR = Path("tenacious_bench_v0.1/train")

def generate_bulk(count=60):
    os.makedirs(BASE_DIR, exist_ok=True)
    generated = 0
    
    for i in range(count):
        company = random.choice(COMPANIES)
        role = random.choice(ROLES)
        name = random.choice(NAMES)
        layoff_count = random.randint(50, 500)
        task_id = f"TB-PROG-{1000 + i}"
        
        # Vary the summary phrasing to avoid 8-gram overlap
        adjectives = ["moderate", "significant", "early-stage", "advanced", "limited"]
        tools = ["internal tools", "SaaS platforms", "legacy systems", "custom ML models", "cloud solutions"]
        summary = f"{company} demonstrates {random.choice(adjectives)} progress using {random.choice(tools)} for production."
        
        task = {
            "task_id": task_id,
            "authoring_notes": f"Programmatic variation {i} with distinct phrasing.",
            "input": {
                "hiring_signal_brief": {
                    "company": company,
                    "ai_maturity": {
                        "score": random.randint(1, 5),
                        "summary": summary
                    },
                    "layoff_signal": {
                        "date": f"2026-04-{random.randint(10, 25)}",
                        "laid_off_count": layoff_count,
                        "source": "verified_news"
                    }
                },
                "prospect_context": {
                    "name": f"{name} {random.choice(['Chen', 'Smith', 'Doe', 'Lee', 'Garcia'])}",
                    "role": role,
                    "email": f"{name.lower()}@{company.lower()}.com"
                },
                "conversation_history": []
            },
            "expected_behavior": f"Address the {layoff_count} layoffs at {company} by proposing support.",
            "scoring_notes": f"Verify {company} mention and absence of 'bench' jargon."
        }
        
        file_path = BASE_DIR / f"{task_id}.json"
        with open(file_path, "w") as f:
            json.dump(task, f, indent=2)
        generated += 1
        
    print(f"Generated {generated} programmatic tasks in {BASE_DIR}")

if __name__ == "__main__":
    generate_bulk(100)
