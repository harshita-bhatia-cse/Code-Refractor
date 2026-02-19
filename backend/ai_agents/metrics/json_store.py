import json
from pathlib import Path
from datetime import datetime

from langchain_core.output_parsers import JsonOutputParser
from .metrics_schema import RepoMetricsSchema


class MetricsJSONStore:
    def __init__(self):
        self.output_path = Path("analysis_output/repo_metrics.json")
        self.output_path.parent.mkdir(exist_ok=True)

        self.parser = JsonOutputParser(
            pydantic_object=RepoMetricsSchema
        )

    def save_current_repo(self, raw_metrics: dict):
        raw_metrics["timestamp"] = datetime.utcnow().isoformat()

        # validate JSON via LangChain
        parsed = self.parser.parse(json.dumps(raw_metrics))

        # ALWAYS overwrite
        with open(self.output_path, "w", encoding="utf-8") as f:
            json.dump(parsed.dict(), f, indent=2)

        return str(self.output_path)

