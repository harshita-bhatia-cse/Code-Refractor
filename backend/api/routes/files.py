from fastapi import APIRouter, Depends, HTTPException
from backend.api.auth.jwt_manager import verify_token
from backend.data.github_client import GitHubClient

router = APIRouter(prefix="/files", tags=["Files"])


@router.get("/{repo_name}")
def get_files(repo_name: str, payload: dict = Depends(verify_token)):
    github_token = payload.get("github_token")
    user_id = payload.get("sub")

    if not github_token:
        raise HTTPException(status_code=401, detail="Login again")

    client = GitHubClient(github_token)
    contents = client.get_repo_contents(user_id, repo_name)

    if isinstance(contents, dict) and contents.get("error"):
        raise HTTPException(status_code=400, detail=contents["message"])

    files = []
    for item in contents:
        if item.get("type") == "file":
            files.append({
                "name": item.get("name"),
                "path": item.get("path"),
                "url": item.get("download_url")
            })

    return files
