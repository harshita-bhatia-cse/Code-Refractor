from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# 🔥 ADD THIS BLOCK
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  #temp allow everything
    allow_credentials=False,
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
