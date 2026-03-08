import os
import uuid
from datetime import datetime, timedelta

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.api.auth.session_store import get_session
from backend.utils.env import load_project_env

# Force-load project .env values for local development.
load_project_env()

SECRET_KEY = os.getenv("JWT_SECRET")
ALGORITHM = "HS256"
JWT_EXPIRES_SECONDS = int(os.getenv("JWT_EXPIRES_SECONDS", "86400"))
OAUTH_STATE_EXPIRES_SECONDS = int(os.getenv("OAUTH_STATE_EXPIRES_SECONDS", "600"))

if not SECRET_KEY:
    raise RuntimeError("JWT_SECRET not set in environment")
if len(SECRET_KEY) < 32:
    raise RuntimeError("JWT_SECRET must be at least 32 characters")

security = HTTPBearer(auto_error=False)


def create_token(user: str, session_id: str):
    now_ts = int(datetime.utcnow().timestamp())
    payload = {
        "sub": user,
        "sid": session_id,
        "iat": now_ts,
        "exp": datetime.utcnow() + timedelta(seconds=JWT_EXPIRES_SECONDS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_oauth_state() -> str:
    now_ts = int(datetime.utcnow().timestamp())
    payload = {
        "typ": "oauth_state",
        "nonce": uuid.uuid4().hex,
        "iat": now_ts,
        "exp": datetime.utcnow() + timedelta(seconds=OAUTH_STATE_EXPIRES_SECONDS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_oauth_state(state: str) -> None:
    try:
        payload = jwt.decode(state, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="OAuth state expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    if payload.get("typ") != "oauth_state":
        raise HTTPException(status_code=400, detail="Invalid OAuth state")


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Missing bearer token")

    token = credentials.credentials

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    session_id = payload.get("sid")
    username = payload.get("sub")
    if not session_id or not username:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Session expired")

    if session.get("username") != username:
        raise HTTPException(status_code=401, detail="Invalid session")

    return payload


def get_github_token(payload: dict) -> str:
    session_id = payload.get("sid")
    if not session_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Session expired")

    github_token = session.get("github_token", "")
    if not github_token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    return github_token

