"""
test_auth.py - Integration tests for WeatherGPT Authentication, User Profiles & SQLite Database Records
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.services import auth_service

@pytest.fixture(scope="module")
def client():
    auth_service.init_db()
    with TestClient(app) as c:
        yield c

def test_user_registration_and_login(client):
    test_email = "test_user_farmer@weathergpt.io"
    reg_payload = {
        "name": "Kisan Ramesh",
        "email": test_email,
        "password": "Password123!",
        "role": "Farmer",
        "phone": "+91 9123456780",
        "state": "Uttar Pradesh",
        "district": "Lucknow",
        "village": "Maharajganj",
        "primary_crop": "Rice",
        "preferred_language": "hi"
    }

    # Register
    res = client.post("/api/auth/register", json=reg_payload)
    assert res.status_code in [201, 400] # 400 if already created in earlier test run
    
    # Login
    login_res = client.post("/api/auth/login", json={
        "email": test_email,
        "password": "Password123!"
    })
    assert login_res.status_code == 200
    token = login_res.json()["token"]
    assert token is not None

    # Get Profile /me
    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    profile = me_res.json()
    assert profile["email"] == test_email
    assert profile["created_at"] is not None
    assert profile["last_login_at"] is not None

    # Update Profile
    update_res = client.put(
        "/api/auth/profile",
        json={"primary_crop": "Wheat", "phone": "+91 9998887776"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert update_res.status_code == 200
    assert update_res.json()["primary_crop"] == "Wheat"

    # Admin inspection
    admin_res = client.get("/api/auth/admin/records")
    assert admin_res.status_code == 200
    data = admin_res.json()
    assert data["total_users"] >= 1
    assert len(data["recent_logs"]) >= 1
