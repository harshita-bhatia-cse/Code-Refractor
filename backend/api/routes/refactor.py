from typing import Optional
import asyncio
import requests

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.ai_agents.core.language_detector import detect_language
from backend.ai_agents.orchestrator import OrchestratorAgent
from backend.ai_agents.refractor.refractor_agent import LLMRefractorAgent
from backend.ai_agents.style.profile import StyleProfile
from backend.ai_agents.style.profile_builder import StyleProfileBuilder
from backend.ai_agents.style.style_analyzer import StyleAnalyzer
from backend.api.auth.jwt_manager import verify_token
from backend.api.schemas.analysis import RefactorResponse
from backend.utils.url_validation import validate_github_raw_url

router = APIRouter(prefix="/refactor", tags=["AI Refactor"])


class RefactorRequest(BaseModel):
    raw_url: Optional[str] = None
    code: Optional[str] = None
    filename: Optional[str] = None
    style_profile: Optional[dict] = None


def should_use_llm(code: str, language: str) -> bool:
    del code
    if language == "json":
        return False
    return True


@router.post("/", response_model=RefactorResponse)
async def refactor_code(request: RefactorRequest, user=Depends(verify_token)):
    del user

    code = request.code
    filename = request.filename

    if request.raw_url:
        raw_url = validate_github_raw_url(request.raw_url)
        try:
            resp = await asyncio.to_thread(
                requests.get,
                raw_url,
                timeout=20,
                allow_redirects=False,
            )
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

    analyzer = OrchestratorAgent()
    static_analysis = analyzer.analyze(code, filename)
    language = detect_language(filename)
    style_profile = _resolve_style_profile(request.style_profile, code, filename)

    if not should_use_llm(code, language):
        return {
            "filename": filename,
            "analysis": static_analysis,
            "llm_refactor": {
                "ok": True,
                "fallback": False,
                "skipped": True,
                "reason": "LLM skipped for simple or JSON input",
                "language": language,
                "filename": filename,
                "refactored_code": code,
                "summary": "LLM not required",
                "issues": [],
                "style_profile": style_profile.model_dump(),
            },
        }

    agent = LLMRefractorAgent()

    try:
        llm_result = await asyncio.to_thread(
            agent.refactor,
            code,
            filename,
            static_analysis,
            style_profile,
        )
        llm_result.setdefault("filename", filename)
        llm_result.setdefault("language", language)
    except asyncio.CancelledError:
        raise HTTPException(status_code=499, detail="Client request cancelled during refactor")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Refactor invocation failed: {exc}")

    return {
        "filename": filename,
        "analysis": static_analysis,
        "llm_refactor": llm_result,
    }


def _resolve_style_profile(
    profile_payload: Optional[dict],
    code: str,
    filename: str,
) -> StyleProfile:
    if profile_payload:
        return StyleProfile(**profile_payload)

    file_style = StyleAnalyzer().analyze_file(filename, code)
    return StyleProfileBuilder().build_from_file_metrics([file_style], repositories_analyzed=0)
