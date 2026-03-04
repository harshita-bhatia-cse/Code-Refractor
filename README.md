# Code-Refractor

AI-assisted code analysis and refactoring tool with:
- FastAPI backend
- static HTML/JS frontend
- GitHub OAuth + JWT auth
- rule-based multi-language metrics
- LLM-based refactor suggestions

## Prerequisites
- Python 3.11+
- GitHub OAuth app credentials

## Environment
Create `.env` in repository root using `.env.example` as template.

Required keys:
- `GITHUB_CLIENT_ID`
- `GITHUB_CLIENT_SECRET`
- `JWT_SECRET`
- `FRONTEND_URL` (for local: `http://127.0.0.1:8080`)
- `LLM_API_KEY`
- `LLM_MODEL`
- `LLM_BASE_URL`

Optional:
- `CORS_ALLOW_ORIGINS` (comma-separated origins)

## Install
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

## Run Locally (Clean Path)
Open two terminals from repository root.

Terminal 1 (backend):
```bash
uvicorn backend.main:app --reload --port 8000
```

Terminal 2 (frontend static server):
```bash
python -m http.server 8080 --directory frontend
```

Open:
- Frontend: `http://127.0.0.1:8080/index.html`
- API docs: `http://127.0.0.1:8000/docs`

## Run Tests
```bash
python -m pytest -q
```

## High-Level Flow
1. Login via GitHub OAuth.
2. Browse repositories and files.
3. Run file-level analysis (`/analyze`).
4. Run LLM refactor (`/refactor`).
5. Optionally run repo-level analysis (`/analyze-repo`).

## Notes
- Keep `.env` private; never commit real secrets.
- If `langchain-groq` is unavailable, app still starts; repo-level AI reasoning falls back safely.
