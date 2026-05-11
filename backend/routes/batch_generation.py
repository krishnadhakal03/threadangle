"""
Batch video generation — queue multiple videos by topic list.

No credits are consumed during queuing.
Each video in the batch is generated via the existing pipeline when
the background task runs, exactly as if the user had submitted it manually.

Endpoints:
  POST /api/batch/generate       — queue a batch
  GET  /api/batch/{batch_id}     — poll status and results
  GET  /api/batch/               — list user's batches
"""
from __future__ import annotations

import json
import uuid
import asyncio
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db, AsyncSessionLocal
from models import User, Generation, BatchJob
from auth import require_full_access_user

from utils.video_pipeline import (
    parse_script,
    build_scene_plan,
    resolve_duration_seconds,
    fetch_scene_clips,
    assemble_video,
    make_scene_response,
    new_run_id,
)
from routes.voice_gen import generate_voice, VoiceGenRequest
from utils.render_guard import (
    acquire_render_slot,
    assert_video_duration_allowed,
    release_render_slot,
    require_video_render_access,
    run_with_render_timeout,
)

router = APIRouter(prefix="/api/batch", tags=["Batch Generation"])


# ── Request / Response schemas ────────────────────────────────────────────────

class BatchRequest(BaseModel):
    topics: List[str]
    niche: str = "general"
    duration_seconds: int = 30
    scene_mode: str = "stock"          # stock | hybrid | ai
    runway_model: str = "gen4_turbo"   # default model for batch (budget-conscious)


class BatchStatusResponse(BaseModel):
    batch_id: str
    status: str
    total: int
    completed: int
    failed: int
    progress_pct: float
    estimated_minutes_remaining: Optional[float]
    videos: List[dict]


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/generate")
async def create_batch(
    req: BatchRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_video_render_access),
):
    """
    Queue a batch of videos. Returns immediately with batch_id.
    Poll GET /api/batch/{batch_id} for progress.

    No credits consumed at this point — generation happens per-video
    in background tasks.
    """
    if not req.topics:
        raise HTTPException(status_code=400, detail="topics list cannot be empty")
    if len(req.topics) > 30:
        raise HTTPException(status_code=400, detail="Maximum 30 topics per batch")
    assert_video_duration_allowed(req.duration_seconds)
    token = await acquire_render_slot()

    batch_id = f"batch_{uuid.uuid4().hex[:12]}"
    batch = BatchJob(
        id=batch_id,
        user_id=current_user.id,
        total_videos=len(req.topics),
        status="queued",
        niche=req.niche,
        topics_json=json.dumps(req.topics),
    )
    db.add(batch)
    await db.commit()

    background_tasks.add_task(
        _generate_batch_with_slot,
        token=token,
        batch_id=batch_id,
        topics=req.topics,
        niche=req.niche,
        duration_seconds=req.duration_seconds,
        scene_mode=req.scene_mode,
        runway_model=req.runway_model,
        user_id=current_user.id,
    )

    return {
        "batch_id": batch_id,
        "total_videos": len(req.topics),
        "status": "queued",
        "estimated_minutes": round(len(req.topics) * 2.5, 1),
        "poll_url": f"/api/batch/{batch_id}",
    }


async def _generate_batch_with_slot(
    token: object,
    batch_id: str,
    topics: list[str],
    niche: str,
    duration_seconds: int,
    scene_mode: str,
    runway_model: str,
    user_id: int,
):
    try:
        for idx, topic in enumerate(topics):
            try:
                await run_with_render_timeout(
                    _generate_one(
                        batch_id=batch_id,
                        topic=topic,
                        niche=niche,
                        duration_seconds=duration_seconds,
                        scene_mode=scene_mode,
                        runway_model=runway_model,
                        user_id=user_id,
                        position=idx,
                    )
                )
            except TimeoutError as exc:
                async with AsyncSessionLocal() as db:
                    result = await db.execute(select(BatchJob).where(BatchJob.id == batch_id))
                    batch = result.scalar_one_or_none()
                    if batch:
                        batch.status = "failed"
                        batch.error_message = f"Video render exceeded timeout: {exc}"[:500]
                        await db.commit()
                break
    finally:
        await release_render_slot(token)


@router.get("/")
async def list_batches(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_full_access_user),
):
    """List all batch jobs for the current user."""
    result = await db.execute(
        select(BatchJob)
        .where(BatchJob.user_id == current_user.id)
        .order_by(BatchJob.created_at.desc())
        .limit(20)
    )
    batches = result.scalars().all()
    return [
        {
            "batch_id": b.id,
            "status": b.status,
            "total": b.total_videos,
            "completed": b.completed_videos,
            "failed": b.failed_videos,
            "niche": b.niche,
            "created_at": b.created_at.isoformat() if b.created_at else None,
        }
        for b in batches
    ]


