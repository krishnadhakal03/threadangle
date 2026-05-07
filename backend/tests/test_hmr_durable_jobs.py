from __future__ import annotations

import sys
from pathlib import Path

import pytest
import pytest_asyncio
from fastapi import BackgroundTasks
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def _generated_video_path(*parts: str) -> Path:
    path = BACKEND_DIR / "generated_videos" / "test_hmr_contract" / Path(*parts)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"fake mp4 bytes")
    return path


@pytest_asyncio.fixture()
async def hmr_session(tmp_path):
    from database import Base
    import models  # noqa: F401 - register SQLAlchemy models on Base metadata

    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'hmr_jobs.db'}", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with Session() as session:
        yield session
    await engine.dispose()


@pytest.mark.asyncio
async def test_hmr_durable_job_create_update_and_progress(hmr_session):
    from models import Generation, User
    from utils.hmr_durable_jobs import create_hmr_render_job_record, hmr_job_to_progress, update_hmr_render_job_record

    user = User(email="hmr@example.com", password_hash="x")
    hmr_session.add(user)
    await hmr_session.flush()
    generation = Generation(user_id=user.id, input_type="video", input_content="script", status="queued")
    hmr_session.add(generation)
    await hmr_session.flush()

    job = await create_hmr_render_job_record(
        hmr_session,
        generation_id=generation.id,
        user_id=user.id,
        run_id="durable-run",
        request_payload={"script_text": "hello"},
        artifact_paths={"review_package": "review_package"},
    )
    await hmr_session.commit()

    progress = hmr_job_to_progress(job)
    assert progress["hmr_render_job"]["execution_mode"] == "background_task"
    assert progress["hmr_render_job"]["worker_active"] is True
    assert progress["hmr_render_job"]["durable_progress"] is True
    assert progress["hmr_render_job"]["progress_store"] == "hmr_render_jobs"

    updated = await update_hmr_render_job_record(
        hmr_session,
        job.id,
        status="processing",
        percent=44,
        step="rendering",
        message="Working",
        render_invoked=True,
    )
    assert updated.status == "processing"
    assert updated.percent == 44
    assert updated.started_at is not None
    assert updated.render_invoked is True

    video_path = _generated_video_path("durable-run.mp4")

    done = await update_hmr_render_job_record(
        hmr_session,
        job.id,
        status="success",
        percent=100,
        step="done",
        message="Done",
        result={"video_path": str(video_path.resolve())},
    )
    assert done.status == "success"
    assert done.worker_active is False
    assert done.result_json == {"video_path": str(video_path.resolve())}
    await hmr_session.refresh(generation)
    assert generation.video_file == "test_hmr_contract/durable-run.mp4"
    done_progress = hmr_job_to_progress(done)
    assert done_progress["hmr_render_job"]["status"] == "success"
    assert done_progress["hmr_render_job"]["worker_active"] is False


@pytest.mark.asyncio
async def test_hmr_durable_job_success_requires_existing_generated_mp4(hmr_session):
    from models import Generation, User
    from utils.hmr_durable_jobs import create_hmr_render_job_record, update_hmr_render_job_record

    user = User(email="missing-video@example.com", password_hash="x")
    hmr_session.add(user)
    await hmr_session.flush()
    generation = Generation(user_id=user.id, input_type="video", input_content="script", status="processing")
    hmr_session.add(generation)
    await hmr_session.flush()
    job = await create_hmr_render_job_record(
        hmr_session,
        generation_id=generation.id,
        user_id=user.id,
        run_id="missing-video-run",
        request_payload={},
    )

    done = await update_hmr_render_job_record(
        hmr_session,
        job.id,
        status="success",
        percent=100,
        step="done",
        message="Done",
        result={"video_path": "missing-video-run.mp4"},
    )

    assert done.status == "failed"
    assert done.step == "missing_video_artifact"
    await hmr_session.refresh(generation)
    assert generation.status == "failed"
    assert generation.video_file is None
    assert "no final MP4" in generation.error_message


