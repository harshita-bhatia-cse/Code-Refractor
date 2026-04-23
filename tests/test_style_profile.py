import shutil
from pathlib import Path
from uuid import uuid4

from backend.ai_agents.style.profile_builder import StyleProfileBuilder
from backend.ai_agents.style.style_analyzer import StyleAnalyzer


def test_style_profile_detects_common_patterns():
    root = _workspace_temp_dir()
    repo = root / "repo"
    repo.mkdir(parents=True)

    try:
        app = repo / "app.py"
        app.write_text(
            """
def load_user_profile(user_id):
    # keep this direct
    profile_data = {}
    if user_id:
        profile_data["id"] = user_id
    return profile_data
""".strip()
            + "\n",
            encoding="utf-8",
        )

        profile = StyleProfileBuilder().build_from_repositories([str(repo)])

        assert profile.naming == "snake_case"
        assert profile.indentation == "4 spaces"
        assert "python" in profile.languages
        assert profile.files_analyzed == 1
    finally:
        _remove_workspace_temp(root)


def test_style_analyzer_groups_frontend_context():
    root = _workspace_temp_dir()
    frontend = root / "frontend"
    frontend.mkdir(parents=True)

    try:
        html = frontend / "index.html"
        css = frontend / "style.css"
        js = frontend / "app.js"

        html.write_text("<html><body><button onclick=\"saveForm()\"></button></body></html>", encoding="utf-8")
        css.write_text(".save-button {\n  display: flex;\n}\n", encoding="utf-8")
        js.write_text("function saveForm() {\n  return true;\n}\n", encoding="utf-8")

        analyzer = StyleAnalyzer()
        metrics = [
            analyzer.analyze_file(str(html), html.read_text(encoding="utf-8")),
            analyzer.analyze_file(str(css), css.read_text(encoding="utf-8")),
            analyzer.analyze_file(str(js), js.read_text(encoding="utf-8")),
        ]
        profile = StyleProfileBuilder().build_from_file_metrics(metrics)

        assert "unified frontend context" in profile.structure
    finally:
        _remove_workspace_temp(root)


def _workspace_temp_dir() -> Path:
    root = Path(__file__).resolve().parent / "_tmp_style" / uuid4().hex
    root.mkdir(parents=True, exist_ok=True)
    return root


def _remove_workspace_temp(path: Path) -> None:
    base = (Path(__file__).resolve().parent / "_tmp_style").resolve()
    target = path.resolve()
    if base in target.parents or target == base:
        shutil.rmtree(target, ignore_errors=True)
