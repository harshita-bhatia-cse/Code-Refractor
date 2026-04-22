from backend.utils.env import load_project_env

load_project_env()

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

frontend_url = os.getenv("FRONTEND_URL", "").strip()
cors_env = os.getenv("CORS_ALLOW_ORIGINS", "").strip()
if cors_env:
    # Normalize env-provided origins (people often include a trailing slash).
    allow_origins = [item.strip().rstrip("/") for item in cors_env.split(",") if item.strip()]
    # Still allow any localhost/127.0.0.1 port in dev to avoid surprises when
    # Vite picks a different port (5173/5174/8080) or the user switches hosts.
    allow_origin_regex = r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"
else:
    allow_origins = [
        "http://127.0.0.1:8080",
        "http://localhost:8080",
    ]
    if frontend_url:
        allow_origins.append(frontend_url)
    # Dev-friendly: Vite may choose a different port (e.g. 5173/5174),
    # and users may open either localhost or 127.0.0.1. Allow both.
    allow_origin_regex = r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"

app.add_middleware(
    CORSMiddleware,
    allow_origins=sorted(set(allow_origins)),
    allow_origin_regex=allow_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# routers
from backend.api.auth.github_oauth import router as github_router
from backend.api.routes.repos import router as repos_router
from backend.api.routes.files import router as files_router
from backend.api.routes.code import router as code_router
from backend.api.routes.profile import router as profile_router

app.include_router(github_router)
app.include_router(repos_router)
app.include_router(files_router)
app.include_router(code_router)
app.include_router(profile_router)


from backend.api.routes import analyze
app.include_router(analyze.router)

from backend.api.routes import repo_analyze
app.include_router(repo_analyze.router)

from backend.api.routes import refactor
app.include_router(refactor.router)

from backend.api.routes import generate
app.include_router(generate.router)

# from backend.api.routes import agent
# app.include_router(agent.router)

