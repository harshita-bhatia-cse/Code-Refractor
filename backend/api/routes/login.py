from fastapi import APIRouter
from backend.api.auth.jwt_manager import create_access_token

router = APIRouter(prefix="/login", tags=["Auth"])

@router.post("/")
def login():
    token = create_access_token(
        user_id="harshita",
        github_token="dummy_token_for_testing"
    )
    return {
        "access_token": token,
        "token_type": "bearer"
    }
