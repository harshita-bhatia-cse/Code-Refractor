from backend.ai_agents.ai_reasoning_agent import AIReasoningAgent
from backend.ai_agents.core.engine import Engine
from backend.ai_agents.metrics.common_metrics import CommonMetrics
from backend.ai_agents.metrics.metrics_aggregator import MetricsAggregator
from backend.ai_agents.core.language_detector import (
    detect_language,
    detect_language_from_code,
)
from backend.ai_agents.core.language_registry import get
from backend.ai_agents.style.profile_builder import StyleProfileBuilder


class OrchestratorAgent:
    def __init__(self):
        self.engine = Engine()
        self.aggregator = MetricsAggregator()
        self.ai_agent = AIReasoningAgent()
        self.style_builder = StyleProfileBuilder()

    def run(self, repo_path: str, output_path: str):
        rule_metrics = self.engine.run(repo_path)
        summary = self._create_llm_summary(rule_metrics)
        ai_analysis = self.ai_agent.analyze(summary)
        style_profile = self.style_builder.build_from_repositories([repo_path])

        final_output = {
            "rule_metrics": rule_metrics,
            "ai_analysis": ai_analysis,
            "style_profile": style_profile.model_dump(),
        }

        self.aggregator.save(final_output, output_path)
        return final_output

    def run_many(self, repo_paths: list[str], output_path: str):
        combined_metrics = {}

        for repo_path in repo_paths:
            repo_metrics = self.engine.run(repo_path)
            for path, result in repo_metrics.items():
                combined_metrics[path] = result

        summary = self._create_llm_summary(combined_metrics)
        ai_analysis = self.ai_agent.analyze(summary)
        style_profile = self.style_builder.build_from_repositories(repo_paths)

        final_output = {
            "rule_metrics": combined_metrics,
            "ai_analysis": ai_analysis,
            "style_profile": style_profile.model_dump(),
        }

        self.aggregator.save(final_output, output_path)
        return final_output

    def analyze(self, code: str, filename: str):
        language = detect_language(filename)

        if language == "unknown":
            language = detect_language_from_code(code)

        analyzer = get(language)

        if analyzer:
            metrics = analyzer.analyze(code)
        else:
            metrics = CommonMetrics().analyze(code)

        quality = self._score_quality(metrics)

        return {
            "languages_detected": [language],
            "overall_quality_score": quality["score"],
            "overall_grade": quality["grade"],
            "overall_risk_badges": quality["risk_badges"],
            "analysis": {
                language: {
                    "start_lines": [1],
                    "metrics": metrics,
                    "quality_score": quality["score"],
                    "grade": quality["grade"],
                    "risk_badges": quality["risk_badges"],
                }
            },
        }

    @staticmethod
    def _score_quality(metrics: dict) -> dict:
        lines = int(metrics.get("lines", 0) or 0)
        functions = int(metrics.get("functions", 0) or 0)
        classes = int(metrics.get("classes", 0) or 0)
        conditionals = metrics.get("conditionals", {}) or {}
        conditional_total = sum(
            int(conditionals.get(key, 0) or 0)
            for key in ("if", "for", "while", "switch")
        )

        penalty = 0
        penalty += min(40, conditional_total * 2)
        penalty += max(0, functions - 20)
        penalty += max(0, classes - 10) * 2
        if lines > 400:
            penalty += min(20, (lines - 400) // 20)

        score = max(0, min(100, 100 - penalty))

        if score >= 90:
            grade = "A"
        elif score >= 80:
            grade = "B"
        elif score >= 70:
            grade = "C"
        elif score >= 60:
            grade = "D"
        else:
            grade = "F"

        risk_badges = []
        if conditional_total >= 15:
            risk_badges.append("high-complexity")
        if functions >= 25:
            risk_badges.append("too-many-functions")
        if lines >= 500:
            risk_badges.append("large-file")
        if score < 60:
            risk_badges.append("low-maintainability")
        if not risk_badges:
            risk_badges.append("healthy")

        return {
            "score": score,
            "grade": grade,
            "risk_badges": risk_badges,
        }

    def _create_llm_summary(self, rule_metrics):
        total_files = len(rule_metrics)
        total_lines = 0
        total_functions = 0
        total_classes = 0

        for file_data in rule_metrics.values():
            metrics = file_data.get("metrics", {})
            total_lines += metrics.get("lines", 0)
            total_functions += metrics.get("functions", 0)
            total_classes += metrics.get("classes", 0)

        return {
            "total_files": total_files,
            "total_lines": total_lines,
            "total_functions": total_functions,
            "total_classes": total_classes,
        }
