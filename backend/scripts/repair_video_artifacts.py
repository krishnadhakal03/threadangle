"""Diagnose and repair video artifact links for Generation/HMR jobs.

Usage from repo root:

    cd backend
    python scripts/repair_video_artifacts.py --generation-id 67
    python scripts/repair_video_artifacts.py --latest 10
    python scripts/repair_video_artifacts.py --generation-id 67 --apply

This script is intentionally local/offline. It does not call paid providers or
external APIs. It only inspects the local DB, HMR job JSON, and files under the
backend/generated_videos tree.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

# Make backend imports work when script is run from backend/ or repo root.
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from database import AsyncSessionLocal  # noqa: E402
from models import Generation, HMRRenderJob  # noqa: E402
from sqlalchemy import select  # noqa: E402

VIDEO_EXTS = (".mp4", ".mov", ".m4v", ".webm")
IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp")
VIDEO_KEYS = {
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
THUMBNAIL_KEYS = {"thumbnail", "thumbnail_path", "video_thumbnail", "cover", "cover_path"}


def _iter_artifact_strings(value: Any, wanted_keys: set[str] | None = None) -> list[str]:
    out: list[str] = []

    def visit(node: Any, key_hint: str | None = None) -> None:
        if node is None:
            return
        if isinstance(node, str):
            lower = node.lower().split("?", 1)[0].split("#", 1)[0]
            key_ok = not wanted_keys or (key_hint or "").lower() in wanted_keys
            ext_ok = lower.endswith(VIDEO_EXTS + IMAGE_EXTS)
            if key_ok or ext_ok:
                out.append(node)
            return
        if isinstance(node, dict):
            for key, child in node.items():
                visit(child, str(key))
            return
        if isinstance(node, (list, tuple)):
            for child in node:
                visit(child, key_hint)

    visit(value)
    return out


def _resolve_existing_local_path(value: str | None) -> str | None:
    if not value:
        return None
    raw = str(value).strip()
    if not raw or raw.startswith(("http://", "https://", "data:")):
        return None
    raw = raw.split("?", 1)[0].split("#", 1)[0]
    p = Path(raw)

    candidates: list[Path] = []
    if p.is_absolute():
        candidates.append(p)
    else:
        candidates.extend(
            [
                Path.cwd() / p,
                BACKEND_ROOT / p,
                BACKEND_ROOT.parent / p,
                BACKEND_ROOT / "generated_videos" / p,
                BACKEND_ROOT / "generated_videos" / p.name,
            ]
        )

    for candidate in candidates:
        try:
            if candidate.exists() and candidate.is_file() and candidate.stat().st_size > 0:
                return str(candidate.resolve())
        except Exception:
            continue
    return None


def _candidate_video_paths(*payloads: Any) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for payload in payloads:
        for item in _iter_artifact_strings(payload, VIDEO_KEYS):
            if not str(item).lower().split("?", 1)[0].endswith(VIDEO_EXTS):
                continue
            if item not in seen:
                out.append(item)
                seen.add(item)
    return out


def _candidate_thumbnail_paths(*payloads: Any) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for payload in payloads:
        for item in _iter_artifact_strings(payload, THUMBNAIL_KEYS):
            if not str(item).lower().split("?", 1)[0].endswith(IMAGE_EXTS):
                continue
            if item not in seen:
                out.append(item)
                seen.add(item)
    return out


def _safe_json(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except Exception:
            return value
    return value


async def inspect_generation(generation_id: int, apply: bool = False) -> dict[str, Any]:
    async with AsyncSessionLocal() as session:
        generation = await session.get(Generation, generation_id)
        if generation is None:
            return {"generation_id": generation_id, "error": "generation_not_found"}

        job_result = await session.execute(
            select(HMRRenderJob)
            .where(HMRRenderJob.generation_id == generation_id)
            .order_by(HMRRenderJob.completed_at.desc().nullslast(), HMRRenderJob.updated_at.desc())
            .limit(1)
        )
        job = job_result.scalars().first()

        payloads = []
        if job is not None:
            payloads.extend([_safe_json(job.result_json), _safe_json(job.artifact_paths_json)])

        current_video_resolved = _resolve_existing_local_path(generation.video_file)
        candidate_videos = _candidate_video_paths(*payloads)
        resolved_video = current_video_resolved
        selected_source = "generation.video_file" if current_video_resolved else None
        for candidate in candidate_videos:
            candidate_resolved = _resolve_existing_local_path(candidate)
            if candidate_resolved:
                resolved_video = candidate_resolved
                selected_source = candidate
                break

        candidate_thumbnails = _candidate_thumbnail_paths(*payloads)
        resolved_thumb = _resolve_existing_local_path(generation.video_thumbnail)
        for thumb in candidate_thumbnails:
            if resolved_thumb:
                break
            resolved_thumb = _resolve_existing_local_path(thumb)

        report = {
            "generation": {
                "id": generation.id,
                "status": generation.status,
                "video_run_id": generation.video_run_id,
                "video_file": generation.video_file,
                "video_file_exists": bool(current_video_resolved),
                "video_thumbnail": generation.video_thumbnail,
                "error_message": generation.error_message,
            },
            "hmr_job": None
            if job is None
            else {
                "id": job.id,
                "status": job.status,
                "percent": job.percent,
                "step": job.step,
                "message": job.message,
                "error_message": job.error_message,
                "run_id": job.run_id,
                "render_invoked": job.render_invoked,
                "artifact_paths_json": _safe_json(job.artifact_paths_json),
                "result_json": _safe_json(job.result_json),
            },
            "candidates": {
                "video_paths": candidate_videos,
                "thumbnail_paths": candidate_thumbnails,
                "selected_video": resolved_video,
                "selected_video_source": selected_source,
                "selected_thumbnail": resolved_thumb,
            },
            "apply": apply,
            "action": "none",
        }

        if apply:
            if resolved_video:
                generation.video_file = resolved_video
                if job is not None:
                    generation.video_run_id = generation.video_run_id or job.run_id
                generation.status = "success"
                generation.error_message = None
                if resolved_thumb:
                    generation.video_thumbnail = resolved_thumb
                if job is not None:
                    job.status = "success"
                    job.percent = 100
                    job.step = "completed"
                    job.message = "Final MP4 artifact linked to generation."
                    job.error_message = None
                    job.worker_active = False
                report["action"] = "backfilled_generation_video_file"
            else:
                generation.status = "failed"
                generation.error_message = "No final MP4 artifact found during repair_video_artifacts diagnostic."
                if job is not None:
                    job.status = "failed"
                    job.percent = 100
                    job.step = "missing_video_artifact"
                    job.message = "No final MP4 artifact found during repair diagnostic."
                    job.error_message = job.message
                    job.worker_active = False
                report["action"] = "marked_failed_missing_video_artifact"
            await session.commit()

        return report


async def latest_generation_ids(limit: int) -> list[int]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Generation.id).order_by(Generation.id.desc()).limit(limit))
        return [int(row[0]) for row in result.fetchall()]


def print_recent_mp4s(limit: int = 20) -> None:
    print("\nRecent MP4 files:")
    root = BACKEND_ROOT / "generated_videos"
    if not root.exists():
        print(f"  generated_videos folder not found: {root}")
        return
    files = sorted(root.rglob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)[:limit]
    for p in files:
        print(f"  {p} size={p.stat().st_size}")


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generation-id", type=int, help="Specific generation id to inspect/repair")
    parser.add_argument("--latest", type=int, default=0, help="Inspect latest N generations")
    parser.add_argument("--apply", action="store_true", help="Apply repair/backfill/failed status updates")
    parser.add_argument("--show-files", action="store_true", help="List recent local MP4 files")
    args = parser.parse_args()

    ids: list[int] = []
    if args.generation_id:
        ids.append(args.generation_id)
    if args.latest:
        ids.extend(await latest_generation_ids(args.latest))
    if not ids:
        parser.error("Provide --generation-id or --latest")

    for generation_id in dict.fromkeys(ids):
        print("\n" + "=" * 80)
        print(f"Generation {generation_id}")
        print(json.dumps(await inspect_generation(generation_id, apply=args.apply), indent=2, default=str)[:12000])

    if args.show_files:
        print_recent_mp4s()


if __name__ == "__main__":
    asyncio.run(main())
