from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class FileLanguageAnalysis(BaseModel):
    start_lines: List[int]
    metrics: Dict[str, Any]


class AnalyzeResponse(BaseModel):
    languages_detected: List[str]
    analysis: Dict[str, FileLanguageAnalysis]


class LLMRefactorResult(BaseModel):
    ok: bool
    language: str
    filename: str
    error: Optional[str] = None
    summary: str
    issues: List[str]
    refactored_code: str
    raw_output: Optional[str] = None


class RefactorResponse(BaseModel):
    filename: str
    analysis: AnalyzeResponse
    llm_refactor: LLMRefactorResult


class AnalyzeRepoResponse(BaseModel):
    message: str
    result: Dict[str, Any]
