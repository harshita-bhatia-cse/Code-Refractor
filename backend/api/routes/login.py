from fastapi import APIRouter, Body
from backend.api.auth.jwt_manager import create_token

router = APIRouter(prefix="/login", tags=["Auth"])


@router.post("/")
def login(username: str = Body(...)):
    token = create_token(user=username, github_token="")

    return {
        "access_token": token,
        "token_type": "bearer"
    }
