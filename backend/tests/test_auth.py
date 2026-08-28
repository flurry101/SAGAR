import time
import jwt
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

client = TestClient(app)
TEST_SECRET = "test-secret-key-for-supabase-jwt-123456"
def create_token(
    sub="test-user-sub-001",
    email="fisher1@sagar.org",
    secret=TEST_SECRET,
    audience="authenticated",
    expires_in=3600,
    include_sub=True,
):
    settings.SUPABASE_JWT_SECRET = TEST_SECRET
    payload = {
        "email": email,
        "aud": audience,
        "role": "authenticated",
        "exp": int(time.time()) + expires_in,
        "iat": int(time.time()),
        "user_metadata": {"email": email, "name": "Ramesh"},
    }
    if include_sub:
        payload["sub"] = sub
    return jwt.encode(payload, secret, algorithm="HS256")

def test_token_info_valid_token():
    token = create_token()
    response = client.get(
        "/api/v1/user/token-info",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "valid"
    assert data["claims"]["sub"] == "test-user-sub-001"
    assert data["claims"]["email"] == "fisher1@sagar.org"

def test_token_info_missing_header():
    response = client.get("/api/v1/user/token-info")
    assert response.status_code == 401
    assert "Authentication credentials were not provided" in response.json()["detail"]

def test_token_info_invalid_signature():
    token = create_token(secret="wrong-secret-key-abcdef-123456789012")
    response = client.get(
        "/api/v1/user/token-info",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401
    assert "Invalid authentication token" in response.json()["detail"]

def test_token_info_expired_token():
    token = create_token(expires_in=-3600)
    response = client.get(
        "/api/v1/user/token-info",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401
    assert "Token has expired" in response.json()["detail"]

def test_token_info_invalid_audience():
    token = create_token(audience="wrong_audience")
    response = client.get(
        "/api/v1/user/token-info",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401
    assert "Invalid token audience" in response.json()["detail"]

def test_token_info_missing_sub():
    token = create_token(include_sub=False)
    response = client.get(
        "/api/v1/user/token-info",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401
    assert "missing subject claim" in response.json()["detail"]
