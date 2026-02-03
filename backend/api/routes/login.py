from fastapi import APIRouter, Body
from backend.api.auth.jwt_manager import create_access_token

router = APIRouter(prefix="/login", tags=["Auth"])


@router.post("/")
def login(username: str = Body(...)):
    token = create_access_token(
        user_id=username,
        github_token=None
    )

    return {
        "access_token": token,
        "token_type": "bearer"
    }
