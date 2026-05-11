from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


OWNER_EMAIL = "krishna.dhakal03@gmail.com"


def _user(email: str, user_id: int = 1):
    return SimpleNamespace(
        id=user_id,
        email=email,
        name="Test User",
        plan="free",
        usage_count=0,
        usage_reset_date=None,
        custom_limit=None,
        onboarding_completed=1,
        google_id=None,
        password_hash="hash",
        voice_learned=False,
        voice_profile=None,
        successful_generations_count=0,
        voice_samples_submitted=False,
        niche_tags=None,
    )


def _app_with_generate_user(current_user):
    from auth import get_current_user
    from database import get_db
    from routes.generate import router as generate_router

    app = FastAPI()
    app.include_router(generate_router, prefix="/api/generate")

    async def override_user():
        return current_user

    async def override_db():
        db = AsyncMock()
        db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))
        yield db

    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[get_db] = override_db
    return app


@pytest.fixture(autouse=True)
def beta_env(monkeypatch):
    monkeypatch.setenv("ENABLE_BETA_WAITLIST_MODE", "true")
    monkeypatch.setenv("BETA_FULL_ACCESS_EMAILS", OWNER_EMAIL)
    monkeypatch.setenv("BETA_SIGNUP_NOTIFY_EMAILS", f"{OWNER_EMAIL},info@kriangle.com")
    monkeypatch.setenv("ENABLE_SERVER_VIDEO_RENDERING", "true")
    monkeypatch.setenv("VIDEO_RENDER_ALLOWED_USER_EMAIL", OWNER_EMAIL)


def test_owner_email_gets_full_access():
    from auth import user_has_beta_full_access
    from routes.auth import _auth_user_payload

    owner = _user(OWNER_EMAIL)

    assert user_has_beta_full_access(owner) is True
    assert _auth_user_payload(owner)["beta_full_access"] is True


def test_non_owner_user_is_beta_gated():
    from auth import BETA_WAITLIST_MESSAGE, user_has_beta_full_access
    from routes.auth import _auth_user_payload

    user = _user("someone@example.com")
    payload = _auth_user_payload(user)

    assert user_has_beta_full_access(user) is False
    assert payload["beta_full_access"] is False
    assert payload["beta_waitlist_message"] == BETA_WAITLIST_MESSAGE


def test_non_owner_generation_request_returns_403():
    client = TestClient(_app_with_generate_user(_user("someone@example.com")))

    response = client.post(
        "/api/generate/",
        json={
            "input_type": "text",
            "content": "This is a long enough beta-gated content request that should never run.",
            "platforms": ["twitter"],
            "tone": "professional",
        },
    )

    assert response.status_code == 403
    assert "private beta testing" in response.text


def test_non_owner_render_request_returns_403():
    client = TestClient(_app_with_generate_user(_user("someone@example.com")))

    response = client.post(
        "/api/generate/video/free",
        json={"script": "word " * 40, "duration_seconds": 10, "dry_run": True},
    )

    assert response.status_code == 403
    assert "private beta testing" in response.text


@pytest.mark.asyncio
async def test_signup_notification_sends_to_configured_recipients(monkeypatch):
    import email_service

    sent = AsyncMock(return_value=True)
    monkeypatch.setattr(email_service, "send_email_async", sent)

    ok = await email_service.send_beta_signup_notifications(
        user_email="new@example.com",
        signup_method="email/password",
        name="New User",
    )

    assert ok is True
    assert sent.await_count == 2
    recipients = [call.args[0] for call in sent.await_args_list]
    assert recipients == [OWNER_EMAIL, "info@kriangle.com"]
    html = sent.await_args_list[0].args[2]
    assert "new@example.com" in html
    assert "email/password" in html
    assert "kriangle.com" in html


@pytest.mark.asyncio
async def test_signup_notification_failure_is_swallowed(monkeypatch, capsys):
    import routes.auth as auth_routes

    async def fail_notify(**_kwargs):
        raise RuntimeError("smtp down")

    monkeypatch.setattr(auth_routes, "send_beta_signup_notifications", fail_notify)

    await auth_routes._send_signup_notifications_safely(_user("new@example.com"), "email/password")

    output = capsys.readouterr().out
    assert "RuntimeError" in output
    assert "smtp down" not in output
