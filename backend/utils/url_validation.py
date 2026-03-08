from urllib.parse import urlparse

from fastapi import HTTPException

ALLOWED_RAW_HOSTS = {
    "raw.githubusercontent.com",
    "gist.githubusercontent.com",
}


def validate_github_raw_url(raw_url: str) -> str:
    if not raw_url:
        raise HTTPException(status_code=400, detail="raw_url is required")

    parsed = urlparse(raw_url.strip())
    if parsed.scheme != "https":
        raise HTTPException(status_code=400, detail="raw_url must use https")

    if parsed.hostname not in ALLOWED_RAW_HOSTS:
        raise HTTPException(status_code=400, detail="raw_url host is not allowed")

    if not parsed.path or parsed.path == "/":
        raise HTTPException(status_code=400, detail="raw_url path is invalid")

    return raw_url.strip()
