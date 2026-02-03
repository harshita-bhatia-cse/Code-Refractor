import json
import os
from datetime import datetime


class MetricsAggregator:
    def save(self, analysis_result: dict, output_path: str):
        print("🔥 MetricsAggregator.save() CALLED")
        print("🔥 Files analyzed:", len(analysis_result))

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        payload = {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "tool": "Code Refactorer AI Analyzer",
            "analysis": analysis_result
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        print(f"✅ Metrics written to {output_path}")
