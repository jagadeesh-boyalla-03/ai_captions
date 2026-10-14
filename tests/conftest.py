"""
Pytest configuration and fixtures for testing Social Caption API and authentication.
"""

import os
import io
import sys
import pytest
from PIL import Image

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastapi.testclient import TestClient

@pytest.fixture(autouse=True)
def isolated_test_db(tmp_path, monkeypatch):
    """Sets up an isolated JSON data directory for each test run."""
    from api import index
    monkeypatch.setattr(index, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(index, "USERS_FILE", str(tmp_path / "users.json"))
    monkeypatch.setattr(index, "HISTORY_FILE", str(tmp_path / "history.json"))
    monkeypatch.setattr(index, "SESSIONS_FILE", str(tmp_path / "sessions.json"))
    monkeypatch.setenv("GEMINI_API_KEY", "AIzaSyTestMockKeyForPytestRunning12345")
    
    # Initialize database files
    index.init_db()
    yield tmp_path

@pytest.fixture
def client():
    """FastAPI TestClient fixture."""
    from api.index import app
    return TestClient(app)

@pytest.fixture
def sample_image_bytes():
    """Generates a small RGB test image in memory as JPEG bytes."""
    img = Image.new("RGB", (100, 100), color=(73, 109, 137))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf.getvalue()

@pytest.fixture
def registered_user(client):
    """Registers a sample user and returns their credentials, response and token."""
    user_data = {
        "name": "Jane Doe",
        "email": "jane.doe@example.com",
        "password": "SecurePassword123!"
    }
    resp = client.post("/api/auth/register", json=user_data)
    data = resp.json()
    return {
        **user_data,
        "id": data["user"]["id"],
        "token": data["token"]
    }
