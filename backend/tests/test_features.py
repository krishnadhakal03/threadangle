import pytest
from httpx import AsyncClient
from main import app
from models import User, Contact
from sqlalchemy import select

@pytest.mark.asyncio
async def test_onboarding_complete(auth_client):
    response = await auth_client.patch("/api/auth/onboarding-complete")
    assert response.status_code == 200
    assert response.json()["message"] == "Onboarding completed"

@pytest.mark.asyncio
async def test_forgot_password(client, test_db):
    # Test with existing email
    response = await client.post("/api/auth/forgot-password", json={"email": "test@example.com"})
    assert response.status_code == 200
    
    async with test_db() as session:
        result = await session.execute(select(User).where(User.email == "test@example.com"))
        user = result.scalar_one()
        assert user.reset_token is not None
        assert user.reset_token_expiry is not None

@pytest.mark.asyncio
async def test_verify_reset_token(client, test_db):
    async with test_db() as session:
        result = await session.execute(select(User).where(User.email == "test@example.com"))
        user = result.scalar_one()
        token = user.reset_token
        
    response = await client.get(f"/api/auth/verify-reset-token?token={token}")
    assert response.status_code == 200
    assert response.json()["valid"] == True

@pytest.mark.asyncio
async def test_reset_password(client, test_db):
    async with test_db() as session:
        result = await session.execute(select(User).where(User.email == "test@example.com"))
        user = result.scalar_one()
        token = user.reset_token
        
    response = await client.post("/api/auth/reset-password", json={
        "token": token,
        "new_password": "newpassword123"
    })
    assert response.status_code == 200
    assert response.json()["message"] == "Password reset successful"

@pytest.mark.asyncio
async def test_contact_submission(client, test_db):
    payload = {
        "name": "Test User",
        "email": "test@example.com",
        "subject": "Testing",
        "message": "This is a test message that is long enough."
    }
    response = await client.post("/api/contact", json=payload)
    assert response.status_code == 200
    
    async with test_db() as session:
        result = await session.execute(select(Contact).where(Contact.email == "test@example.com"))
        contact = result.scalar_one()
        assert contact.subject == "Testing"

@pytest.mark.asyncio
async def test_admin_stats_protected(client):
    response = await client.get("/api/admin/stats", headers={"X-Admin-Password": "wrong"})
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_admin_stats_success(client):
    import os
    admin_pw = os.getenv("ADMIN_PASSWORD", "test_admin_pass")
    os.environ["ADMIN_PASSWORD"] = admin_pw # Ensure it's set
    
    response = await client.get("/api/admin/stats", headers={"X-Admin-Password": admin_pw})
    assert response.status_code == 200
    assert "overview" in response.json()
    assert "recent_users" in response.json()
