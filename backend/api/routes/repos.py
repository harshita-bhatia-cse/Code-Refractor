from fastapi import APIRouter, Depends, HTTPException

from backend.api.auth.jwt_manager import get_github_token, verify_token
from backend.data.github_client import GitHubClient, GitHubAPIError

router = APIRouter(prefix="/repos", tags=["Repos"])

@router.get("/")
def list_repos(payload: dict = Depends(verify_token)):
    github_token = get_github_token(payload)
    username = payload.get("sub")

    if not github_token or not username:
        raise HTTPException(status_code=401, detail="Unauthorized")

    client = GitHubClient(github_token)
    try:
        repos = client.get_repositories()
    except GitHubAPIError as exc:
        status = 401 if exc.status_code == 401 else 502
        detail = (
            "GitHub authentication failed: bad credentials"
            if status == 401
            else f"GitHub API error: {exc.message}"
        )
        raise HTTPException(status_code=status, detail=detail)

    return repos
