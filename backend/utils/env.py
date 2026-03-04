from pathlib import Path

from dotenv import load_dotenv


def load_project_env() -> None:
    """Load environment variables from repo root `.env`, fallback to `backend/.env`."""
    backend_dir = Path(__file__).resolve().parents[1]
    repo_root = backend_dir.parent

    root_env = repo_root / ".env"
    backend_env = backend_dir / ".env"

    if root_env.exists():
        load_dotenv(root_env)
    elif backend_env.exists():
        load_dotenv(backend_env)
