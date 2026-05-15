from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def _user(user_id: int = 1):
    return SimpleNamespace(id=user_id, email="krishna.dhakal03@gmail.com")


def _generation(**overrides):
    data = {
        "id": 10,
        "user_id": 1,
        "input_type": "video",
        "video_run_id": "run_test123",
        "video_file": "sample-run_test123/sample.mp4",
        "video_thumbnail": "sample-run_test123/sample.jpg",
        "status": "success",
        "error_message": None,
        "created_at": None,
        "seo_tags": None,
        "seo_hashtags": None,
        "seo_title": "Sample",
        "seo_description": None,
        "thumbnail_text": None,
        "runway_credits_used": 0,
        "elevenlabs_credits_used": 0,
        "total_cost_usd": 0,
        "video_duration_seconds": 10,
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def _app_with_db(db, current_user=None) -> FastAPI:
    from auth import get_current_user
    from database import get_db
    from routes.generate import router as generate_router

    app = FastAPI()
    app.include_router(generate_router, prefix="/api/generate")

    async def override_user():
        return current_user or _user()

    async def override_db():
        yield db

    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[get_db] = override_db
    return app


def _db_returning(row):
    db = AsyncMock()
    db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=row)))
    db.delete = AsyncMock()
    db.commit = AsyncMock()
    return db


def test_delete_generation_assets_removes_run_folder_and_nested_artifacts(tmp_path, monkeypatch):
    import utils.video_artifacts as artifacts

    monkeypatch.setattr(artifacts, "GENERATED_ROOT", tmp_path)
    run_dir = tmp_path / "sample-run_test123"
    for subdir in ("raw", "temp", "audio"):
        (run_dir / subdir).mkdir(parents=True)
        (run_dir / subdir / f"run_test123_{subdir}.dat").write_bytes(b"x")
    (run_dir / "sample.mp4").write_bytes(b"mp4")
    (run_dir / "sample.jpg").write_bytes(b"jpg")

    report = artifacts.delete_generation_assets(
        video_file="sample-run_test123/sample.mp4",
        video_thumbnail="sample-run_test123/sample.jpg",
        video_run_id="run_test123",
    )

    assert report.deleted_count >= 1
    assert not run_dir.exists()


def test_delete_generation_assets_ignores_missing_files(tmp_path, monkeypatch):
    import utils.video_artifacts as artifacts

    monkeypatch.setattr(artifacts, "GENERATED_ROOT", tmp_path)

    report = artifacts.delete_generation_assets(
        video_file="missing-run/missing.mp4",
        video_thumbnail="missing-run/missing.jpg",
        video_run_id="missing_run",
    )

    assert report.deleted_count == 0


def test_unauthorized_user_cannot_delete_another_users_video():
    db = _db_returning(None)
    client = TestClient(_app_with_db(db, current_user=_user(user_id=2)))

    response = client.delete("/api/generate/video/10")

    assert response.status_code == 404
    db.delete.assert_not_awaited()


def test_download_requires_matching_owner_and_success_status(tmp_path, monkeypatch):
    import utils.video_artifacts as artifacts

    monkeypatch.setattr(artifacts, "GENERATED_ROOT", tmp_path)
    run_dir = tmp_path / "sample-run_test123"
    run_dir.mkdir()
    (run_dir / "sample.mp4").write_bytes(b"mp4")
    db = _db_returning(_generation())
    client = TestClient(_app_with_db(db))

    response = client.get("/api/generate/video/download/sample-run_test123/sample.mp4")

    assert response.status_code == 200
    assert response.content == b"mp4"


def test_deleted_video_is_not_downloadable():
    db = _db_returning(None)
    client = TestClient(_app_with_db(db))

    response = client.get("/api/generate/video/download/sample-run_test123/sample.mp4")

    assert response.status_code == 404


def test_deleted_history_row_does_not_expose_download_url():
    from routes.generate import _serialize_video_history_row

    payload = _serialize_video_history_row(_generation(status="deleted"), include_heavy=False)

    assert payload["download_url"] is None
    assert payload["video_url"] is None


def test_success_history_row_requires_existing_local_mp4(tmp_path, monkeypatch):
    import routes.generate as generate_route

    monkeypatch.setattr(generate_route, "generated_root", lambda: tmp_path)

    payload = generate_route._serialize_video_history_row(
        _generation(video_file="missing-run/missing.mp4", status="success"),
        include_heavy=False,
    )

    assert payload["download_url"] is None
    assert payload["video_url"] is None
    assert "final MP4 artifact is missing" in payload["warning"]


def test_success_history_row_exposes_existing_local_mp4(tmp_path, monkeypatch):
    import routes.generate as generate_route

    monkeypatch.setattr(generate_route, "generated_root", lambda: tmp_path)
    run_dir = tmp_path / "sample-run_test123"
    run_dir.mkdir()
    (run_dir / "sample.mp4").write_bytes(b"mp4")

    payload = generate_route._serialize_video_history_row(_generation(), include_heavy=False)

    assert payload["download_url"] == "/api/generate/video/download/sample-run_test123/sample.mp4"
    assert payload["video_url"] == "/api/generate/video/download/sample-run_test123/sample.mp4"


def test_live_free_footage_rejects_paid_providers_by_default(monkeypatch):
    monkeypatch.setenv("ENABLE_SERVER_VIDEO_RENDERING", "true")
    monkeypatch.setenv("VIDEO_RENDER_ALLOWED_USER_EMAIL", "krishna.dhakal03@gmail.com")
    monkeypatch.setenv("MAX_VIDEO_DURATION_SECONDS", "35")
    monkeypatch.delenv("FREE_VIDEO_ALLOW_PAID_PROVIDERS", raising=False)
    client = TestClient(_app_with_db(_db_returning(None)))

    response = client.post(
        "/api/generate/video/free",
        json={
            "script": "Hook line. " + "Body value " * 20 + "CTA follow.",
            "duration_seconds": 10,
            "dry_run": False,
            "scene_mode": "auto",
            "tts_provider": "free",
        },
    )

    assert response.status_code == 400
    assert "stock footage" in response.text


def test_cleanup_old_video_artifacts_only_deletes_generated_root(tmp_path, monkeypatch):
    import utils.video_artifacts as artifacts

    monkeypatch.setattr(artifacts, "GENERATED_ROOT", tmp_path / "generated_videos")
    root = artifacts.generated_root()
    old_run = root / "old-run_123"
    new_run = root / "new-run_456"
    outside = tmp_path / "outside"
    old_run.mkdir(parents=True)
    new_run.mkdir(parents=True)
    outside.mkdir()
    (old_run / "old.mp4").write_bytes(b"old")
    (new_run / "new.mp4").write_bytes(b"new")
    (outside / "keep.mp4").write_bytes(b"keep")

    old_time = time.time() - (100 * 3600)
    os.utime(old_run, (old_time, old_time))
    os.utime(old_run / "old.mp4", (old_time, old_time))

    report = artifacts.cleanup_old_video_artifacts(completed_hours=72, failed_temp_hours=24)

    assert report.deleted_count == 1
    assert not old_run.exists()
    assert new_run.exists()
    assert outside.exists()
