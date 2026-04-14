from typing import Optional
import asyncio
import requests

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.ai_agents.orchestrator import OrchestratorAgent
from backend.ai_agents.refractor.refractor_agent import LLMRefractorAgent
from backend.ai_agents.core.language_detector import detect_language
from backend.api.auth.jwt_manager import verify_token
from backend.api.schemas.analysis import RefactorResponse
from backend.utils.url_validation import validate_github_raw_url

router = APIRouter(prefix="/refactor", tags=["AI Refactor"])


class RefactorRequest(BaseModel):
    raw_url: Optional[str] = None
    code: Optional[str] = None
    filename: Optional[str] = None


# ===============================
# 🔥 SMART LLM DECISION FUNCTION
# ===============================
def should_use_llm(code: str, language: str) -> bool:
    if language == "json":
        return False
    if len(code) < 300:
        return False
    if len(code) > 8000:
        return False
    return True


# ===============================
# 🚀 MAIN API
# ===============================
@router.post("/", response_model=RefactorResponse)
async def refactor_code(request: RefactorRequest, user=Depends(verify_token)):
    del user

    code = request.code
    filename = request.filename

    # ===============================
    # 🔹 FETCH CODE FROM URL
    # ===============================
    if request.raw_url:
        raw_url = validate_github_raw_url(request.raw_url)
        try:
            resp = await asyncio.to_thread(requests.get, raw_url, timeout=20, allow_redirects=False)
            resp.raise_for_status()
            code = resp.text
            if not filename:
                filename = raw_url.split("/")[-1] or "unknown.txt"
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Unable to fetch raw_url: {exc}")

    if not code:
        raise HTTPException(status_code=400, detail="Either raw_url or code must be provided")

    if not filename:
        filename = "snippet.txt"

    # ===============================
    # 🔹 FAST STATIC ANALYSIS
    # ===============================
    analyzer = OrchestratorAgent()
    static_analysis = analyzer.analyze(code, filename)

    language = detect_language(filename)

    # ===============================
    # 🔥 SKIP LLM (FAST RESPONSE)
    # ===============================
    if not should_use_llm(code, language):
        return {
            "filename": filename,
            "analysis": static_analysis,
            "llm_refactor": {
                "ok": True,
                "skipped": True,
                "reason": "LLM skipped (simple/json/large file)",
                "language": language,       # ✅ FIXED
                "filename": filename,       # ✅ FIXED
                "refactored_code": code,
                "summary": "LLM not required",
                "issues": []
            }
        }

    # ===============================
    # 🔹 LLM REFACTOR
    # ===============================
    agent = LLMRefractorAgent()

    try:
        llm_result = await asyncio.to_thread(
            agent.refactor,
            code,
            filename,
            static_analysis
        )

        # 🔥 SAFETY FIX (VERY IMPORTANT)
        if llm_result:
            llm_result.setdefault("filename", filename)
            llm_result.setdefault("language", language)

    except asyncio.CancelledError:
        raise HTTPException(status_code=499, detail="Client request cancelled during refactor")

    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Refactor invocation failed: {exc}")

    # ===============================
    # 🔹 FINAL RESPONSE
    # ===============================
    return {
        "filename": filename,
        "analysis": static_analysis,
        "llm_refactor": llm_result,
    }