from pydantic import BaseModel

class RepoAnalyzeRequest(BaseModel):
    repo_path: str
