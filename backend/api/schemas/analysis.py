from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class FileLanguageAnalysis(BaseModel):
    start_lines: List[int]
    metrics: Dict[str, Any]
    quality_score: Optional[int] = None
    grade: Optional[str] = None
    risk_badges: List[str] = Field(default_factory=list)


class AnalyzeResponse(BaseModel):
    languages_detected: List[str]
    overall_quality_score: Optional[int] = None
    overall_grade: Optional[str] = None
    overall_risk_badges: List[str] = Field(default_factory=list)
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
