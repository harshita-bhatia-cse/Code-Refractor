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

    # ✅ Repo-level analysis
    def run(self, repo_path: str, output_path: str):
        results = self.engine.run(repo_path)
        self.aggregator.save(results, output_path)
        return results

    # ✅ Viewer-level analysis (file-aware + fallback)
    def analyze(self, code: str, filename: str):
        # 1️⃣ Detect language from filename
        language = detect_language(filename)

        # 2️⃣ Fallback to content-based detection
        if language == "unknown":
            language = detect_language_from_code(code)

        # ---------- HTML → split into HTML / CSS / JS ----------
        if language == "html":
            segmenter = CodeSegmenter()
            segments, start_lines = segmenter.segment(code)

            analysis = {}

            for lang, code_lines in segments.items():
                if not code_lines:
                    continue

                segment_code = "\n".join(code_lines)
                analyzer = get(lang)

                if analyzer:
                    metrics = analyzer.analyze(segment_code)
                else:
                    metrics = CommonMetrics().analyze(segment_code)

                analysis[lang] = {
                    "start_lines": start_lines.get(lang, []),
                    "metrics": metrics
                }

            return {
                "languages_detected": list(analysis.keys()),
                "analysis": analysis
            }

        # ---------- Non-HTML: single language ----------
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