@pytest.mark.asyncio
async def test_hmr_durable_job_recovery_marks_queued_and_processing_failed(hmr_session):
    from models import Generation, User
    from utils.hmr_durable_jobs import create_hmr_render_job_record, recover_interrupted_hmr_jobs, update_hmr_render_job_record

    user = User(email="recover@example.com", password_hash="x")
    hmr_session.add(user)
    await hmr_session.flush()
    generation = Generation(user_id=user.id, input_type="video", input_content="script", status="queued")
    hmr_session.add(generation)
    await hmr_session.flush()
    queued = await create_hmr_render_job_record(
        hmr_session,
        generation_id=generation.id,
        user_id=user.id,
        run_id="queued-run",
        request_payload={},
    )
    processing = await create_hmr_render_job_record(
        hmr_session,
        generation_id=generation.id,
        user_id=user.id,
        run_id="processing-run",
        request_payload={},
    )
    await update_hmr_render_job_record(
        hmr_session,
        processing.id,
        status="processing",
        percent=30,
        step="rendering",
        message="Rendering",
    )

    recovered = await recover_interrupted_hmr_jobs(hmr_session)

    assert {job.id for job in recovered} == {queued.id, processing.id}
    assert all(job.status == "failed" for job in recovered)
    assert all(job.error_message == "server_restart_or_worker_crash" for job in recovered)
    assert all(job.worker_active is False for job in recovered)


@pytest.mark.asyncio
async def test_async_hmr_route_creates_durable_job_and_progress_uses_job_state(hmr_session, monkeypatch):
    from models import Generation, HMRRenderJob, User
    from routes.generate import GenerateVideoRequest, generate_free_video, get_video_generation_progress
    from utils.hmr_durable_jobs import update_hmr_render_job_record

    monkeypatch.setenv("ENABLE_HYBRID_MOTION_RENDERER", "1")
    monkeypatch.setenv("VIDEO_GENERATION_DRY_RUN", "1")

    user = User(email="route-async@example.com", password_hash="x")
    hmr_session.add(user)
    await hmr_session.flush()

    request = GenerateVideoRequest(
        script="Still spending three hours editing one Short? Use quick cuts to turn one idea into a tighter clip.",
        scene_mode="hybrid_motion",
        dry_run=True,
        hmr_async=True,
        duration_seconds=12,
        niche="creator workflow",
    )
    background_tasks = BackgroundTasks()
    response = await generate_free_video(request, background_tasks=background_tasks, db=hmr_session, current_user=user)

    assert response["queued"] is True
    assert response["render_invoked"] is False
    assert response["async_execution_status"] == "background_task"
    assert response["durable_progress"] is True
    assert len(background_tasks.tasks) == 1

    generation = await hmr_session.get(Generation, response["generation_id"])
    assert generation is not None
    assert generation.status == "queued"

    job_result = await hmr_session.execute(
        select(HMRRenderJob).where(HMRRenderJob.generation_id == response["generation_id"])
    )
    job = job_result.scalar_one()
    assert job.status == "queued"
    assert job.render_invoked is False
    assert job.progress_store == "hmr_render_jobs"

    queued_progress = await get_video_generation_progress(generation.id, current_user=user, db=hmr_session)
    assert queued_progress["status"] == "queued"
    assert queued_progress["hmr_render_job"]["run_id"] == job.run_id
    assert queued_progress["hmr_render_job"]["durable_progress"] is True

    await update_hmr_render_job_record(
        hmr_session,
        job.id,
        status="success",
        percent=100,
        step="done",
        message="HMR background render complete.",
        render_invoked=True,
        result={"video_path": str(_generated_video_path("route-async.mp4").resolve())},
    )
    generation.status = "success"
    await hmr_session.commit()

    success_progress = await get_video_generation_progress(generation.id, current_user=user, db=hmr_session)
    assert success_progress["status"] == "success"
    assert success_progress["percent"] == 100
    assert success_progress["hmr_render_job"]["worker_active"] is False
    assert success_progress["hmr_render_job"]["render_invoked"] is True

    await update_hmr_render_job_record(
        hmr_session,
        job.id,
        status="failed",
        percent=0,
        step="error",
        message="HMR background render failed.",
        error_message="mock failure",
        render_invoked=True,
    )
    generation.status = "failed"
    generation.error_message = "mock failure"
    await hmr_session.commit()

    failed_progress = await get_video_generation_progress(generation.id, current_user=user, db=hmr_session)
    assert failed_progress["status"] == "failed"
    assert failed_progress["percent"] == 0
    assert failed_progress["message"] == "mock failure"
    assert failed_progress["hmr_render_job"]["worker_active"] is False


