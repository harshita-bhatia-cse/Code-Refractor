from fastapi import APIRouter, Depends, HTTPException, Query
from backend.api.auth.jwt_manager import verify_token
from backend.data.github_client import GitHubClient

router = APIRouter(prefix="/files", tags=["Files"])


@router.get("/{repo_name}")
def get_files(
    repo_name: str,
    path: str = Query("", description="Folder path"),
    payload: dict = Depends(verify_token)
):
    github_token = payload.get("github_token")
    username = payload.get("sub")

    if not github_token or not username:
        raise HTTPException(status_code=401, detail="Unauthorized")

    client = GitHubClient(github_token)

    items = client.get_repo_contents(username, repo_name, path)

    if not isinstance(items, list):
        raise HTTPException(status_code=400, detail="Invalid GitHub response")

    result = []
    for item in items:
        result.append({
            "name": item["name"],
            "path": item["path"],
            "type": item["type"],
            # ✅ ALWAYS return raw_url for files
            "raw_url": item.get("download_url")
        })

    return result
