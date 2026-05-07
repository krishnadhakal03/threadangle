"""Durable HMR background job persistence and recovery helpers."""

from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Generation, HMRRenderJob
from utils.hmr_render_jobs import create_hmr_render_job_state


TERMINAL_STATUSES = {"success", "failed"}
_VIDEO_KEYS = {
    "video",
    "final_video",
    "final_video_path",
    "video_file",
    "video_path",
    "output_path",
    "rendered_video",
    "rendered_video_path",
    "platform_safe_video",
    "platform_safe_video_path",
}
_THUMBNAIL_KEYS = {"thumbnail", "thumbnail_path", "video_thumbnail", "cover", "cover_path"}


def _now() -> datetime:
    return datetime.utcnow()


def _backend_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _generated_root() -> Path:
    return _backend_root() / "generated_videos"


def _iter_artifact_strings(value: Any, *, wanted_keys: set[str] | None = None) -> list[str]:
    """Recursively collect artifact-looking string values from nested JSON."""
    out: list[str] = []

    def visit(node: Any, key_hint: str | None = None) -> None:
        if node is None:
            return
        if isinstance(node, str):
            lower = node.lower()
            key_ok = not wanted_keys or (key_hint or "").lower() in wanted_keys
            ext_ok = lower.endswith((".mp4", ".mov", ".m4v", ".webm", ".png", ".jpg", ".jpeg"))
            if key_ok or ext_ok:
                out.append(node)
            return
        if isinstance(node, dict):
            for k, v in node.items():
                visit(v, str(k))
            return
        if isinstance(node, (list, tuple)):
            for item in node:
                visit(item, key_hint)

    visit(value)
    return out


def _candidate_video_paths(*payloads: Any) -> list[str]:
    candidates: list[str] = []
    for payload in payloads:
        candidates.extend(_iter_artifact_strings(payload, wanted_keys=_VIDEO_KEYS))
    # Keep only likely video values first; recursive collector may include thumbnails.
    video_candidates = [p for p in candidates if str(p).lower().split("?")[0].endswith((".mp4", ".mov", ".m4v", ".webm"))]
    # Preserve order and de-dupe.
    seen = set()
    out = []
    for p in video_candidates:
        if p not in seen:
            out.append(p)
            seen.add(p)
    return out


def _candidate_thumbnail_paths(*payloads: Any) -> list[str]:
    candidates: list[str] = []
    for payload in payloads:
        candidates.extend(_iter_artifact_strings(payload, wanted_keys=_THUMBNAIL_KEYS))
    image_candidates = [p for p in candidates if str(p).lower().split("?")[0].endswith((".png", ".jpg", ".jpeg", ".webp"))]
    seen = set()
    out = []
    for p in image_candidates:
        if p not in seen:
            out.append(p)
            seen.add(p)
    return out


def _resolve_existing_local_path(path_value: str | None) -> str | None:
    """Resolve a renderer artifact path to an existing local file path."""
    if not path_value:
        return None
    raw = str(path_value).strip()
    if not raw or raw.startswith(("http://", "https://", "data:")):
        return None
    if raw.startswith(("[", "{")):
        return None

    # Remove query/hash if any accidentally came from a URL-like local value.
    raw = raw.split("?", 1)[0].split("#", 1)[0]
    p = Path(raw)
    backend = _backend_root()
    generated_root = _generated_root().resolve()

    candidates = []
    if p.is_absolute():
        candidates.append(p)
    else:
        candidates.extend([
            Path.cwd() / p,
            backend / p,
            backend.parent / p,
            backend / "generated_videos" / p,
            backend / "generated_videos" / p.name,
        ])

    for candidate in candidates:
        try:
            resolved = candidate.resolve()
            if generated_root not in resolved.parents:
                continue
            if resolved.exists() and resolved.is_file() and resolved.stat().st_size > 0:
                return str(resolved)
        except Exception:
            continue
    return None


def _relative_generated_asset_path(path_value: str | None) -> str | None:
    resolved = _resolve_existing_local_path(path_value)
    if not resolved:
        return None
    try:
        return str(Path(resolved).relative_to(_generated_root().resolve())).replace("\\", "/")
    except Exception:
        return None


def _valid_generation_video_path(generation: Generation | None) -> str | None:
    if generation is None:
        return None
    return _resolve_existing_local_path(getattr(generation, "video_file", None))


async def _finalize_generation_video_artifact(
    session: AsyncSession,
    job: HMRRenderJob,
    *,
    result: dict[str, Any] | None,
) -> bool:
    """Backfill Generation.video_file from durable HMR artifacts.

    A durable HMR job must not be considered successful unless a final local MP4
    can be found either on the Generation row or in HMR result/artifact JSON.
    """
    generation = await session.get(Generation, job.generation_id)
    existing_video = _valid_generation_video_path(generation)
    if existing_video:
        print(f"[VIDEO_FINALIZE] generation already has valid video_file: {existing_video}")
        return True

    payloads = [result or {}, job.result_json or {}, job.artifact_paths_json or {}]
    for candidate in _candidate_video_paths(*payloads):
        resolved = _resolve_existing_local_path(candidate)
        if not resolved:
            continue
        if generation is not None:
            generation.video_file = _relative_generated_asset_path(resolved) or resolved
            generation.video_run_id = generation.video_run_id or job.run_id
            generation.status = "success"
            generation.error_message = None
            if not generation.video_thumbnail:
                for thumb in _candidate_thumbnail_paths(*payloads):
                    resolved_thumb = _resolve_existing_local_path(thumb)
                    if resolved_thumb:
                        generation.video_thumbnail = _relative_generated_asset_path(resolved_thumb) or resolved_thumb
                        break
        print(f"[VIDEO_FINALIZE] generation.video_file backfilled from HMR artifact: {resolved}")
        await session.flush()
        return True

    print(
        "[VIDEO_FINALIZE] missing final MP4 for "
        f"generation_id={job.generation_id} run_id={job.run_id}. "
        f"artifact_paths_json={job.artifact_paths_json} result_json={result or job.result_json}"
    )
    if generation is not None:
        generation.status = "failed"
        generation.error_message = "Render completed metadata but no final MP4 artifact was found."
    await session.flush()
    return False


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

    final_status = status
    final_percent = percent
    final_step = step
    final_message = message
    final_error_message = error_message

    if result is not None:
        job.result_json = result
    if render_invoked is not None:
        job.render_invoked = render_invoked

    # Critical production contract: success requires a downloadable MP4.
    if status == "success":
        has_video = await _finalize_generation_video_artifact(session, job, result=result)
        if not has_video:
            final_status = "failed"
            final_percent = 100
            final_step = "missing_video_artifact"
            final_message = "Render completed metadata but no final MP4 artifact was found."
            final_error_message = final_message

    job.status = final_status
    job.percent = max(0, min(100, int(final_percent)))
    job.step = final_step
    job.message = final_message
    job.error_message = final_error_message
    job.updated_at = _now()
    if final_status == "processing" and job.started_at is None:
        job.started_at = _now()
    if final_status in TERMINAL_STATUSES:
        job.completed_at = _now()
        job.worker_active = False
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
