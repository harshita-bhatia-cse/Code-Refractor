import shutil
import tempfile
from fastapi import APIRouter, Depends, HTTPException
from backend.api.auth.jwt_manager import verify_token
from backend.ai_agents.orchestrator import OrchestratorAgent
from backend.data.github_client import GitHubClient

router = APIRouter(prefix="/analyze-repo", tags=["AI Repo Analysis"])


@router.post("/")
def analyze_repo(repo_path: str, user=Depends(verify_token)):

    try:
        github_token = user["github_token"]
        username = user["sub"]

        # 🔥 Create temporary folder
        temp_dir = tempfile.mkdtemp()

        # 🔥 Download GitHub repo
        client = GitHubClient(github_token)
        client.download_repo(username, repo_path, temp_dir)

        # 🔥 Run analysis on downloaded repo
        agent = OrchestratorAgent()
        result = agent.run(temp_dir, "backend/analysis_output/repo_metrics.json")

        # 🔥 Cleanup temp folder
        shutil.rmtree(temp_dir)

        return {
            "message": "Repository analyzed successfully",
            "result": result
        }

    except Exception as e:
        print("🔥 ERROR:", str(e))
        raise HTTPException(status_code=500, detail=str(e))
