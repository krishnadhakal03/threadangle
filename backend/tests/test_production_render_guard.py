from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def _user(email: str = "krishna.dhakal03@gmail.com"):
    return SimpleNamespace(
        id=1,
        email=email,
        plan="pro",
        usage_count=0,
        custom_limit=None,
        voice_learned=False,
        voice_profile=None,
    )


def _app_with_generate_router(current_user=None) -> FastAPI:
    from auth import get_current_user
    from database import get_db
    from routes.generate import router as generate_router

    app = FastAPI()
    app.include_router(generate_router, prefix="/api/generate")

    if current_user is not None:
        async def override_user():
            return current_user

        app.dependency_overrides[get_current_user] = override_user

    async def override_db():
        db = AsyncMock()
        db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock(side_effect=lambda obj: setattr(obj, "id", getattr(obj, "id", 1)))
        yield db

    app.dependency_overrides[get_db] = override_db
    return app


@pytest.fixture(autouse=True)
def render_env(monkeypatch):
    monkeypatch.setenv("ENABLE_SERVER_VIDEO_RENDERING", "true")
    monkeypatch.setenv("VIDEO_RENDER_ALLOWED_USER_EMAIL", "krishna.dhakal03@gmail.com")
    monkeypatch.setenv("MAX_CONCURRENT_VIDEO_RENDERS", "1")
    monkeypatch.setenv("MAX_VIDEO_DURATION_SECONDS", "35")
    monkeypatch.setenv("MAX_VIDEO_RENDER_SECONDS", "5")
    from utils.render_guard import reset_render_guard_for_tests

    reset_render_guard_for_tests()
    yield
    reset_render_guard_for_tests()


def test_non_logged_in_render_request_is_rejected():
    client = TestClient(_app_with_generate_router())

    response = client.post("/api/generate/video/free", json={"script": "word " * 40, "duration_seconds": 10})

    assert response.status_code == 401


def test_logged_in_non_owner_render_request_is_rejected():
    client = TestClient(_app_with_generate_router(_user("someone@example.com")))

    response = client.post("/api/generate/video/free", json={"script": "word " * 40, "duration_seconds": 10})

    assert response.status_code == 403


def test_owner_email_can_render_when_enabled(tmp_path):
    from utils.video_pipeline import ScenePlan

    out = tmp_path / "render.mp4"
    out.write_bytes(b"fake mp4")
    scenes = [
        ScenePlan(
            idx=0,
            start=0.0,
            end=5.0,
            part="hook",
            source_text="Hook",
            subtitle="Hook",
            visual_description="Stock clip",
            keywords=[],
            energy="high",
        )
    ]
    client = TestClient(_app_with_generate_router(_user()))

    with patch("routes.generate.fetch_scene_clips", new_callable=AsyncMock, return_value=scenes), \
         patch("routes.generate.assemble_video", return_value={"video_path": str(out), "thumbnail_path": None, "ffmpeg_error": None}), \
         patch("routes.generate.generate_youtube_metadata", new_callable=AsyncMock, return_value={"title": "Owner Render"}):
        response = client.post(
            "/api/generate/video/free",
            json={"script": "Hook line. " + "Body value " * 20 + "CTA follow.", "duration_seconds": 10, "dry_run": True},
        )

    assert response.status_code == 200
    assert response.json()["success"] is True


def test_render_duration_over_35_seconds_is_rejected():
    client = TestClient(_app_with_generate_router(_user()))

    response = client.post("/api/generate/video/free", json={"script": "word " * 80, "duration_seconds": 36})

    assert response.status_code == 400
    assert "duration" in response.text.lower()


@pytest.mark.asyncio
async def test_concurrent_render_is_rejected():
    from fastapi import HTTPException
    from utils.render_guard import acquire_render_slot, release_render_slot

    token = await acquire_render_slot()
    try:
        with pytest.raises(HTTPException) as exc:
            await acquire_render_slot()
    finally:
        await release_render_slot(token)

    assert exc.value.status_code == 429


def test_production_env_checker_does_not_leak_secret_prefixes(monkeypatch, capsys):
    fake_secret = "sk_live_super_secret_value"
    monkeypatch.setenv("ANTHROPIC_API_KEY", fake_secret)
    monkeypatch.setenv("STRIPE_SECRET_KEY", fake_secret)
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", fake_secret)
    monkeypatch.setenv("STRIPE_STARTER_PRICE_ID", "price_starter")
    monkeypatch.setenv("STRIPE_PRO_PRICE_ID", "price_pro")
    monkeypatch.setenv("ZOHO_EMAIL", "test@example.com")
    monkeypatch.setenv("ZOHO_PASSWORD", fake_secret)
    monkeypatch.setenv("GOOGLE_CLIENT_ID", fake_secret)
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", fake_secret)
    monkeypatch.setenv("JWT_SECRET", fake_secret)

    import main

    capsys.readouterr()
    importlib.reload(main)
    output = capsys.readouterr().out

    assert fake_secret not in output
    assert fake_secret[:8] not in output
    assert "is set" in output
