import os
import jwt
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pathlib import Path
from dotenv import load_dotenv

# Force load backend/.env
load_dotenv(Path(__file__).resolve().parents[2] / '.env')

SECRET_KEY = os.getenv("JWT_SECRET")
ALGORITHM = "HS256"

if not SECRET_KEY:
    raise RuntimeError("JWT_SECRET not set in environment")

security = HTTPBearer()

def create_token(user: str, github_token: str):
    payload = {
        "sub": user,
        "github_token": github_token,
        "exp": datetime.utcnow() + timedelta(days=1)
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    print("JWT created for user:", user)

    return token

def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        print("JWT verified for user:", payload.get("sub"))

        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")

    except jwt.InvalidTokenError as e:
        print("JWT verify failed:", str(e))
        raise HTTPException(status_code=401, detail="Invalid token")

