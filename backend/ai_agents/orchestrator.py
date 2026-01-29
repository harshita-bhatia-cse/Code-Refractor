from backend.ai_agents.metrics_agent import MetricsAgent
from backend.ai_agents.refactor_agent import RefactorAgent
from backend.ai_agents.style_agent import StyleAgent


class OrchestratorAgent:
    def __init__(self):
        self.metrics = MetricsAgent()
        self.refactor = RefactorAgent()
        self.style = StyleAgent()

    def analyze(self, code: str) -> dict:
        return {
            "metrics": self.metrics.run(code),
            "refactor": self.refactor.run(code),
            "style": self.style.run(code),
            "summary": "AI agents successfully analyzed the code"
        }
