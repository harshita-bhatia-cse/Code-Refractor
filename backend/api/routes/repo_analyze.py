import shutil
import tempfile

from fastapi import APIRouter, Depends, HTTPException

from backend.ai_agents.orchestrator import OrchestratorAgent
from backend.api.auth.jwt_manager import verify_token
from backend.api.schemas.analysis import AnalyzeRepoResponse
from backend.data.github_client import GitHubClient

router = APIRouter(prefix="/analyze-repo", tags=["AI Repo Analysis"])


@router.post("/", response_model=AnalyzeRepoResponse)
def analyze_repo(repo_path: str, user=Depends(verify_token)):
    temp_dir = None

    try:
        github_token = user["github_token"]
        username = user["sub"]

        temp_dir = tempfile.mkdtemp()

        client = GitHubClient(github_token)
        client.download_repo(username, repo_path, temp_dir)

        agent = OrchestratorAgent()
        result = agent.run(temp_dir, "backend/analysis_output/repo_metrics.json")

        return {
            "message": "Repository analyzed successfully",
            "result": result,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        if temp_dir:
            shutil.rmtree(temp_dir, ignore_errors=True)
