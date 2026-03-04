from backend.api.routes import analyze as analyze_route
from backend.api.routes import refactor as refactor_route
from backend.data.github_client import GitHubClient


def test_profile_requires_auth(client):
    response = client.get("/profile/")
    assert response.status_code == 401
    assert response.json()["detail"] == "Missing bearer token"


def test_profile_with_auth(authed_client):
    response = authed_client.get("/profile/")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "JWT protected profile"
    assert body["user"]["sub"] == "test-user"


def test_repos_returns_data(authed_client, monkeypatch):
    monkeypatch.setattr(
        GitHubClient,
        "get_repositories",
        lambda self: [
            {"name": "repo-a", "private": False, "url": "https://github.com/u/repo-a"}
        ],
    )

    response = authed_client.get("/repos/")
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert body[0]["name"] == "repo-a"


def test_analyze_returns_metrics(authed_client, monkeypatch):
    class DummyResponse:
        def __init__(self, text):
            self.text = text

        def raise_for_status(self):
            return None

    monkeypatch.setattr(
        analyze_route.requests,
        "get",
        lambda raw_url, timeout: DummyResponse("def run():\n    return 1\n"),
    )
    monkeypatch.setattr(
        analyze_route.OrchestratorAgent,
        "analyze",
        lambda self, code, filename: {
            "languages_detected": ["python"],
            "analysis": {"python": {"start_lines": [1], "metrics": {"lines": 2}}},
        },
    )

    response = authed_client.get(
        "/analyze/",
        params={"raw_url": "https://raw.githubusercontent.com/org/repo/main/app.py"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["languages_detected"] == ["python"]


def test_refactor_inline_code(authed_client, monkeypatch):
    monkeypatch.setattr(
        refactor_route.OrchestratorAgent,
        "analyze",
        lambda self, code, filename: {"languages_detected": ["json"], "analysis": {}},
    )
    monkeypatch.setattr(
        refactor_route.LLMRefractorAgent,
        "refactor",
        lambda self, code, filename, analysis=None: {
            "ok": True,
            "language": "json",
            "filename": filename,
            "error": None,
            "summary": "Refactored",
            "issues": [],
            "refactored_code": "{\n  \"a\": 1\n}",
        },
    )

    response = authed_client.post(
        "/refactor/",
        json={"code": "{\"a\":1}", "filename": "sample.json"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["filename"] == "sample.json"
    assert body["llm_refactor"]["ok"] is True


def test_generate_is_not_implemented(authed_client):
    response = authed_client.post("/generate/")
    assert response.status_code == 501