@pytest.mark.asyncio
async def test_hmr_video_history_falls_back_to_hmr_job_artifact_path(hmr_session, tmp_path):
    from models import Generation, HMRRenderJob, User
    from routes.generate import get_video_history_item

    user = User(email="fallback@example.com", password_hash="x")
    hmr_session.add(user)
    await hmr_session.flush()

    generation = Generation(
        user_id=user.id,
        input_type="video",
        input_content="hmr video fallback",
        status="success",
        video_run_id="run-123",
        video_file=None,
    )
    hmr_session.add(generation)
    await hmr_session.flush()

    video_path = _generated_video_path("run-123.mp4")

    job = HMRRenderJob(
        id="job-123",
        generation_id=generation.id,
        user_id=user.id,
        run_id="run-123",
        status="success",
        percent=100,
        step="done",
        message="Done",
        artifact_paths_json={"video": str(video_path.resolve())},
        result_json={"hybrid_motion": {"video_path": str(video_path.resolve())}},
    )
    hmr_session.add(job)
    await hmr_session.commit()

    history_item = await get_video_history_item(generation.id, current_user=user, db=hmr_session)
    assert history_item["file"] == "test_hmr_contract/run-123.mp4"
    assert history_item["video_url"] == "/api/generate/video/download/test_hmr_contract/run-123.mp4"
    assert history_item["download_url"] == "/api/generate/video/download/test_hmr_contract/run-123.mp4"


@pytest.mark.asyncio
async def test_hmr_video_history_list_falls_back_to_hmr_job_artifact_paths(hmr_session):
    from models import Generation, HMRRenderJob, User
    from routes.generate import get_video_history

    user = User(email="list-fallback@example.com", password_hash="x")
    hmr_session.add(user)
    await hmr_session.flush()

    generation = Generation(
        user_id=user.id,
        input_type="video",
        input_content="hmr list fallback",
        status="success",
        video_run_id="run-456",
        video_file=None,
        video_thumbnail=None,
    )
    hmr_session.add(generation)
    await hmr_session.flush()

    video_path = _generated_video_path("run-456.mp4")
    job = HMRRenderJob(
        id="job-456",
        generation_id=generation.id,
        user_id=user.id,
        run_id="run-456",
        status="success",
        percent=100,
        step="done",
        message="Done",
        artifact_paths_json={"video": str(video_path.resolve())},
        result_json={},
    )
    hmr_session.add(job)
    await hmr_session.commit()

    history = await get_video_history(current_user=user, db=hmr_session)
    assert isinstance(history, list)
    assert len(history) == 1
    row = history[0]
    assert row["file"] == "test_hmr_contract/run-456.mp4"
    assert row["video_url"] == "/api/generate/video/download/test_hmr_contract/run-456.mp4"
    assert row["download_url"] == "/api/generate/video/download/test_hmr_contract/run-456.mp4"
    assert row["thumbnail_url"] is None


