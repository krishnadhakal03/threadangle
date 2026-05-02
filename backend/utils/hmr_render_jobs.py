"""Truthful job-state helpers for HMR async worker progress."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


HMR_RENDER_JOB_STATUSES = ("queued", "processing", "success", "failed")


def _utc_timestamp() -> str:
    return datetime.utcnow().isoformat()


def _clamp_percent(value: int) -> int:
    return max(0, min(100, int(value)))


@dataclass
class HMRRenderJobState:
    """Serializable state boundary shared by UI progress and future workers."""

    run_id: str
    generation_id: int | None = None
    execution_mode: str = "scaffold_only"
    worker_active: bool = False
    durable_progress: bool = False
    progress_store: str = "in_memory_task_progress"
    status: str = "queued"
    percent: int = 2
    step: str = "queued"
    message: str = "HMR job metadata scaffold created; no background worker is active."
    render_invoked: bool = False
    artifact_paths: dict[str, str] = field(default_factory=dict)
    error_message: str | None = None
    updated_at: str = field(default_factory=_utc_timestamp)

    def __post_init__(self) -> None:
        validate_hmr_render_job_status(self.status)
        self.percent = _clamp_percent(self.percent)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_progress(self) -> dict[str, Any]:
        return {
            "percent": self.percent,
            "message": self.error_message or self.message,
            "step": self.step,
            "updated_at": self.updated_at,
            "hmr_render_job": self.to_dict(),
        }


def validate_hmr_render_job_status(status: str) -> None:
    if status not in HMR_RENDER_JOB_STATUSES:
        raise ValueError(f"Invalid HMR render job status: {status}")


def create_hmr_render_job_state(
    *,
    run_id: str,
    generation_id: int | None = None,
    artifact_paths: dict[str, str] | None = None,
    active_worker: bool = False,
) -> HMRRenderJobState:
    if active_worker:
        return HMRRenderJobState(
            run_id=str(run_id),
            generation_id=generation_id,
            execution_mode="background_task",
            worker_active=True,
            durable_progress=True,
            progress_store="hmr_render_jobs",
            message="HMR render job queued for durable background worker.",
            artifact_paths=dict(artifact_paths or {}),
        )
    return HMRRenderJobState(
        run_id=str(run_id),
        generation_id=generation_id,
        artifact_paths=dict(artifact_paths or {}),
    )


def transition_hmr_render_job_state(
    state: HMRRenderJobState,
    *,
    status: str,
    percent: int | None = None,
    step: str | None = None,
    message: str | None = None,
    error_message: str | None = None,
    render_invoked: bool | None = None,
) -> HMRRenderJobState:
    validate_hmr_render_job_status(status)
    defaults = {
        "queued": (2, "queued", "HMR render job queued."),
        "processing": (15, "rendering", "HMR render job is running in a background worker."),
        "success": (100, "done", "HMR render job complete."),
        "failed": (0, "error", "HMR render job failed."),
    }
    default_percent, default_step, default_message = defaults[status]
    return HMRRenderJobState(
        run_id=state.run_id,
        generation_id=state.generation_id,
        execution_mode=state.execution_mode,
        worker_active=state.worker_active,
        durable_progress=state.durable_progress,
        progress_store=state.progress_store,
        status=status,
        percent=_clamp_percent(default_percent if percent is None else percent),
        step=default_step if step is None else step,
        message=default_message if message is None else message,
        render_invoked=state.render_invoked if render_invoked is None else render_invoked,
        artifact_paths=dict(state.artifact_paths),
        error_message=error_message,
    )


def seed_hmr_render_progress(
    progress_store: dict[int, dict[str, Any]],
    state: HMRRenderJobState,
) -> dict[str, Any]:
    if state.generation_id is None:
        raise ValueError("generation_id is required before seeding HMR progress.")
    progress = state.to_progress()
    progress_store[state.generation_id] = progress
    return progress
