from fastapi import APIRouter, Depends, HTTPException

from backend.api.auth.jwt_manager import verify_token

router = APIRouter(prefix="/generate", tags=["Generate"])


@router.post("/")
def generate_code(user=Depends(verify_token)):
    del user
    raise HTTPException(
        status_code=501,
        detail="Code generation endpoint is not implemented yet.",
    )
