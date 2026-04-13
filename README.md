# Code-Refractor

AI-assisted code analysis and refactoring tool with:
- FastAPI backend
- static HTML/JS frontend
- GitHub OAuth + JWT auth
- rule-based multi-language metrics
- LLM-based refactor suggestions with RAG-powered context retrieval (FAISS)

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
- (optional) `LLM_EMBED_MODEL` for RAG embeddings (default: `all-MiniLM-L6-v2`)

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

Key runtime deps for RAG:
- `sentence-transformers`
- `faiss-cpu`
- `numpy`

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
   - RAG pipeline: chunk → embed → FAISS index → retrieve relevant context → inject into LLM prompt.
5. Optionally run repo-level analysis (`/analyze-repo`).

## Recent Changes (RAG Upgrade)
- Replaced naive character-based chunking in `LLMRefractorAgent` with a Retrieval-Augmented Generation pipeline.
- Added `backend/ai_agents/rag/` (chunker, embedder, vector store, retriever, pipeline).
- Prompt now includes top relevant chunks before target code to improve context and reduce tokens.
- Added optional fallbacks (hash embeddings, numpy-less cosine) to keep runtime resilient if deps are missing.

## Notes
- Keep `.env` private; never commit real secrets.
- If `langchain-groq` is unavailable, app still starts; repo-level AI reasoning falls back safely.
