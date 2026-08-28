import time
import uuid
import jwt
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

client = TestClient(app)

TEST_SECRET = "test-secret-key-for-supabase-jwt-123456"


def create_token(sub: str, email: str = "fisher@sagar.org") -> str:
    settings.SUPABASE_JWT_SECRET = TEST_SECRET
    payload = {
        "sub": sub,
        "email": email,
        "aud": "authenticated",
        "role": "authenticated",
        "exp": int(time.time()) + 3600,
        "iat": int(time.time()),
        "user_metadata": {"email": email},
    }
    return jwt.encode(payload, TEST_SECRET, algorithm="HS256")


def test_user_lifecycle():
    unique_sub = f"sub-{uuid.uuid4().hex[:8]}"
    email = f"{unique_sub}@sagar.org"
    token = create_token(sub=unique_sub, email=email)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Accessing /me before creating user should fail with 401
    resp = client.get("/api/v1/user/me", headers=headers)
    assert resp.status_code == 401

    # 2. Create user with profile data
    create_payload = {
        "name": "Karthik Fisher",
        "preferred_language": "ta",
        "home_port": "Chennai Harbour",
        "vessel_id": "vessel-999",
    }
    resp = client.post("/api/v1/user/create", json=create_payload, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["message"] == "User created successfully"
    assert data["supabase_uid"] == unique_sub
    assert data["email"] == email
    assert data["name"] == "Karthik Fisher"
    assert data["preferred_language"] == "ta"
    assert data["home_port"] == "Chennai Harbour"
    assert data["vessel_id"] == "vessel-999"

    # 3. Duplicate create should return 400
    dup_resp = client.post("/api/v1/user/create", json=create_payload, headers=headers)
    assert dup_resp.status_code == 400
    assert dup_resp.json()["detail"] == "User already exists"

    # 4. Get current user profile
    me_resp = client.get("/api/v1/user/me", headers=headers)
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["supabase_uid"] == unique_sub
    assert me_data["name"] == "Karthik Fisher"
    assert me_data["preferred_language"] == "ta"
    assert "user_id" in me_data
    assert "created_at" in me_data

    # 5. Update user profile
    update_payload = {
        "name": "Karthik K",
        "home_port": "Tuticorin Port",
        "preferred_language": "en",
    }
    update_resp = client.put("/api/v1/user/me", json=update_payload, headers=headers)
    assert update_resp.status_code == 200
    updated_data = update_resp.json()
    assert updated_data["name"] == "Karthik K"
    assert updated_data["home_port"] == "Tuticorin Port"
    assert updated_data["preferred_language"] == "en"
    assert updated_data["vessel_id"] == "vessel-999"


def test_starter_compatibility_endpoints():
    unique_sub = f"sub-{uuid.uuid4().hex[:8]}"
    email = f"starter-{unique_sub}@sagar.org"
    token = create_token(sub=unique_sub, email=email)
    headers = {"Authorization": f"Bearer {token}"}

    # Test /user/create (without /api/v1 prefix)
    resp = client.post("/user/create", headers=headers)
    assert resp.status_code == 201
    assert resp.json()["supabase_uid"] == unique_sub

    # Test /user/me
    resp = client.get("/user/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == email
