import pytest
import os
import json
import asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, MagicMock, AsyncMock

# Import app components
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set dummy env vars for tests
os.environ["ANTHROPIC_API_KEY"] = "test-key"
os.environ["JWT_SECRET"] = "test-secret"
os.environ["ENVIRONMENT"] = "testing"

from main import app
from database import Base, get_db

# Test Database Setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"
engine = create_async_engine(
    TEST_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    echo=False
)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def override_get_db():
    async with AsyncSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="function", autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()

@pytest.fixture(scope="function")
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

# --- AUTH TESTS ---

async def test_signup_success(client):
    response = await client.post("/api/auth/signup", json={"email": "test@example.com", "password": "password123"})
    assert response.status_code == 200
    assert "token" in response.json()

async def test_signup_duplicate(client):
    await client.post("/api/auth/signup", json={"email": "dup@example.com", "password": "password123"})
    response = await client.post("/api/auth/signup", json={"email": "dup@example.com", "password": "password123"})
    assert response.status_code == 409

async def test_signup_short_password(client):
    response = await client.post("/api/auth/signup", json={"email": "short@example.com", "password": "123"})
    assert response.status_code in [400, 422]

async def test_login_success(client):
    await client.post("/api/auth/signup", json={"email": "login@example.com", "password": "password123"})
    response = await client.post("/api/auth/login", json={"email": "login@example.com", "password": "password123"})
    assert response.status_code == 200
    assert "token" in response.json()

async def test_login_wrong_password(client):
    await client.post("/api/auth/signup", json={"email": "wrongpass@example.com", "password": "password123"})
    response = await client.post("/api/auth/login", json={"email": "wrongpass@example.com", "password": "wrong"})
    assert response.status_code == 401

async def test_login_non_existent_email(client):
    response = await client.post("/api/auth/login", json={"email": "no@exists.com", "password": "password123"})
    assert response.status_code == 401

async def test_get_me_valid_token(client):
    res = await client.post("/api/auth/signup", json={"email": "me@example.com", "password": "password123"})
    token = res.json()["token"]
    response = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "me@example.com"

async def test_get_me_no_token(client):
    response = await client.get("/api/auth/me")
    assert response.status_code == 401

async def test_get_me_invalid_token(client):
    response = await client.get("/api/auth/me", headers={"Authorization": "Bearer invalid"})
    assert response.status_code == 401

# --- GENERATE TESTS ---

