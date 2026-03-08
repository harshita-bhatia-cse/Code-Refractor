import os
import urllib.parse
import uuid

import requests
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

from backend.api.auth.jwt_manager import JWT_EXPIRES_SECONDS, create_oauth_state, create_token, verify_oauth_state
from backend.api.auth.session_store import put_session
from backend.utils.env import load_project_env

load_project_env()

router = APIRouter(prefix="/auth/github", tags=["GitHub Auth"])

CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
FRONTEND_URL = os.getenv("FRONTEND_URL")

missing = []
if not CLIENT_ID:
    missing.append("GITHUB_CLIENT_ID")
if not CLIENT_SECRET:
    missing.append("GITHUB_CLIENT_SECRET")
if not FRONTEND_URL:
    missing.append("FRONTEND_URL")
if missing:
    raise RuntimeError(f"Missing environment variables: {', '.join(missing)}")


@router.get("/login")
def github_login():
    state = create_oauth_state()
    query = urllib.parse.urlencode(
        {
            "client_id": CLIENT_ID,
            "scope": "repo",
            "state": state,
        }
    )
    return RedirectResponse(f"https://github.com/login/oauth/authorize?{query}")


@router.get("/callback")
def github_callback(code: str, state: str):
    verify_oauth_state(state)

    token_response = requests.post(
        "https://github.com/login/oauth/access_token",
        headers={"Accept": "application/json"},
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "code": code,
        },
        timeout=10,
    )

    token_data = token_response.json()
    github_token = token_data.get("access_token")
    if not github_token:
        raise HTTPException(status_code=400, detail="Failed to obtain GitHub access token")

    user_response = requests.get(
        "https://api.github.com/user",
        headers={
            "Authorization": f"Bearer {github_token}",
            "Accept": "application/json",
        },
        timeout=10,
    )
    user_data = user_response.json()
    username = user_data.get("login")
    if not username:
        raise HTTPException(status_code=400, detail="Failed to fetch GitHub user")

    session_id = uuid.uuid4().hex
    put_session(
        session_id=session_id,
        username=username,
        github_token=github_token,
        ttl_seconds=JWT_EXPIRES_SECONDS,
    )
    jwt_token = create_token(user=username, session_id=session_id)

    fragment = urllib.parse.urlencode({"token": jwt_token, "user": username})
    redirect_url = f"{FRONTEND_URL}/dashboard.html#{fragment}"
    return RedirectResponse(url=redirect_url)