@router.get("/{batch_id}")
async def get_batch_status(
    batch_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_full_access_user),
):
    """Poll batch progress. Returns per-video status and download URLs."""
    result = await db.execute(
        select(BatchJob)
        .where(BatchJob.id == batch_id, BatchJob.user_id == current_user.id)
    )
    batch = result.scalar_one_or_none()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    videos_result = await db.execute(
        select(Generation)
        .where(
            Generation.batch_id == batch_id,
            Generation.user_id == current_user.id,
        )
        .order_by(Generation.created_at)
    )
    videos = videos_result.scalars().all()

    total = batch.total_videos or 1
    completed = sum(1 for v in videos if v.status == "success")
    failed = sum(1 for v in videos if v.status == "failed")
    progress_pct = round((completed + failed) / total * 100, 1)
    remaining = total - completed - failed
    est_remaining = round(remaining * 2.5, 1) if remaining > 0 else 0.0

    return {
        "batch_id": batch_id,
        "status": batch.status,
        "total": total,
        "completed": completed,
        "failed": failed,
        "progress_pct": progress_pct,
        "estimated_minutes_remaining": est_remaining,
        "videos": [
            {
                "id": v.id,
                "topic": v.topic,
                "status": v.status,
                "download_url": f"/api/generate/video/download/{v.video_file}" if v.video_file else None,
                "thumbnail_url": f"/api/generate/video/download/{v.video_thumbnail}" if v.video_thumbnail else None,
                "seo_title": v.seo_title,
                "runway_credits_used": v.runway_credits_used,
                "error": v.error_message if v.status == "failed" else None,
            }
            for v in videos
        ],
    }


# ── Background worker ─────────────────────────────────────────────────────────

async def _generate_one(
    batch_id: str,
    topic: str,
    niche: str,
    duration_seconds: int,
    scene_mode: str,
    runway_model: str,
    user_id: int,
    position: int,
):
    """Background task: generate a single video and save the Generation record."""
    async with AsyncSessionLocal() as db:
        try:
            print(f"[BATCH] {batch_id} [{position}] Starting: {topic}")

            # ── Update batch status to processing on first item ────────────
            if position == 0:
                result = await db.execute(select(BatchJob).where(BatchJob.id == batch_id))
                batch = result.scalar_one_or_none()
                if batch:
                    batch.status = "processing"
                    await db.commit()

            # ── Build script from topic ────────────────────────────────────
            script_text = topic   # Topic IS the hook text for batch mode
            parts = parse_script(script_text)
            duration = resolve_duration_seconds(parts, duration_seconds)
            assert_video_duration_allowed(duration)
            scenes = build_scene_plan(parts, duration)
            run_id = new_run_id()

            # ── Generate voiceover (ElevenLabs or pyttsx3 fallback) ────────
            audio_path = None
            try:
                tts = generate_voice(VoiceGenRequest(text=script_text))
                audio_path = tts.audio_file
            except Exception as tts_exc:
                print(f"[BATCH] TTS failed for '{topic}': {tts_exc}")

            # ── Fetch scene clips (stock-only by default, no credits risk) ─
            scenes = await run_with_render_timeout(
                fetch_scene_clips(
                    scenes,
                    run_id=run_id,
                    mode=scene_mode,
                    runway_model=runway_model,
                )
            )

            # ── Assemble video ─────────────────────────────────────────────
            render = await run_with_render_timeout(
                asyncio.to_thread(assemble_video, scenes, run_id=run_id, audio_path=audio_path)
            )

            runway_credits = round(
                sum(float(getattr(s, "credits_cost", 0.0) or 0.0) for s in scenes), 2
            )
            el_chars = len(script_text)

            gen = Generation(
                user_id=user_id,
                input_type="video",
                input_content=topic[:5000],
                status="success",
                video_run_id=run_id,
                video_file=render.get("video_path", ""),
                video_duration_seconds=duration,
                video_thumbnail=render.get("thumbnail_path"),
                video_scenes_json=json.dumps(make_scene_response(scenes)),
                batch_id=batch_id,
                topic=topic[:255],
                runway_credits_used=runway_credits,
                elevenlabs_credits_used=el_chars,
                total_cost_usd=round(runway_credits * 0.01 + (el_chars / 1000.0) * 0.30, 4),
            )
            db.add(gen)

            # Update batch counters
            result = await db.execute(select(BatchJob).where(BatchJob.id == batch_id))
            batch = result.scalar_one_or_none()
            if batch:
                batch.completed_videos = (batch.completed_videos or 0) + 1
                if (batch.completed_videos + (batch.failed_videos or 0)) >= batch.total_videos:
                    batch.status = "done"
                    batch.completed_at = datetime.utcnow()

            await db.commit()
            print(f"[BATCH] {batch_id} [{position}] Done: {topic}")

        except Exception as exc:
            print(f"[BATCH] {batch_id} [{position}] FAILED: {topic} — {exc}")
            try:
                fail_gen = Generation(
                    user_id=user_id,
                    input_type="video",
                    input_content=topic[:5000],
                    status="failed",
                    error_message=str(exc)[:500],
                    batch_id=batch_id,
                    topic=topic[:255],
                )
                db.add(fail_gen)
                result = await db.execute(select(BatchJob).where(BatchJob.id == batch_id))
                batch = result.scalar_one_or_none()
                if batch:
                    batch.failed_videos = (batch.failed_videos or 0) + 1
                    if (batch.completed_videos + batch.failed_videos) >= batch.total_videos:
                        batch.status = "done"
                        batch.completed_at = datetime.utcnow()
                await db.commit()
            except Exception:
                pass
