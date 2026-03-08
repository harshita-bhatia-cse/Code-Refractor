import requests
from fastapi import APIRouter, Depends, HTTPException, Query

from backend.ai_agents.orchestrator import OrchestratorAgent
from backend.api.auth.jwt_manager import verify_token
from backend.api.schemas.analysis import AnalyzeResponse
from backend.utils.url_validation import validate_github_raw_url

router = APIRouter(prefix="/analyze", tags=["AI Analysis"])


@router.get("/", response_model=AnalyzeResponse)
def analyze(raw_url: str = Query(...), user=Depends(verify_token)):
    del user

    if any(x in raw_url for x in ["<", "REPO_NAME", "branch", "path-to-file"]):
        raise HTTPException(status_code=400, detail="Invalid raw_url. Paste a real GitHub raw file URL.")

    raw_url = validate_github_raw_url(raw_url)

    try:
        resp = requests.get(raw_url, timeout=10, allow_redirects=False)
        resp.raise_for_status()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    code = resp.text
    filename = raw_url.split("/")[-1]
    agent = OrchestratorAgent()
    return agent.analyze(code, filename)
