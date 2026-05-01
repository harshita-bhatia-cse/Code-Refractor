import os
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .utils.env import load_project_env

load_project_env()

app = FastAPI()

frontend_url = os.getenv("FRONTEND_URL", "").strip()
cors_env = os.getenv("CORS_ALLOW_ORIGINS", "").strip()

if cors_env:
    allow_origins = [item.strip().rstrip("/") for item in cors_env.split(",") if item.strip()]
else:
    allow_origins = [
        "http://127.0.0.1:8080",
        "http://localhost:8080",
    ]
    if frontend_url:
        allow_origins.append(frontend_url)

allow_origin_regex = r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"

app.add_middleware(
    CORSMiddleware,
    allow_origins=sorted(set(allow_origins)),
    allow_origin_regex=allow_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from backend.api.auth.github_oauth import router as github_router
from backend.api.routes.repos import router as repos_router
from backend.api.routes.files import router as files_router
from backend.api.routes.code import router as code_router
from backend.api.routes.profile import router as profile_router
from backend.api.routes.login import router as login_router
from backend.api.routes import analyze
from backend.api.routes import generate
from backend.api.routes import refactor
from backend.api.routes import repo_analyze

app.include_router(github_router)
app.include_router(repos_router)
app.include_router(files_router)
app.include_router(code_router)
app.include_router(profile_router)
app.include_router(login_router)
app.include_router(analyze.router)
app.include_router(repo_analyze.router)
app.include_router(refactor.router)
app.include_router(generate.router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def root():
    return {"message": "Code Refractor Backend Running"}
