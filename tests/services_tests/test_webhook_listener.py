# tests/service_tests/test_webhook_listener.py
import multipart
import os
import json
import hmac
import hashlib
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from services.webhook_listener.main import app

client = TestClient(app)


def generate_signature(secret: str, body: bytes) -> str:
    """
    Generate a GitHub-style HMAC SHA256 signature for the webhook payload.
    """
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


@pytest.fixture(autouse=True)
def set_env_vars(monkeypatch):
    """
    Automatically set required environment variables for each test.
    """
    monkeypatch.setenv("GITHUB_SECRET", "testsecret")
    monkeypatch.setenv("REDIS_URL_DOCKER", "redis://fake-url")


@pytest.mark.asyncio
async def test_valid_signature_and_pr_event(monkeypatch):
    """
    Test webhook with a valid signature and a pull request event.
    Should enqueue the event in Redis and return success.
    """
    body = {
        "repository": {"full_name": "user/repo"},
        "pull_request": {"number": 42},
        "action": "opened",
    }
    body_bytes = json.dumps(body).encode()

    signature = generate_signature("testsecret", body_bytes)

    fake_redis = AsyncMock()
    fake_redis.lpush.return_value = 1
    fake_redis.ping.return_value = True

    # Patch Redis connection to use the fake_redis mock
    with patch("services.webhook_listener.main.from_url", AsyncMock(return_value=fake_redis)):
        response = client.post(
            "/webhook",
            headers={"x-hub-signature-256": signature},
            json=body,
        )

    assert response.status_code == 200
    data = response.json()
    assert "enqueued" in data
    assert data["enqueued"]["pr_number"] == 42
    fake_redis.lpush.assert_awaited_once()


def test_invalid_signature():
    """
    Test webhook with an invalid signature.
    Should return 401 Unauthorized.
    """
    body = {"repository": {"full_name": "user/repo"}}
    body_bytes = json.dumps(body).encode()

    # Wrong secret used for signature
    signature = generate_signature("wrongsecret", body_bytes)

    response = client.post(
        "/webhook",
        headers={"x-hub-signature-256": signature},
        json=body,
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid signature"


def test_non_pr_event(monkeypatch):
    """
    Test webhook with a valid signature but not a pull request event.
    Should return ignored=True.
    """
    body = {
        "repository": {"full_name": "user/repo"},
        "action": "opened",
    }
    body_bytes = json.dumps(body).encode()
    signature = generate_signature("testsecret", body_bytes)

    response = client.post(
        "/webhook",
        headers={"x-hub-signature-256": signature},
        json=body,
    )

    assert response.status_code == 200
    assert response.json() == {"ignored": True}
