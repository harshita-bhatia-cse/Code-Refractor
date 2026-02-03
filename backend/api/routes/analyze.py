import requests
from fastapi import APIRouter, Depends, HTTPException, Query
from backend.api.auth.jwt_manager import verify_token
from backend.ai_agents.orchestrator import OrchestratorAgent

router = APIRouter(prefix="/analyze", tags=["AI Analysis"])


@router.get("/")
def analyze(
    raw_url: str = Query(...),
    user=Depends(verify_token)
):
    # 🚫 Block placeholders
    if any(x in raw_url for x in ["<", "REPO_NAME", "branch", "path-to-file"]):
        raise HTTPException(
            status_code=400,
            detail="Invalid raw_url. Paste a REAL GitHub raw file URL."
        )

    try:
        resp = requests.get(raw_url, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    code = resp.text
    filename = raw_url.split("/")[-1]  # 🔥 critical

    agent = OrchestratorAgent()
    return agent.analyze(code, filename)
