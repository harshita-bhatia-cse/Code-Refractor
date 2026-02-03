from ..core.base_agent import BaseAgent
from ..core.analysis_context import AnalysisContext


class PythonStyleAgent(BaseAgent):
    def run(self, context: AnalysisContext):
        issues = []

        for i, line in enumerate(context.code.splitlines(), 1):
            if len(line) > 100:
                issues.append(f"Line {i}: exceeds 100 characters")

        return {
            "style_issues": issues or ["PEP8 style looks fine"]
        }