@patch("utils.ai.AsyncAnthropic")
async def test_generate_text_success(mock_anthropic, client):
    mock_instance = mock_anthropic.return_value
    mock_instance.messages.create = AsyncMock(return_value=MagicMock(content=[MagicMock(text=json.dumps({
        "twitter": {"hook": "h", "thread": [], "hashtags": []},
        "linkedin": {"title": "t", "body": "b", "hashtags": []},
        "tiktok": {"hook_line": "h", "script": {}, "on_screen_text": [], "caption": "", "hashtags": [], "audio_suggestion": ""}
    }))]))

    res = await client.post("/api/auth/signup", json={"email": "gen@example.com", "password": "password123"})
    token = res.json()["token"]

    response = await client.post("/api/generate/", 
        json={"input_type": "text", "content": "test", "platforms": ["twitter"], "tone": "professional"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200

@patch("utils.ai.AsyncAnthropic")
@patch("utils.ai.extract_content_from_url")
async def test_generate_url_success(mock_extract, mock_anthropic, client):
    mock_extract.return_value = "Content"
    mock_instance = mock_anthropic.return_value
    mock_instance.messages.create = AsyncMock(return_value=MagicMock(content=[MagicMock(text=json.dumps({"twitter": {}}))]))

    res = await client.post("/api/auth/signup", json={"email": "url@example.com", "password": "password123"})
    token = res.json()["token"]

    response = await client.post("/api/generate/", 
        json={"input_type": "url", "content": "http://example.com", "platforms": ["twitter"], "tone": "p"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200

@patch("utils.ai.AsyncAnthropic")
async def test_generate_all_platforms(mock_anthropic, client):
    mock_instance = mock_anthropic.return_value
    mock_instance.messages.create = AsyncMock(return_value=MagicMock(content=[MagicMock(text=json.dumps({
        "twitter": {}, "linkedin": {}, "tiktok": {}
    }))]))

    res = await client.post("/api/auth/signup", json={"email": "all@example.com", "password": "password123"})
    token = res.json()["token"]

    response = await client.post("/api/generate/", 
        json={"input_type": "text", "content": "test", "platforms": ["twitter", "linkedin", "tiktok"], "tone": "viral"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200

async def test_generate_no_auth(client):
    response = await client.post("/api/generate/", json={})
    assert response.status_code == 401

@patch("utils.ai.extract_content_from_url")
async def test_generate_invalid_url(mock_extract, client):
    mock_extract.return_value = None
    res = await client.post("/api/auth/signup", json={"email": "invurl@example.com", "password": "password123"})
    token = res.json()["token"]

    response = await client.post("/api/generate/", 
        json={"input_type": "url", "content": "http://invalid-url.com", "platforms": ["twitter"], "tone": "p"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400

@patch("utils.ai.AsyncAnthropic")
async def test_generate_limit_reached(mock_anthropic, client):
    mock_instance = mock_anthropic.return_value
    mock_instance.messages.create = AsyncMock(return_value=MagicMock(content=[MagicMock(text=json.dumps({"twitter": {}}))]))

    res = await client.post("/api/auth/signup", json={"email": "limit@example.com", "password": "password123"})
    token = res.json()["token"]

    for _ in range(3):
        await client.post("/api/generate/", 
            json={"input_type": "text", "content": "t", "platforms": ["twitter"], "tone": "p"},
            headers={"Authorization": f"Bearer {token}"}
        )
    
    response = await client.post("/api/generate/", 
        json={"input_type": "text", "content": "t", "platforms": ["twitter"], "tone": "p"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403

# --- FREE TOOL TESTS ---

@patch("routes.free.AsyncAnthropic")
async def test_free_hooks_success(mock_anthropic, client):
    mock_instance = mock_anthropic.return_value
    mock_instance.messages.create = AsyncMock(return_value=MagicMock(content=[MagicMock(text=json.dumps({
        "hooks": [{"type": "t", "text": "t", "why_it_works": "w"}] * 5
    }))]))

    response = await client.post("/api/free/generate-hooks", json={"topic": "test", "category": "Marketing"})
    assert response.status_code == 200
    assert len(response.json()["hooks"]) == 5

async def test_free_hooks_empty_topic(client):
    response = await client.post("/api/free/generate-hooks", json={"topic": "", "category": "Marketing"})
    assert response.status_code in [400, 422]

# --- PAYMENTS TESTS ---

@patch("stripe.checkout.Session.create")
async def test_create_checkout_success(mock_stripe, client):
    mock_stripe.return_value = MagicMock(url="http://stripe.com")
    
    res = await client.post("/api/auth/signup", json={"email": "pay@example.com", "password": "password123"})
    token = res.json()["token"]

    response = await client.post("/api/payments/create-checkout?plan=starter", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200

async def test_create_checkout_no_auth(client):
    response = await client.post("/api/payments/create-checkout?plan=starter")
    assert response.status_code == 401

async def test_create_checkout_invalid_plan(client):
    res = await client.post("/api/auth/signup", json={"email": "payinv@example.com", "password": "password123"})
    token = res.json()["token"]

    response = await client.post("/api/payments/create-checkout?plan=invalid", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 400

# --- SESSION 11 FEATURE TESTS ---

async def test_onboarding_complete_success(client):
    res = await client.post("/api/auth/signup", json={"email": "onboard@example.com", "password": "password123"})
    token = res.json()["token"]
    response = await client.patch("/api/auth/onboarding-complete", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["message"] == "Onboarding completed"

async def test_forgot_password_and_verify(client):
    await client.post("/api/auth/signup", json={"email": "reset@example.com", "password": "password123"})
    # Trigger forgot password
    response = await client.post("/api/auth/forgot-password", json={"email": "reset@example.com"})
    assert response.status_code == 200
    
    # In tests, we would need to check the DB for the token since we can't read the email
    async with AsyncSessionLocal() as session:
        from models import User
        from sqlalchemy import select
        result = await session.execute(select(User).where(User.email == "reset@example.com"))
        user = result.scalar_one()
        token = user.reset_token
        assert token is not None

    # Verify token
    v_res = await client.get(f"/api/auth/verify-reset-token?token={token}")
    assert v_res.status_code == 200
    assert v_res.json()["valid"] is True

async def test_reset_password_success(client):
    await client.post("/api/auth/signup", json={"email": "reset2@example.com", "password": "password123"})
    async with AsyncSessionLocal() as session:
        from models import User
        from sqlalchemy import select
        result = await session.execute(select(User).where(User.email == "reset2@example.com"))
        user = result.scalar_one()
        token = "test-token-direct"
        user.reset_token = token
        from datetime import datetime, timedelta
        user.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
        await session.commit()

    response = await client.post("/api/auth/reset-password", json={
        "token": token,
        "new_password": "newpassword456"
    })
    assert response.status_code == 200
    
    # Try logging in with new password
    login_res = await client.post("/api/auth/login", json={"email": "reset2@example.com", "password": "newpassword456"})
    assert login_res.status_code == 200

async def test_contact_us_success(client):
    payload = {
        "name": "Alex",
        "email": "alex@example.com",
        "subject": "Question",
        "message": "This is a long enough message for the contact form to accept."
    }
    response = await client.post("/api/contact", json=payload)
    assert response.status_code == 200
    assert "Thanks" in response.json()["message"]

async def test_admin_stats_access(client):
    os.environ["ADMIN_PASSWORD"] = "secret123"
    # Success
    response = await client.get("/api/admin/stats", headers={"X-Admin-Password": "secret123"})
    assert response.status_code == 200
    assert "overview" in response.json()
    
    # Failure
    response = await client.get("/api/admin/stats", headers={"X-Admin-Password": "wrong"})
    assert response.status_code == 401
