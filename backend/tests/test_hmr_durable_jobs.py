from __future__ import annotations

import sys
from pathlib import Path

import pytest
import pytest_asyncio
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
