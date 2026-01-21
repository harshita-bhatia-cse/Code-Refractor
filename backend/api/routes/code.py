from fastapi import APIRouter, Depends, HTTPException
from backend.api.auth.jwt_manager import verify_token
from backend.data.github_client import GitHubClient

router = APIRouter(prefix="/code", tags=["Code"])


@router.get("/")
def get_code(raw_url: str, payload: dict = Depends(verify_token)):
    github_token = payload.get("github_token")

    if not github_token:
        raise HTTPException(status_code=401, detail="Login again")

    client = GitHubClient(github_token)
    result = client.get_file_content(raw_url)

    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["message"])

    return {
        "raw_url": raw_url,
        "code": result["content"]
    }