@pytest.mark.asyncio
async def test_hmr_video_history_list_falls_back_to_hybrid_motion_result_json(hmr_session):
    from models import Generation, HMRRenderJob, User
    from routes.generate import get_video_history

    user = User(email="list-result-fallback@example.com", password_hash="x")
    hmr_session.add(user)
    await hmr_session.flush()

    generation = Generation(
        user_id=user.id,
        input_type="video",
        input_content="hmr result json fallback",
        status="success",
        video_run_id="run-789",
        video_file=None,
        video_thumbnail=None,
    )
    hmr_session.add(generation)
    await hmr_session.flush()

    video_path = _generated_video_path("run-789.mp4")
    job = HMRRenderJob(
        id="job-789",
        generation_id=generation.id,
        user_id=user.id,
        run_id="run-789",
        status="success",
        percent=100,
        step="done",
        message="Done",
        artifact_paths_json={},
        result_json={"hybrid_motion": {"video_path": str(video_path.resolve())}},
    )
    hmr_session.add(job)
    await hmr_session.commit()

    history = await get_video_history(current_user=user, db=hmr_session)
    assert isinstance(history, list)
    assert len(history) == 1
    row = history[0]
    assert row["file"] == "test_hmr_contract/run-789.mp4"
    assert row["video_url"] == "/api/generate/video/download/test_hmr_contract/run-789.mp4"
    assert row["download_url"] == "/api/generate/video/download/test_hmr_contract/run-789.mp4"
    assert row["thumbnail_url"] is None


@pytest.mark.asyncio
async def test_video_history_rejects_json_clip_list_as_downloadable_file(hmr_session):
    from models import Generation, User
    from routes.generate import get_video_history_item

    user = User(email="json-list-video@example.com", password_hash="x")
    hmr_session.add(user)
    await hmr_session.flush()

    generation = Generation(
        user_id=user.id,
        input_type="video",
        input_content="clip list is not a final video",
        status="success",
        video_file='["raw/clip-one.mp4", "raw/clip-two.mp4"]',
    )
    hmr_session.add(generation)
    await hmr_session.commit()

    history_item = await get_video_history_item(generation.id, current_user=user, db=hmr_session)
    assert history_item["status"] == "failed"
    assert history_item["file"] is None
    assert history_item["download_url"] is None
    assert history_item["warning"] == "Generation completed without a downloadable MP4 artifact."


