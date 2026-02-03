from backend.ai_agents.core.file_scanner import FileScanner
from backend.ai_agents.core.language_detector import detect_language
from backend.ai_agents.metrics.common_metrics import CommonMetrics
from backend.ai_agents.core.language_registry import get
from backend.ai_agents.domain.python_domain_classifier import PythonDomainClassifier


class Engine:
    def run(self, repo_path: str):
        scanner = FileScanner()
        files = scanner.scan(repo_path)
        result = {}

        domain_classifier = PythonDomainClassifier()

        for path, code in files:
            lang = detect_language(path)
            analyzer = get(lang)

            # ---------- Metrics ----------
            if analyzer:
                metrics = analyzer.analyze(code)
            else:
                metrics = CommonMetrics().analyze(code)

            file_result = {
                "language": lang,
                "metrics": metrics
            }

            # ---------- 🔥 Python Domain Classification ----------
            if lang == "python":
                file_result["tech_domain"] = domain_classifier.classify(code)

            result[path] = file_result

        return result
