# import requests
# from fastapi import APIRouter, Depends, HTTPException, Query

# from backend.ai_agents.orchestrator import OrchestratorAgent
# from backend.api.auth.jwt_manager import verify_token
# from backend.api.schemas.analysis import AnalyzeResponse
# from backend.utils.url_validation import validate_github_raw_url

# router = APIRouter(prefix="/analyze", tags=["AI Analysis"])


# @router.get("/", response_model=AnalyzeResponse)
# def analyze(raw_url: str = Query(...), user=Depends(verify_token)):
#     del user

#     if any(x in raw_url for x in ["<", "REPO_NAME", "branch", "path-to-file"]):
#         raise HTTPException(status_code=400, detail="Invalid raw_url. Paste a real GitHub raw file URL.")

#     raw_url = validate_github_raw_url(raw_url)

#     try:
#         resp = requests.get(raw_url, timeout=10, allow_redirects=False)
#         resp.raise_for_status()
#     except Exception as exc:
#         raise HTTPException(status_code=400, detail=str(exc))

#     code = resp.text
#     filename = raw_url.split("/")[-1]
#     agent = OrchestratorAgent()
#     return agent.analyze(code, filename)

import requests
from fastapi import APIRouter, Depends, HTTPException, Query

from backend.ai_agents.orchestrator import OrchestratorAgent
from backend.api.auth.jwt_manager import verify_token
from backend.api.schemas.analysis import AnalyzeResponse
from backend.utils.url_validation import validate_github_raw_url

router = APIRouter(prefix="/analyze", tags=["AI Analysis"])


@router.get("/", response_model=AnalyzeResponse)
def analyze(
    raw_url: str = Query(...),
    user=Depends(verify_token)  # 🔥 keep auth
):
    # =========================
    # DEBUG LOG
    # =========================
    print("🔥 ANALYZE API HIT")
    print("URL:", raw_url)

    if not raw_url:
        raise HTTPException(status_code=400, detail="raw_url is required")

    # ❌ INVALID PLACEHOLDER CHECK
    if any(x in raw_url for x in ["<", "REPO_NAME", "branch", "path-to-file"]):
        raise HTTPException(
            status_code=400,
            detail="Invalid raw_url. Use real GitHub raw URL"
        )

    # =========================
    # VALIDATE URL
    # =========================
    try:
        raw_url = validate_github_raw_url(raw_url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid URL: {e}")

    # =========================
    # FETCH FILE
    # =========================
    try:
        resp = requests.get(raw_url, timeout=10)

        if resp.status_code != 200:
            raise HTTPException(
                status_code=400,
                detail=f"GitHub fetch failed: {resp.status_code}"
            )

    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Fetch error: {exc}")

    code = resp.text

    if not code.strip():
        raise HTTPException(status_code=400, detail="Empty file")

    filename = raw_url.split("/")[-1] or "unknown.txt"

    # =========================
    # RUN ANALYSIS
    # =========================
    try:
        agent = OrchestratorAgent()
        result = agent.analyze(code, filename)

        # 🔥 SAFETY RETURN
        if not result:
            raise ValueError("Empty analysis result")

        return result

    except Exception as e:
        print("❌ ANALYSIS ERROR:", e)

        # 🔥 NEVER CRASH UI
        return {
            "languages_detected": ["unknown"],
            "overall_quality_score": 0,
            "overall_grade": "F",
            "overall_risk_badges": ["analysis-failed"],
            "analysis": {},
        }