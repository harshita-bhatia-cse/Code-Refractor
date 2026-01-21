from fastapi import APIRouter, Depends, HTTPException
from backend.api.auth.jwt_manager import verify_token
from backend.data.github_client import GitHubClient

router = APIRouter(prefix="/repos", tags=["Repositories"])


@router.get("/")
def list_repos(payload: dict = Depends(verify_token)):
    print("=== /repos CALLED ===")
    print("PAYLOAD:", payload)

    github_token = payload.get("github_token")

    if not github_token:
        print("❌ NO GITHUB TOKEN")
        raise HTTPException(401, "GitHub token missing")

    client = GitHubClient(github_token)
    repos = client.list_repos()

    print("REPOS FROM GITHUB:", repos)

    return repos
