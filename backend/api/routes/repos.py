from fastapi import APIRouter, Depends, HTTPException

from backend.api.auth.jwt_manager import get_github_token, verify_token
from backend.data.github_client import GitHubClient

router = APIRouter(prefix="/repos", tags=["Repos"])

@router.get("/")
def list_repos(payload: dict = Depends(verify_token)):
    github_token = get_github_token(payload)
    username = payload.get("sub")

    if not github_token or not username:
        raise HTTPException(status_code=401, detail="Unauthorized")

    client = GitHubClient(github_token)
    repos = client.get_repositories()

    return repos
