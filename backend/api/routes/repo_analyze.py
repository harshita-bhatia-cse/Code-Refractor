from fastapi import APIRouter, Depends, HTTPException
from backend.api.auth.jwt_manager import verify_token
from backend.ai_agents.orchestrator import OrchestratorAgent

router = APIRouter(prefix="/analyze-repo", tags=["AI Repo Analysis"])


@router.post("/")
def analyze_repo(
    repo_path: str,
    user=Depends(verify_token)
):
    agent = OrchestratorAgent()

    output_path = "backend/analysis_output/repo_metrics.json"

    try:
        result = agent.run(repo_path, output_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "message": "Repository analyzed successfully",
        "output_file": output_path,
        "files_analyzed": len(result)
    }
