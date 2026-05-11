from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import BackgroundTasks

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def _owner():
    return SimpleNamespace(id=1, email="krishna.dhakal03@gmail.com")


def _db_with_refresh_id(generation_id: int = 123):
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()

    async def refresh(obj):
        obj.id = generation_id

    db.refresh = AsyncMock(side_effect=refresh)
    return db


def _stock_request(dry_run: bool):
    from routes.generate import GenerateFromPreviewRequest

    return GenerateFromPreviewRequest(
        preview_id="preview_test",
        approved_scenes=[
            {
                "method": "stock",
                "duration": 5,
                "subtitle": "This is the test line.",
                "description": "person working at laptop",
            }
        ],
        dry_run=dry_run,
        script="This is the test line for a short free footage render with enough detail to pass the live render quality guard.",
        tts_provider="free",
    )


@pytest.fixture(autouse=True)
def render_env(monkeypatch):
    monkeypatch.setenv("ENABLE_SERVER_VIDEO_RENDERING", "true")
    monkeypatch.setenv("VIDEO_RENDER_ALLOWED_USER_EMAIL", "krishna.dhakal03@gmail.com")
    monkeypatch.setenv("ENABLE_BETA_WAITLIST_MODE", "true")
    monkeypatch.setenv("BETA_FULL_ACCESS_EMAILS", "krishna.dhakal03@gmail.com")


@pytest.mark.asyncio
async def test_real_render_requested_is_not_marked_effective_dry_run(monkeypatch):
    import routes.generate as generate

    monkeypatch.setenv("VIDEO_GENERATION_DRY_RUN", "0")
    monkeypatch.setattr(generate, "acquire_render_slot", AsyncMock(return_value=object()))

    response = await generate.generate_video_from_preview(
        request=_stock_request(dry_run=False),
        background_tasks=BackgroundTasks(),
        current_user=_owner(),
        db=_db_with_refresh_id(),
    )

    assert response["dry_run"] is False
    assert response["effective_dry_run"] is False
    assert response["diagnostic_reason"] == "Real free-footage render requested."


@pytest.mark.asyncio
async def test_server_dry_run_env_returns_visible_reason(monkeypatch):
    import routes.generate as generate

    monkeypatch.setenv("VIDEO_GENERATION_DRY_RUN", "1")
    monkeypatch.setattr(generate, "acquire_render_slot", AsyncMock(return_value=object()))

    response = await generate.generate_video_from_preview(
        request=_stock_request(dry_run=False),
        background_tasks=BackgroundTasks(),
        current_user=_owner(),
        db=_db_with_refresh_id(),
    )

    assert response["dry_run"] is False
    assert response["effective_dry_run"] is True
    assert "VIDEO_GENERATION_DRY_RUN" in response["diagnostic_reason"]
    assert "no MP4 rendered" in response["diagnostic_reason"]


def test_metadata_only_history_has_reason_and_no_download():
    from routes.generate import _serialize_video_history_row

    generation = SimpleNamespace(
        id=1,
        video_run_id=None,
        video_duration_seconds=5,
        video_file=None,
        video_thumbnail=None,
        created_at=None,
        status="success",
        error_message="Dry run only - no MP4 rendered. VIDEO_GENERATION_DRY_RUN is enabled on the server.",
        seo_tags=None,
        seo_hashtags=None,
        seo_title=None,
        seo_description=None,
        thumbnail_text=None,
        runway_credits_used=0,
        elevenlabs_credits_used=0,
        total_cost_usd=0,
    )

    payload = _serialize_video_history_row(generation, include_heavy=False)

    assert payload["metadata_only"] is True
    assert payload["download_url"] is None
    assert payload["video_url"] is None
    assert "no MP4 rendered" in payload["result_reason"]


def test_owner_render_guard_still_enforced_for_non_owner(monkeypatch):
    from fastapi import HTTPException
    from utils.render_guard import require_video_render_access

    monkeypatch.setenv("VIDEO_GENERATION_DRY_RUN", "0")

    with pytest.raises(HTTPException) as exc:
        import anyio

        anyio.run(require_video_render_access, SimpleNamespace(id=2, email="not-owner@example.com"))

    assert exc.value.status_code == 403
