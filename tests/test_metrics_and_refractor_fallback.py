from backend.ai_agents.metrics.java_metrics import JavaMetrics
from backend.ai_agents.orchestrator import OrchestratorAgent
from backend.ai_agents.refractor.refractor_agent import LLMRefractorAgent


def test_java_metrics_counts_private_and_public_methods():
    code = """class Solution {
    private int f(int n){
        if(n == 1) return 1;
        if(n == 0) return 0;
        return f(n - 2) + f(n - 1);
    }
    public int fib(int n) {
        return f(n);
    }
}"""
    metrics = JavaMetrics().analyze(code)
    assert metrics["functions"] == 2
    assert metrics["classes"] == 1
    assert metrics["conditionals"]["if"] == 2


def test_refractor_fallback_unwraps_nested_json_string():
    content = """```json
{
  "summary": "Outer summary",
  "issues": ["outer issue"],
  "refactored_code": "{\\"summary\\": \\"Inner summary\\", \\"issues\\": [\\"inner issue\\"], \\"refactored_code\\": \\"public class Solution {\\\\n    public int fib(int n) {\\\\n        return n;\\\\n    }\\\\n}\\"}"
}
```"""

    parsed = LLMRefractorAgent._parse_json_content(content) or LLMRefractorAgent._parse_json_content_loose(content)
    assert parsed is not None

    normalized = LLMRefractorAgent._coerce_parsed_envelope(parsed)
    assert "summary" in normalized
    assert normalized["summary"] == "Outer summary"
    assert "issues" in normalized
    assert normalized["issues"] == ["outer issue"]
    assert "refactored_code" in normalized
    assert "public class Solution" in normalized["refactored_code"]


def test_quality_score_returns_grade_and_badges():
    quality = OrchestratorAgent._score_quality(
        {
            "lines": 650,
            "functions": 35,
            "classes": 2,
            "conditionals": {"if": 12, "for": 5, "while": 1, "switch": 0},
        }
    )
    assert 0 <= quality["score"] <= 100
    assert quality["grade"] in {"A", "B", "C", "D", "F"}
    assert "high-complexity" in quality["risk_badges"]
    assert "too-many-functions" in quality["risk_badges"]
    assert "large-file" in quality["risk_badges"]
