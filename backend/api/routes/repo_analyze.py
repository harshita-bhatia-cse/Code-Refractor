import os
import shutil
import tempfile

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from backend.ai_agents.orchestrator import OrchestratorAgent
from backend.api.auth.jwt_manager import get_github_token, verify_token
from backend.api.schemas.analysis import AnalyzeRepoResponse
from backend.data.github_client import GitHubClient

router = APIRouter(prefix="/analyze-repo", tags=["AI Repo Analysis"])


class AnalyzeRepoRequest(BaseModel):
    repo_path: str | None = None
    repositories: list[str] = Field(default_factory=list)


@router.post("/", response_model=AnalyzeRepoResponse)
def analyze_repo(
    request: AnalyzeRepoRequest | None = Body(default=None),
    repo_path: str | None = Query(default=None),
    user=Depends(verify_token),
):
    temp_dir = None

    try:
        github_token = get_github_token(user)
        username = user["sub"]
        repo_names = _requested_repositories(request, repo_path)

        if not repo_names:
            raise HTTPException(
                status_code=400,
                detail="Provide repo_path or repositories to analyze.",
            )

        temp_dir = tempfile.mkdtemp()
        client = GitHubClient(github_token)
        downloaded_paths = []

        for index, repository in enumerate(repo_names):
            owner, repo_name = _resolve_repository(repository, username)
            target_dir = temp_dir if len(repo_names) == 1 else os.path.join(temp_dir, f"repo-{index}")
            if len(repo_names) > 1:
                os.makedirs(target_dir, exist_ok=True)
            client.download_repo(owner, repo_name, target_dir)
            downloaded_paths.append(target_dir)

        agent = OrchestratorAgent()
        if len(downloaded_paths) == 1:
            result = agent.run(downloaded_paths[0], "backend/analysis_output/repo_metrics.json")
        else:
            result = agent.run_many(downloaded_paths, "backend/analysis_output/repo_metrics.json")

        return {
            "message": "Repository analyzed successfully",
            "result": result,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        if temp_dir:
            shutil.rmtree(temp_dir, ignore_errors=True)


def _requested_repositories(
    request: AnalyzeRepoRequest | None,
    repo_path: str | None,
) -> list[str]:
    if request and request.repositories:
        return [repo for repo in request.repositories if repo]
    if request and request.repo_path:
        return [request.repo_path]
    if repo_path:
        return [repo_path]
    return []


def _resolve_repository(repository: str, default_owner: str) -> tuple[str, str]:
    value = (repository or "").strip().strip("/")
    if not value:
        raise HTTPException(status_code=400, detail="Repository cannot be empty.")

    if "/" in value:
        owner, repo_name = value.split("/", 1)
        owner = owner.strip()
        repo_name = repo_name.strip()
        if not owner or not repo_name:
            raise HTTPException(status_code=400, detail=f"Invalid repository format: {repository}")
        return owner, repo_name

    return default_owner, value
