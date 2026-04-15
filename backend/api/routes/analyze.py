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

    print("ANALYZE API HIT")
    print(f"URL: {raw_url}")

    if not raw_url:
        raise HTTPException(status_code=400, detail="raw_url is required")

    if any(x in raw_url for x in ["<", "REPO_NAME", "branch", "path-to-file"]):
        raise HTTPException(
            status_code=400,
            detail="Invalid raw_url. Use real GitHub raw URL",
        )

    try:
        raw_url = validate_github_raw_url(raw_url)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid URL: {exc}") from exc

    try:
        resp = requests.get(raw_url, timeout=10, allow_redirects=False)
        resp.raise_for_status()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Fetch error: {exc}") from exc

    code = resp.text
    if not code.strip():
        raise HTTPException(status_code=400, detail="Empty file")

    filename = raw_url.split("/")[-1] or "unknown.txt"

    try:
        agent = OrchestratorAgent()
        result = agent.analyze(code, filename)
        if not result:
            raise ValueError("Empty analysis result")
        return result
    except Exception as exc:
        print(f"ANALYSIS ERROR: {exc}")
        return {
            "languages_detected": ["unknown"],
            "overall_quality_score": 0,
            "overall_grade": "F",
            "overall_risk_badges": ["analysis-failed"],
            "analysis": {},
        }
