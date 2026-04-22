from fastapi import APIRouter, Depends, HTTPException, Query

from backend.api.auth.jwt_manager import get_github_token, verify_token
from backend.data.github_client import GitHubClient, GitHubAPIError

router = APIRouter(prefix="/files", tags=["Files"])


@router.get("/{repo_name}")
def get_files(
    repo_name: str,
    owner: str | None = Query(
        None,
        description="Repo owner (GitHub login). If omitted, defaults to the authenticated user.",
    ),
    path: str = Query("", description="Folder path"),
    payload: dict = Depends(verify_token)
):
    github_token = get_github_token(payload)
    username = payload.get("sub")

    if not github_token or not username:
        raise HTTPException(status_code=401, detail="Unauthorized")

    client = GitHubClient(github_token)
    resolved_owner = owner or username
    try:
        items = client.get_repo_contents(resolved_owner, repo_name, path)
    except GitHubAPIError as exc:
        if exc.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail=f"Repository/path not found: {resolved_owner}/{repo_name}/{path}".rstrip("/"),
            )
        if exc.status_code == 401:
            raise HTTPException(status_code=401, detail="GitHub authentication failed")
        raise HTTPException(status_code=502, detail=f"GitHub API error: {exc.message}")

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