@pytest.mark.asyncio
async def test_download_endpoint_returns_generated_mp4_and_blocks_traversal():
    from fastapi import HTTPException
    from fastapi.responses import FileResponse
    from routes.generate import download_generated_video

    video_path = _generated_video_path("downloadable.mp4")
    response = await download_generated_video("test_hmr_contract/downloadable.mp4")
    assert isinstance(response, FileResponse)
    assert Path(response.path) == video_path.resolve()

    with pytest.raises(HTTPException) as exc:
        await download_generated_video("../secret.mp4")
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_ui_preview_hybrid_motion_generates_downloadable_local_mp4(hmr_session, monkeypatch, tmp_path):
    import routes.generate as generate_route
    from models import Generation, User
    from routes.generate import (
        GenerateFromPreviewRequest,
        download_generated_video,
        generate_video_from_preview,
        get_video_history_item,
    )

    monkeypatch.setenv("ENABLE_HYBRID_MOTION_RENDERER", "1")
    monkeypatch.setenv("VIDEO_GENERATION_DRY_RUN", "0")
    monkeypatch.setenv("ALLOW_PAID_PROVIDERS", "0")
    monkeypatch.setenv("ALLOW_RUNWAYML", "0")
    monkeypatch.setenv("ALLOW_ELEVENLABS", "0")
    monkeypatch.setenv("ALLOW_GEMINI", "0")
    monkeypatch.setenv("ALLOW_OPENAI", "0")
    monkeypatch.setenv("ALLOW_ANTHROPIC", "0")
    monkeypatch.setattr(generate_route, "AsyncSessionLocal", lambda: hmr_session)
    monkeypatch.setattr(
        generate_route,
        "generate_voice",
        lambda request: type("VoiceResult", (), {"audio_file": None})(),
    )

    render_calls = []

    def fake_render_hybrid_video(**kwargs):
        render_calls.append(kwargs)
        output_path = Path(kwargs["output_path"])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"fake ui hmr mp4 bytes")
        return {
            "video_path": str(output_path),
            "duration": 30.0,
            "scene_reports": [{"scene_id": 1, "template": "local_hmr"}],
            "media_mix": {"LOCAL_FALLBACK": 1},
            "warnings": [],
        }

    monkeypatch.setattr(
        "utils.hybrid_motion_renderer.render_hybrid_video",
        fake_render_hybrid_video,
    )
    monkeypatch.setattr(
        "utils.hmr_ui_productization.materialize_hmr_ui_review_workflow",
        lambda **kwargs: {
            "review_package_status": "created",
            "artifact_paths": {"video": kwargs["video_path"]},
            "full_render_required": False,
        },
    )

    user = User(email="ui-hmr@example.com", password_hash="x")
    hmr_session.add(user)
    await hmr_session.flush()

    request = GenerateFromPreviewRequest(
        preview_id="ui-preview-1",
        scene_mode="hybrid_motion",
        dry_run=False,
        script=(
            "Hook: I pasted one script, and AI built the whole Short. "
            "Body: The app split it into scenes, created visuals, added captions, "
            "and prepared the video without spending credits. "
            "CTA: This is the recovery test. If download works, production is back."
        ),
        tts_provider="free",
        approved_scenes=[
            {
                "scene_index": 0,
                "scene_type": "hook",
                "caption_text": "I pasted one script, and AI built the whole Short.",
                "description": "Local UI proof card",
                "duration": 5,
                "method": "image_to_video",
            },
            {
                "scene_index": 1,
                "scene_type": "body",
                "caption_text": "The app split it into scenes and added captions.",
                "description": "Local editing timeline",
                "duration": 10,
                "method": "extend",
            },
            {
                "scene_index": 2,
                "scene_type": "cta",
                "caption_text": "If download works, production is back.",
                "description": "Download button success",
                "duration": 5,
                "method": "extend",
            },
        ],
        confirmed_plan={"scene_mode": "hybrid_motion"},
    )

    background_tasks = BackgroundTasks()
    queued = await generate_video_from_preview(
        request,
        background_tasks=background_tasks,
        current_user=user,
        db=hmr_session,
    )
    assert queued["status"] == "queued"
    assert len(background_tasks.tasks) == 1

    await background_tasks.tasks[0]()

    generation = await hmr_session.get(Generation, queued["generation_id"])
    assert generation.status == "success"
    assert generation.video_file.endswith(".mp4")
    assert not generation.video_file.startswith(("[", "{"))
    assert generate_route._resolve_downloadable_generated_video_file(generation.video_file) == generation.video_file
    assert generation.runway_credits_used == 0.0
    assert generation.elevenlabs_credits_used == 0
    assert generation.total_cost_usd == 0.0
    assert render_calls
    assert render_calls[0]["use_free_tts"] is True
    assert render_calls[0]["output_path"].is_relative_to(generate_route._generated_videos_root())

    history_item = await get_video_history_item(generation.id, current_user=user, db=hmr_session)
    assert history_item["status"] == "success"
    assert history_item["download_url"] == f"/api/generate/video/download/{generation.video_file}"

    download = await download_generated_video(generation.video_file)
    assert download.media_type == "video/mp4"
    assert Path(download.path).exists()


@pytest.mark.asyncio
async def test_hmr_render_jobs_startup_ddl_is_idempotent(hmr_session):
    await hmr_session.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS hmr_render_jobs (
                id VARCHAR PRIMARY KEY,
                generation_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                run_id VARCHAR NOT NULL,
                status VARCHAR DEFAULT 'queued',
                percent INTEGER DEFAULT 2,
                step VARCHAR DEFAULT 'queued',
                message TEXT,
                error_message TEXT,
                request_json JSON,
                artifact_paths_json JSON,
                result_json JSON,
                execution_mode VARCHAR DEFAULT 'background_task',
                worker_active BOOLEAN DEFAULT 1,
                durable_progress BOOLEAN DEFAULT 1,
                progress_store VARCHAR DEFAULT 'hmr_render_jobs',
                render_invoked BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                started_at DATETIME,
                completed_at DATETIME,
                FOREIGN KEY(generation_id) REFERENCES generations(id),
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )
    )
    await hmr_session.execute(text("SELECT id, generation_id, progress_store FROM hmr_render_jobs LIMIT 1"))
