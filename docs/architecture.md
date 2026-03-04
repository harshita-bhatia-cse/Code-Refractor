# Architecture

## Overview
Code-Refractor is a two-tier application:
- Backend: FastAPI service for GitHub OAuth, JWT auth, repository browsing, code analysis, and LLM-based refactoring.
- Frontend: static HTML/CSS/JS client that calls backend APIs and renders repos, files, source code, analysis, and refactor output.

## Runtime Flow
1. User opens `frontend/index.html` and clicks GitHub login.
2. Backend `/auth/github/login` redirects to GitHub OAuth.
3. GitHub redirects to `/auth/github/callback`; backend exchanges code for GitHub token and issues app JWT.
4. Frontend stores JWT and requests:
   - `/repos/` to list repositories
   - `/files/{repo}` to browse contents
   - `/analyze/?raw_url=...` for static metrics
   - `/refactor/` for static + LLM refactor output

## Backend Modules
- `backend/main.py`: app composition, CORS, router registration.
- `backend/api/auth/*`: GitHub OAuth and JWT handling.
- `backend/api/routes/*`: HTTP routes for repos/files/code/analyze/refactor/profile.
- `backend/data/github_client.py`: GitHub REST API wrapper.
- `backend/ai_agents/*`: analysis and refactor agents.

## AI Analysis Layer
- `OrchestratorAgent` dispatches analysis flow.
- `Engine` performs repo-wide scanning and metrics extraction.
- `language_detector` + `language_registry` select analyzers.
- `metrics/*` computes language-specific rule metrics.
- `LLMRefractorAgent` calls OpenAI-compatible chat completion API and normalizes output.

## Storage
- Repo analysis results are written to `backend/analysis_output/repo_metrics.json`.
- No database is used currently; state is request-scoped or browser storage.
