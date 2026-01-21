from fastapi import APIRouter, Depends
from backend.api.auth.jwt_manager import verify_token

router = APIRouter(prefix="/profile", tags=["Profile"])

@router.get("/")
# def get_profile():
#     return {
#         "name": "Harshita",
#         "role": "Backend + AI Developer",
#         "status": "Profile route working"
#     }
def get_profile(user_id: str = Depends(verify_token)):
    return {
        "user": user_id,
        "status": "JWT protected profile"
    }