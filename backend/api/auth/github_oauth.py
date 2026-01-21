from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv
import os
import requests
import urllib.parse

from backend.api.auth.jwt_manager import create_access_token

load_dotenv()

router = APIRouter(prefix="/auth/github", tags=["GitHub Auth"])

CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")

if not CLIENT_ID or not CLIENT_SECRET:
    raise RuntimeError("GitHub OAuth credentials missing")


@router.get("/login")
def github_login():
    url = (
        "https://github.com/login/oauth/authorize"
        f"?client_id={CLIENT_ID}&scope=repo"
    )
    return RedirectResponse(url)


@router.get("/callback")
def github_callback(code: str):
    # 1️⃣ Exchange code for token
    token_res = requests.post(
        "https://github.com/login/oauth/access_token",
        headers={"Accept": "application/json"},
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "code": code,
        },
    ).json()

    github_token = token_res.get("access_token")
    if not github_token:
        raise HTTPException(status_code=400, detail="GitHub token not received")

    # 2️⃣ Fetch user
    user_res = requests.get(
        "https://api.github.com/user",
        headers={"Authorization": f"Bearer {github_token}"},
    ).json()

    username = user_res.get("login")
    if not username:
        raise HTTPException(status_code=400, detail="GitHub user not found")

    # 3️⃣ CREATE JWT (THIS LINE IS CRITICAL)
    jwt_token = create_access_token(
        user_id=username,
        github_token=github_token
    )

    # 4️⃣ Redirect to frontend
    frontend_url = "http://127.0.0.1:8080/dashboard.html"
    params = {
        "token": jwt_token,
        "user": username
    }

    redirect_url = f"{frontend_url}?{urllib.parse.urlencode(params)}"
    return RedirectResponse(url=redirect_url)
