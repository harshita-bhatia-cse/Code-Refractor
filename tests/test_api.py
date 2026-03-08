from backend.api.routes import analyze as analyze_route
from backend.api.routes import repo_analyze as repo_analyze_route
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
        lambda raw_url, timeout, allow_redirects=False: DummyResponse("def run():\n    return 1\n"),
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


def test_analyze_repo_success_cleans_temp_dir(authed_client, monkeypatch):
    deleted_paths = []

    monkeypatch.setattr(repo_analyze_route.tempfile, "mkdtemp", lambda: "tmp-repo-dir")
    monkeypatch.setattr(
        repo_analyze_route.shutil,
        "rmtree",
        lambda path, ignore_errors=True: deleted_paths.append((path, ignore_errors)),
    )
    monkeypatch.setattr(
        repo_analyze_route.GitHubClient,
        "download_repo",
        lambda self, username, repo, save_path: None,
    )
    monkeypatch.setattr(
        repo_analyze_route.OrchestratorAgent,
        "run",
        lambda self, repo_path, output_path: {"rule_metrics": {}, "ai_analysis": {}},
    )

    response = authed_client.post("/analyze-repo/", params={"repo_path": "demo-repo"})
    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "Repository analyzed successfully"
    assert deleted_paths == [("tmp-repo-dir", True)]


def test_analyze_repo_failure_still_cleans_temp_dir(authed_client, monkeypatch):
    deleted_paths = []

    monkeypatch.setattr(repo_analyze_route.tempfile, "mkdtemp", lambda: "tmp-repo-dir")
    monkeypatch.setattr(
        repo_analyze_route.shutil,
        "rmtree",
        lambda path, ignore_errors=True: deleted_paths.append((path, ignore_errors)),
    )
    monkeypatch.setattr(
        repo_analyze_route.GitHubClient,
        "download_repo",
        lambda self, username, repo, save_path: (_ for _ in ()).throw(Exception("download failed")),
    )

    response = authed_client.post("/analyze-repo/", params={"repo_path": "demo-repo"})
    assert response.status_code == 500
    assert response.json()["detail"] == "download failed"
    assert deleted_paths == [("tmp-repo-dir", True)]
