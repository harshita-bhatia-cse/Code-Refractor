import os
import urllib.parse
import uuid

import requests
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from backend.api.auth.jwt_manager import (
    JWT_EXPIRES_SECONDS,
    create_oauth_state,
    create_token,
    verify_oauth_state,
)
from backend.api.auth.session_store import put_session
from backend.utils.env import load_project_env

load_project_env()

router = APIRouter(prefix="/auth/github", tags=["GitHub Auth"])

# Requests session with mild retries to survive transient network hiccups
_session = requests.Session()
_session.mount(
    "https://",
    HTTPAdapter(
        max_retries=Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
        ),
    ),
)
_session.mount("http://", _session.get_adapter("https://"))

# Default timeouts: (connect, read)
REQUEST_TIMEOUT = (10, 20)

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

    try:
        token_response = _session.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "code": code,
            },
            timeout=REQUEST_TIMEOUT,
        )
        token_response.raise_for_status()
    except requests.exceptions.Timeout as exc:
        raise HTTPException(status_code=504, detail="GitHub token request timed out") from exc
    except requests.exceptions.RequestException as exc:
        raise HTTPException(status_code=502, detail="GitHub token request failed") from exc

    token_data = token_response.json()
    github_token = token_data.get("access_token")
    if not github_token:
        raise HTTPException(status_code=400, detail="Failed to obtain GitHub access token")

    try:
        user_response = _session.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {github_token}",
                "Accept": "application/json",
            },
            timeout=REQUEST_TIMEOUT,
        )
        user_response.raise_for_status()
    except requests.exceptions.Timeout as exc:
        raise HTTPException(status_code=504, detail="GitHub user request timed out") from exc
    except requests.exceptions.RequestException as exc:
        raise HTTPException(status_code=502, detail="GitHub user request failed") from exc

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
