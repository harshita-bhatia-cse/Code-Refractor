from fastapi import APIRouter, Depends, HTTPException, Query
from backend.api.auth.jwt_manager import verify_token
from backend.data.github_client import GitHubClient

router = APIRouter(prefix="/code", tags=["Code"])


@router.get("/")
def get_code(
    raw_url: str = Query(...),
    payload: dict = Depends(verify_token)
):
    if not raw_url or raw_url == "undefined":
        raise HTTPException(status_code=400, detail="Invalid raw_url")

    github_token = payload.get("github_token")
    if not github_token:
        raise HTTPException(status_code=401, detail="Login again")

    client = GitHubClient(github_token)

    try:
        result = client.get_file_content(raw_url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["message"])

    return {
        "raw_url": raw_url,
        "code": result.get("content", "")
    }
