from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class FileStyleMetrics(BaseModel):
    path: str
    language: str
    naming_counts: dict[str, int] = Field(default_factory=dict)
    indentation_counts: dict[str, int] = Field(default_factory=dict)
    line_count: int = 0
    avg_function_length: float = 0.0
    function_count: int = 0
    comment_density: float = 0.0
    comment_styles: dict[str, int] = Field(default_factory=dict)
    structure_counts: dict[str, int] = Field(default_factory=dict)
    frontend_group: str | None = None


class StyleProfile(BaseModel):
    naming: str = "mixed"
    indentation: str = "unknown"
    comments: str = "balanced"
    structure: str = "mixed"
    function_style: str = "moderate"
    languages: list[str] = Field(default_factory=list)
    repositories_analyzed: int = 0
    files_analyzed: int = 0
    confidence: float = 0.0
    evidence: dict[str, Any] = Field(default_factory=dict)

    def to_prompt_text(self) -> str:
        return (
            f"Naming convention: {self.naming}\n"
            f"Indentation: {self.indentation}\n"
            f"Comment style: {self.comments}\n"
            f"Code structure: {self.structure}\n"
            f"Function style: {self.function_style}\n"
            f"Languages observed: {', '.join(self.languages) or 'unknown'}\n"
            f"Confidence: {self.confidence:.2f}"
        )
