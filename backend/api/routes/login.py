from fastapi import APIRouter, Body
import uuid

from backend.api.auth.jwt_manager import create_token
from backend.api.auth.session_store import put_session

router = APIRouter(prefix="/login", tags=["Auth"])


@router.post("/")
def login(username: str = Body(...)):
    session_id = uuid.uuid4().hex
    put_session(session_id=session_id, username=username, github_token="", ttl_seconds=3600)
    token = create_token(user=username, session_id=session_id)

    return {
        "access_token": token,
        "token_type": "bearer"
    }
