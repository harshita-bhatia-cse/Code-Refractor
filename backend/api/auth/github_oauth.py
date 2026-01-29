import os
import requests
import urllib.parse

from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv

from backend.api.auth.jwt_manager import create_token

# --------------------------------------------------
# Load environment variables
# --------------------------------------------------
load_dotenv()

router = APIRouter(prefix="/auth/github", tags=["GitHub Auth"])

# --------------------------------------------------
# Environment variables
# --------------------------------------------------
CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
FRONTEND_URL = os.getenv("FRONTEND_URL")

# --------------------------------------------------
# Validate env variables (FAIL FAST)
# --------------------------------------------------
missing = []
if not CLIENT_ID:
    missing.append("GITHUB_CLIENT_ID")
if not CLIENT_SECRET:
    missing.append("GITHUB_CLIENT_SECRET")
if not FRONTEND_URL:
    missing.append("FRONTEND_URL")

if missing:
    raise RuntimeError(f"Missing environment variables: {', '.join(missing)}")

# --------------------------------------------------
# GitHub Login
# --------------------------------------------------
@router.get("/login")
def github_login():
    github_auth_url = (
        "https://github.com/login/oauth/authorize"
        f"?client_id={CLIENT_ID}&scope=repo"
    )
    return RedirectResponse(github_auth_url)

# --------------------------------------------------
# GitHub OAuth Callback
# --------------------------------------------------
@router.get("/callback")
def github_callback(code: str):
    # 1️⃣ Exchange code for GitHub access token
    token_response = requests.post(
        "https://github.com/login/oauth/access_token",
        headers={"Accept": "application/json"},
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "code": code
        },
        timeout=10
    )

    token_data = token_response.json()
    github_token = token_data.get("access_token")

    if not github_token:
        raise HTTPException(
            status_code=400,
            detail="Failed to obtain GitHub access token"
        )

    # 2️⃣ Fetch GitHub user info
    user_response = requests.get(
        "https://api.github.com/user",
        headers={
            "Authorization": f"Bearer {github_token}",
            "Accept": "application/json"
        },
        timeout=10
    )

    user_data = user_response.json()
    username = user_data.get("login")

    if not username:
        raise HTTPException(
            status_code=400,
            detail="Failed to fetch GitHub user"
        )

    # 3️⃣ Create JWT for your app
    jwt_token = create_token(
        user=username,
        github_token=github_token
    )

    # 4️⃣ Redirect to frontend dashboard
    query_params = urllib.parse.urlencode({
        "token": jwt_token,
        "user": username
    })

    redirect_url = f"{FRONTEND_URL}/dashboard.html?{query_params}"
    return RedirectResponse(url=redirect_url)
