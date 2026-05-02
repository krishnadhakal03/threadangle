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

    done = await update_hmr_render_job_record(
        hmr_session,
        job.id,
        status="success",
        percent=100,
        step="done",
        message="Done",
        result={"video_path": "out.mp4"},
    )
    assert done.status == "success"
    assert done.worker_active is False
    assert done.result_json == {"video_path": "out.mp4"}
    done_progress = hmr_job_to_progress(done)
    assert done_progress["hmr_render_job"]["status"] == "success"
    assert done_progress["hmr_render_job"]["worker_active"] is False


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
        result={"video_path": "backend/generated_videos/route-async.mp4"},
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
