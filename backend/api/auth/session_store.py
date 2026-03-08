import time
from threading import Lock
from typing import Optional

_STORE = {}
_LOCK = Lock()


def _is_expired(entry: dict) -> bool:
    return int(entry.get("exp", 0)) <= int(time.time())


def put_session(session_id: str, username: str, github_token: str, ttl_seconds: int) -> None:
    exp = int(time.time()) + max(1, int(ttl_seconds))
    with _LOCK:
        _STORE[session_id] = {
            "username": username,
            "github_token": github_token,
            "exp": exp,
        }


def get_session(session_id: str) -> Optional[dict]:
    with _LOCK:
        entry = _STORE.get(session_id)
        if not entry:
            return None
        if _is_expired(entry):
            _STORE.pop(session_id, None)
            return None
        return entry


def delete_session(session_id: str) -> None:
    with _LOCK:
        _STORE.pop(session_id, None)
