from backend.ai_agents.ai_reasoning_agent import AIReasoningAgent
from backend.ai_agents.core.engine import Engine
from backend.ai_agents.metrics.metrics_aggregator import MetricsAggregator
from backend.ai_agents.core.language_detector import (
    detect_language,
    detect_language_from_code
)
from backend.ai_agents.core.code_segmenter import CodeSegmenter
from backend.ai_agents.core.language_registry import get
from backend.ai_agents.metrics.common_metrics import CommonMetrics


class OrchestratorAgent:

    def __init__(self):
        self.engine = Engine()
        self.aggregator = MetricsAggregator()
        self.ai_agent = AIReasoningAgent()

    # ===============================
    # 🔹 Repo-level Hybrid Analysis
    # ===============================
    def run(self, repo_path: str, output_path: str):

        # 1️⃣ Rule-based metrics
        rule_metrics = self.engine.run(repo_path)

        # 2️⃣ Create compact summary for LLM
        summary = self._create_llm_summary(rule_metrics)

        # 3️⃣ LLM reasoning layer (🔥 send summary NOT full metrics)
        ai_analysis = self.ai_agent.analyze(summary)

        # 4️⃣ Merge results
        final_output = {
            "rule_metrics": rule_metrics,
            "ai_analysis": ai_analysis
        }

        # 5️⃣ Save output
        self.aggregator.save(final_output, output_path)


        return final_output
    

    # ===============================
    # 🔹 File-level Analysis
    # ===============================
    def analyze(self, code: str, filename: str):

        language = detect_language(filename)

        if language == "unknown":
            language = detect_language_from_code(code)

        analyzer = get(language)

        if analyzer:
            metrics = analyzer.analyze(code)
        else:
            metrics = CommonMetrics().analyze(code)

        return {
            "languages_detected": [language],
            "analysis": {
                language: {
                    "start_lines": [1],
                    "metrics": metrics
                }
            }
        }


    # ===============================
    # 🔹 LLM Summary Generator
    # ===============================
    def _create_llm_summary(self, rule_metrics):

        total_files = len(rule_metrics)

        total_lines = 0
        total_functions = 0
        total_classes = 0

        for file_data in rule_metrics.values():
            for lang_data in file_data.get("analysis", {}).values():
                metrics = lang_data.get("metrics", {})
                total_lines += metrics.get("lines", 0)
                total_functions += metrics.get("functions", 0)
                total_classes += metrics.get("classes", 0)

        return {
            "total_files": total_files,
            "total_lines": total_lines,
            "total_functions": total_functions,
            "total_classes": total_classes
        }
