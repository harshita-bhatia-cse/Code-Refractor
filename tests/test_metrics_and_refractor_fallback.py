from backend.ai_agents.metrics.java_metrics import JavaMetrics
from backend.ai_agents.orchestrator import OrchestratorAgent
from backend.ai_agents.refractor.refractor_agent import LLMRefractorAgent
from backend.ai_agents.style.profile import StyleProfile


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


def test_refactor_skips_large_files():
    agent = LLMRefractorAgent()
    large_code = "x" * 8001
    result = agent.refactor(large_code, "test.py", None)

    assert result["ok"] is True
    assert result["skipped"] is True
    assert "File too large" in result["reason"]


def test_missing_api_key_still_cleans_small_html(monkeypatch):
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    agent = LLMRefractorAgent()
    code = """<html>
      <head>
        <style>
          body{

          }
        </style>
      </head>
      <body>
        <div class = "container">
          <h2>Grocery Bill Counter</h2>
        </div>
      </body>
</html>"""

    result = agent.refactor(code, "index.html", None)

    assert result["ok"] is True
    assert result["fallback"] is True
    assert result["skipped"] is False
    assert result["refactored_code"] != code
    assert "<!DOCTYPE html>" in result["refactored_code"]
    assert "<main" in result["refactored_code"]
    assert "<form>" in result["refactored_code"]
    assert "<input" in result["refactored_code"]
    assert "<button" in result["refactored_code"]
    assert 'class="container"' in result["refactored_code"]


def test_style_prompt_blocks_generic_html_comments_and_boilerplate():
    profile = StyleProfile(
        naming="lowercase",
        indentation="4 spaces",
        comments="sparse, plain",
        structure="inline",
        function_style="not enough function evidence",
    )

    messages = LLMRefractorAgent._build_messages(
        "index.html",
        "html",
        {},
        profile,
        "<html><body><h1>Hello</h1></body></html>",
    )

    prompt = "\n".join(message["content"] for message in messages)

    assert "StyleProfile" in prompt
    assert "sparse, plain" in prompt
    assert "Do not add comments" in prompt
    assert "If code is too minimal" in prompt
    assert "semantic HTML" in prompt


def test_llm_html_output_is_sanitized_against_generic_comments():
    profile = StyleProfile(
        naming="lowercase",
        indentation="4 spaces",
        comments="sparse, plain",
        structure="inline",
        function_style="not enough function evidence",
    )
    agent = LLMRefractorAgent()
    llm_code = """<html>
    <head>
        <style>
            body {
                /* styles for body */
            }
        </style>
    </head>
    <body>
        <div class = "container">
            <h2>Grocery Bill Counter</h2>
        </div>
    </body>
</html>"""

    cleaned = agent._post_process_refactored_code(llm_code, "html", profile)

    assert "styles for body" not in cleaned
    assert 'class="container"' in cleaned
    assert "body {" in cleaned


def test_minimal_grocery_html_expands_into_realistic_frontend():
    profile = StyleProfile(indentation="4 spaces", comments="sparse, plain")
    agent = LLMRefractorAgent()
    code = """<html>
    <head>
        <style>
            body{
            }
        </style>
    </head>
    <body>
        <div class = "container">
            <h2>Grocery Bill Counter</h2>
            <label>Item Name</label>
        </div>
    </body>
</html>"""

    transformed = agent._post_process_refactored_code(code, "html", profile)

    assert transformed != code
    assert "<!DOCTYPE html>" in transformed
    assert '<html lang="en">' in transformed
    assert '<label for="item-name">Item Name</label>' in transformed
    assert '<input type="number" id="item-price"' in transformed
    assert '<button type="submit">Add Item</button>' in transformed


def test_llm_rate_limit_falls_back_to_local_rewrite(monkeypatch):
    agent = LLMRefractorAgent()
    agent.api_key = "test-key"

    def fake_request(messages):
        del messages
        raise RuntimeError("429 Too Many Requests")

    monkeypatch.setattr(agent, "_make_request", fake_request)

    code = """<html>
    <head>
        <style>
            body{
            }
        </style>
    </head>
    <body>
        <div class = "container">
            <h2>Grocery Bill Counter</h2>
            <label>Item Name</label>
        </div>
    </body>
</html>"""

    result = agent.refactor(code, "index.html", None, {"indentation": "4 spaces"})

    assert result["ok"] is True
    assert result["fallback"] is True
    assert result["reason"] == "429 Too Many Requests"
    assert "rate-limited" in result["summary"]
    assert result["refactored_code"] != code
    assert "<!DOCTYPE html>" in result["refactored_code"]
    assert '<input type="text" id="item-name"' in result["refactored_code"]
