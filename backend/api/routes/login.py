from backend.database import users_collection
from datetime import datetime

async def save_user(user):
    print("Saving user:", user)

    existing_user = await users_collection.find_one({
        "github_id": user["id"]
    })

    if not existing_user:

        new_user = {
            "github_id": user["id"],
            "username": user["login"],
            "email": user.get("email"),
            "avatar": user.get("avatar_url"),
            "created_at": datetime.utcnow(),
            "last_login": datetime.utcnow()
        }

        await users_collection.insert_one(new_user)

    else:
        await users_collection.update_one(
            {"github_id": user["id"]},
            {"$set": {"last_login": datetime.utcnow()}}
        )

    return True

from fastapi import APIRouter, Body
import uuid

from backend.api.auth.jwt_manager import create_token
from backend.api.auth.session_store import put_session


router = APIRouter(prefix="/login", tags=["Auth"])


@router.post("/")
async def login(username: str = Body(...)):

    user_data = {
        "id": username,
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