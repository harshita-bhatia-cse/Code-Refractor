from pathlib import Path

from dotenv import load_dotenv


def load_project_env() -> None:
    """Load environment variables from repo root `.env` and then `backend/.env`.

    Loading backend/.env second lets backend-specific secrets (like real GitHub
    client credentials) override placeholder values that might live in the root
    file. This way you set the ID once in either place and avoid editing both.
    """
    backend_dir = Path(__file__).resolve().parents[1]
    repo_root = backend_dir.parent

    root_env = repo_root / ".env"
    backend_env = backend_dir / ".env"

    if root_env.exists():
        load_dotenv(root_env)
    if backend_env.exists():
        # override so backend/.env can replace placeholders from the root file
        load_dotenv(backend_env, override=True)
