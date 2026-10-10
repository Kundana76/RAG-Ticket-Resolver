import os

# Must be set before the app is imported
os.environ.setdefault("AUTH_SECRET", "test-secret-not-for-production")
os.environ.setdefault("WEBHOOK_SECRET", "hook-secret")

import pytest
from fastapi.testclient import TestClient

from copilot.copilot_api import app


@pytest.fixture(scope="session")
def client():
    return TestClient(app)


@pytest.fixture(scope="session")
def admin_headers(client):
    """First registered account becomes admin (or log in if an earlier test created it)."""
    r = client.post("/auth/register", json={"username": "boss", "password": "correct-horse-1"})
    if r.status_code != 200:
        r = client.post("/auth/login", json={"username": "boss", "password": "correct-horse-1"})
    return {"Authorization": f"Bearer {r.json()['token']}"}
