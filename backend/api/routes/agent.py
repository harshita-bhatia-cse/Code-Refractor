from fastapi import APIRouter, Depends
from backend.api.auth.jwt_manager import verify_token

router = APIRouter(prefix="/agent", tags=["AI Agent"])

@router.post("/analyze")
def analyze_code(payload: dict, user=Depends(verify_token)):
    code = payload.get("code")

    if not code:
        return {"error": "No code received"}

    return {
        "message": "AI agent successfully accessed the code",
        "lines": len(code.splitlines()),
        "characters": len(code),
        "preview": code[:300]
    }
