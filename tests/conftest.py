import os

import pytest
from fastapi.testclient import TestClient

# Set env before importing the app; auth modules validate these at import time.
os.environ.setdefault("GITHUB_CLIENT_ID", "test-client-id")
os.environ.setdefault("GITHUB_CLIENT_SECRET", "test-client-secret")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret")
os.environ.setdefault("FRONTEND_URL", "http://127.0.0.1:8080")

from backend.api.auth.jwt_manager import verify_token
from backend.main import app


@pytest.fixture
def client():
    app.dependency_overrides.clear()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def authed_client(client):
    app.dependency_overrides[verify_token] = lambda: {
        "sub": "test-user",
        "github_token": "test-gh-token",
    }
    return client
