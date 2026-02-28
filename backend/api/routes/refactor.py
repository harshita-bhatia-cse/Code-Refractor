from typing import Optional

import requests
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.ai_agents.orchestrator import OrchestratorAgent
from backend.ai_agents.refractor.refractor_agent import LLMRefractorAgent
from backend.api.auth.jwt_manager import verify_token

router = APIRouter(prefix="/refactor", tags=["AI Refactor"])


class RefactorRequest(BaseModel):
    raw_url: Optional[str] = None
    code: Optional[str] = None
    filename: Optional[str] = None


@router.post("/")
def refactor_code(request: RefactorRequest, user=Depends(verify_token)):
    del user

    code = request.code
    filename = request.filename

    if request.raw_url:
        raw_url = request.raw_url.strip()
        if not raw_url.startswith("http"):
            raise HTTPException(status_code=400, detail="raw_url must be a valid http(s) URL")
        try:
            resp = requests.get(raw_url, timeout=20)
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

    agent = LLMRefractorAgent()
    llm_result = agent.refactor(code=code, filename=filename, analysis=static_analysis)

    return {
        "filename": filename,
        "analysis": static_analysis,
        "llm_refactor": llm_result,
    }
