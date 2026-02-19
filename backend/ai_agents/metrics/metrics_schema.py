from pydantic import BaseModel, Field
from typing import Dict


class RepoMetricsSchema(BaseModel):
    repo_name: str = Field(description="Repository name")
    language_breakdown: Dict[str, int]
    total_files: int
    total_lines: int
    complexity_score: float
    issues: Dict[str, int]
    timestamp: str

