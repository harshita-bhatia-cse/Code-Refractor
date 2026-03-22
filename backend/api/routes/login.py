from backend.database import cursor, conn

async def save_user(user):
    print("Saving user:", user)

    github_id = str(user.get("id")) if user.get("id") else user.get("login")

    cursor.execute("""
    INSERT OR REPLACE INTO users (github_id, email, name, avatar)
    VALUES (?, ?, ?, ?)
    """, (
        github_id,
        user.get("email"),
        user.get("login"),
        user.get("avatar_url")
    ))

    conn.commit()

    return True

from fastapi import APIRouter, Body
import uuid

from backend.api.auth.jwt_manager import create_token
from backend.api.auth.session_store import put_session


router = APIRouter(prefix="/login", tags=["Auth"])


@router.post("/")
async def login(username: str = Body(...)):

    user_data = {
    "id": f"local_{username}", 
    "login": username,
    "email": None,
    "avatar_url": None
}

    await save_user(user_data)

    session_id = uuid.uuid4().hex

    put_session(
        session_id=session_id,
        username=username,
        github_token="",
        ttl_seconds=3600
    )

    token = create_token(user=username, session_id=session_id)

    return {
        "access_token": token,
        "token_type": "bearer"
    }