from backend.ai_agents.metrics.java_metrics import JavaMetrics
from backend.ai_agents.ai_reasoning_agent import AIReasoningAgent
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


def test_split_code_chunks_respects_max_chars():
    agent = LLMRefractorAgent()
    code = "\n".join(["line" + str(i) for i in range(1, 20)])
    chunks = agent._split_code_chunks(code, max_chars=50)

    assert all(len(chunk) <= 50 for chunk in chunks)
    assert "line1" in chunks[0]


def test_refactor_chunked_retries_for_payload_too_large(monkeypatch):
    agent = LLMRefractorAgent()
    agent.max_input_chars = 25
    agent.chunk_size_chars = 25
    agent.max_retries = 2
    agent.chunk_shrink_factor = 0.5

    calls = []

    def fake_refactor_single(code, filename, analysis, language):
        calls.append(code)
        if len(code) > 12:
            return {
                "ok": False,
                "error": "LLM request failed: Payload Too Large (413)",
                "refactored_code": code,
            }
        return {
            "ok": True,
            "refactored_code": code.upper(),
            "issues": [],
            "summary": "",
        }

    monkeypatch.setattr(agent, "_refactor_single", fake_refactor_single)

    result = agent._refactor_chunked("abcdefghij1234567890ABCDEF", "test.py", None, "python")

    assert result["ok"]
    assert "AB" in result["refactored_code"]
    assert len(calls) > 1


def test_refactor_chunked_respects_max_chunks():
    agent = LLMRefractorAgent()
    agent.chunk_enabled = True
    agent.max_input_chars = 100
    agent.chunk_size_chars = 10
    agent.max_chunks = 2

    # Force split to 3 chunks by monkeypatch to avoid calling LLM.
    agent._split_code_chunks = lambda code, max_chars=None: ["a", "b", "c"]

    result = agent._refactor_chunked("x" * 100, "test.py", None, "python")

    assert result["ok"] is False
    assert "Too many chunks" in result["error"]
    assert "LLM_CHUNK_MAX_CHUNKS" in result["error"]


def test_ai_reasoning_agent_uses_llm_api_key(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("LLM_MODEL", "llama-3.1-8b-instant")
    monkeypatch.setenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")

    class DummyResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "choices": [
                    {
                        "message": {
                            "content": (
                                '{"maintainability_score": 7,'
                                '"complexity_level": "medium",'
                                '"architecture_type": "layered",'
                                '"strengths": ["clear modules"],'
                                '"weaknesses": ["some duplication"],'
                                '"recommendations": ["add tests"]}'
                            )
                        }
                    }
                ]
            }

    def fake_post(*args, **kwargs):
        return DummyResponse()

    monkeypatch.setattr("backend.ai_agents.ai_reasoning_agent.requests.post", fake_post)

    result = AIReasoningAgent().analyze({"lines": 10})

    assert result["maintainability_score"] == 7
    assert result["complexity_level"] == "medium"
    assert result["architecture_type"] == "layered"
    assert result["strengths"] == ["clear modules"]


def test_repo_summary_uses_engine_metric_shape():
    summary = OrchestratorAgent()._create_llm_summary(
        {
            "src/a.java": {
                "language": "java",
                "metrics": {"lines": 12, "functions": 2, "classes": 1},
            },
            "src/b.py": {
                "language": "python",
                "metrics": {"lines": 20, "functions": 3, "classes": 1},
            },
        }
    )

    assert summary["total_files"] == 2
    assert summary["total_lines"] == 32
    assert summary["total_functions"] == 5
    assert summary["language_counts"] == {"java": 1, "python": 1}
    assert summary["largest_files"][0]["path"] == "src/b.py"


def test_refractor_rebuilds_code_from_structure_object():
    parsed = {
        "summary": "Structured output",
        "issues": [],
        "refactored_code": {
            "class": "TwoSumSolution",
            "methods": [
                {
                    "name": "findTwoSum",
                    "return_type": "int[]",
                    "parameters": [
                        {"name": "numbers", "type": "int[]"},
                        {"name": "targetSum", "type": "int"},
                    ],
                    "body": {
                        "variables": [
                            {"name": "numCount", "type": "int", "value": "numbers.length"},
                            {"name": "result", "type": "int[]", "value": "new int[]{-1}"},
                        ],
                        "statements": ["return result;"],
                    },
                }
            ],
        },
    }

    normalized = LLMRefractorAgent._coerce_parsed_envelope(parsed)

    assert "class TwoSumSolution" in normalized["refactored_code"]
    assert "public int[] findTwoSum" in normalized["refactored_code"]
    assert "return result;" in normalized["refactored_code"]


def test_refactor_output_validator_rejects_metadata_blob():
    assert LLMRefractorAgent._looks_like_code("{'class': 'TwoSumSolution', 'methods': []}", "java") is False
    assert LLMRefractorAgent._looks_like_code('{"summary":"x","issues":[],"refactored_code":"y"}', "java") is False
    assert LLMRefractorAgent._looks_like_code("class Solution {\n    public int x() { return 1; }\n}", "java") is True


