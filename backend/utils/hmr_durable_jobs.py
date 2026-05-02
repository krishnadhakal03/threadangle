"""Durable HMR background job persistence and recovery helpers."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import HMRRenderJob
from utils.hmr_render_jobs import create_hmr_render_job_state


TERMINAL_STATUSES = {"success", "failed"}


def _now() -> datetime:
    return datetime.utcnow()


def hmr_job_to_progress(job: HMRRenderJob) -> dict[str, Any]:
    state = create_hmr_render_job_state(
        run_id=job.run_id,
        generation_id=job.generation_id,
        artifact_paths=job.artifact_paths_json or {},
        active_worker=True,
    )
    state.status = job.status
    state.percent = int(job.percent or 0)
    state.step = job.step or job.status
    state.message = job.message or state.message
    state.error_message = job.error_message
    state.execution_mode = job.execution_mode or state.execution_mode
    state.worker_active = bool(job.worker_active)
    state.durable_progress = bool(job.durable_progress)
    state.progress_store = job.progress_store or state.progress_store
    state.render_invoked = bool(job.render_invoked)
    return state.to_progress()


async def create_hmr_render_job_record(
    session: AsyncSession,
    *,
    generation_id: int,
    user_id: int,
    run_id: str,
    request_payload: dict[str, Any],
    artifact_paths: dict[str, str] | None = None,
) -> HMRRenderJob:
    job = HMRRenderJob(
        id=str(uuid.uuid4()),
        generation_id=generation_id,
        user_id=user_id,
        run_id=run_id,
        status="queued",
        percent=2,
        step="queued",
        message="HMR render job queued for durable background worker.",
        request_json=request_payload,
        artifact_paths_json=artifact_paths or {},
        execution_mode="background_task",
        worker_active=True,
        durable_progress=True,
        progress_store="hmr_render_jobs",
        render_invoked=False,
    )
    session.add(job)
    await session.flush()
    return job


async def update_hmr_render_job_record(
    session: AsyncSession,
    job_id: str,
    *,
    status: str,
    percent: int,
    step: str,
    message: str,
    error_message: str | None = None,
    result: dict[str, Any] | None = None,
    render_invoked: bool | None = None,
) -> HMRRenderJob:
    job = await session.get(HMRRenderJob, job_id)
    if job is None:
        raise ValueError(f"HMR render job not found: {job_id}")
    job.status = status
    job.percent = max(0, min(100, int(percent)))
    job.step = step
    job.message = message
    job.error_message = error_message
    job.updated_at = _now()
    if status == "processing" and job.started_at is None:
        job.started_at = _now()
    if status in TERMINAL_STATUSES:
        job.completed_at = _now()
        job.worker_active = False
    if result is not None:
        job.result_json = result
    if render_invoked is not None:
        job.render_invoked = render_invoked
    await session.flush()
    return job


async def recover_interrupted_hmr_jobs(session: AsyncSession) -> list[HMRRenderJob]:
    """Mark non-terminal durable jobs as failed after process restart."""
    result = await session.execute(
        select(HMRRenderJob).where(HMRRenderJob.status.in_(["queued", "processing"]))
    )
    jobs = list(result.scalars().all())
    for job in jobs:
        job.status = "failed"
        job.percent = 0
        job.step = "interrupted"
        job.message = "HMR render job was interrupted before completion."
        job.error_message = "server_restart_or_worker_crash"
        job.worker_active = False
        job.completed_at = _now()
        job.updated_at = _now()
    await session.flush()
    return jobs
