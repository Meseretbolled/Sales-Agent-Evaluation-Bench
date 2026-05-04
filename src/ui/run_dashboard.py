import http.server
import socketserver
import json
import os
import sys
from pathlib import Path

# Allow running from any directory
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

PORT = 8008
DIRECTORY = str(ROOT / "src" / "ui")

class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        if self.path == "/api/scenarios":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            
            scenarios = []
            dev_path = Path("tenacious_bench_v0.1/dev")
            for f in sorted(dev_path.glob("*.json")):
                scenarios.append({"id": f.stem, "path": str(f)})
            
            self.wfile.write(json.dumps(scenarios).encode())
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == "/api/evaluate":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode())
            
            task_path = data.get("task_path")
            agent_output = data.get("agent_output")
            
            try:
                task = json.loads(Path(task_path).read_text())
                result = evaluate(task, agent_output)
                
                # Convert dimensions list to mapping
                dims = {d.dimension: d.score for d in result.dimensions}
                
                # Format result for UI
                response = {
                    "score": round(result.weighted_score, 3),
                    "rubric": [
                        {"name": "Signal Confidence", "score": dims.get("signal_confidence_compliance", 0), "weight": 0.25},
                        {"name": "ICP Alignment", "score": dims.get("icp_segment_correctness", 0), "weight": 0.20},
                        {"name": "Capacity Honesty (BCH)", "score": dims.get("bench_capacity_honesty", 0), "weight": 0.20},
                        {"name": "Tone Compliance", "score": dims.get("tone_compliance", 0), "weight": 0.15},
                        {"name": "Booking Link", "score": dims.get("booking_link_present", 0), "weight": 0.10},
                        {"name": "Banned Phrases", "score": dims.get("banned_phrase_check", 0), "weight": 0.10},
                    ],
                    "bch_failure": dims.get("bench_capacity_honesty", 0) == 0
                }
                
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(str(e).encode())

if __name__ == "__main__":
    os.chdir(ROOT)
    with socketserver.TCPServer(("", PORT), DashboardHandler) as httpd:
        print(f"\n🚀  Tenacious-Bench Dashboard  →  http://localhost:{PORT}\n")
        print("    Open in your browser to present.")
        print("    Ctrl-C to stop.\n")
        httpd.serve_forever()
