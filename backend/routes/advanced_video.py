from fastapi import APIRouter, Depends, HTTPException, Body, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict
from pathlib import Path

from utils.seo import generate_seo
from utils.thumbnail import generate_thumbnail
from utils.captions import build_word_timestamps, build_srt_from_words
from utils.pattern_interrupts import build_interrupt_schedule
from utils.batch_queue import create_job, run_job, BATCH_JOBS
from utils.optimization import ingest_metrics_csv, summarize_metrics
from utils.render_guard import (
    acquire_render_slot,
    assert_video_duration_allowed,
    release_render_slot,
    require_video_render_access,
    run_with_render_timeout,
)

router = APIRouter(prefix="/api/generate", tags=["ViralVideo"])


class SeoRequest(BaseModel):
    topic: str
    niche: str = "general"
    keywords: List[str] = []


class ThumbnailRequest(BaseModel):
    topic: str
    niche: str = "general"
    model: str | None = None


class CaptionsRequest(BaseModel):
    text: str
    duration_seconds: float
    style: str = "tiktok"


class InterruptRequest(BaseModel):
    duration_seconds: float
    min_gap: float = 3.0
    max_gap: float = 5.0


class BatchRequest(BaseModel):
    items: List[Dict[str, object]]


@router.post("/seo")
async def generate_seo_content(req: SeoRequest):
    try:
        return generate_seo(req.topic, req.niche, req.keywords)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/thumbnail")
async def generate_thumbnail_image(req: ThumbnailRequest):
    model = req.model or "gpt-image-1"
    try:
        return generate_thumbnail(req.topic, req.niche, model=model)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/thumbnail/download/{filename}")
async def download_thumbnail(filename: str):
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename.")
    file_path = Path(__file__).resolve().parents[1] / "generated_videos" / "thumbnails" / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Thumbnail not found.")
    return FileResponse(path=str(file_path), media_type="image/png", filename=filename)


@router.post("/captions")
async def generate_captions(req: CaptionsRequest, _=Depends(require_video_render_access)):
    assert_video_duration_allowed(req.duration_seconds)
    words = build_word_timestamps(req.text, req.duration_seconds)
    srt = build_srt_from_words(words)
    return {
        "style": req.style,
        "words": words,
        "srt": srt,
    }


@router.post("/pattern-interrupts")
async def generate_interrupts(req: InterruptRequest, _=Depends(require_video_render_access)):
    assert_video_duration_allowed(req.duration_seconds)
    return {
        "interrupts": build_interrupt_schedule(req.duration_seconds, req.min_gap, req.max_gap)
    }


@router.post("/batch")
async def create_batch_job(
    req: BatchRequest,
    background_tasks: BackgroundTasks,
    _=Depends(require_video_render_access),
):
    if not req.items:
        raise HTTPException(status_code=400, detail="Batch items cannot be empty.")
    for item in req.items:
        assert_video_duration_allowed(item.get("duration_seconds"))
    token = await acquire_render_slot()
    job_id = create_job(req.items)
    background_tasks.add_task(_run_job_with_slot, job_id, token)
    return {"job_id": job_id, "status": "queued"}


async def _run_job_with_slot(job_id: str, token: object):
    try:
        try:
            await run_with_render_timeout(run_job(job_id))
        except TimeoutError as exc:
            job = BATCH_JOBS.get(job_id)
            if job is not None:
                job["status"] = "failed"
                job["error"] = f"Video render exceeded timeout: {exc}"
    finally:
        await release_render_slot(token)


@router.get("/batch/{job_id}")
async def get_batch_job(job_id: str):
    job = BATCH_JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return job


@router.post("/metrics/upload")
async def upload_metrics(csv_text: str = Body(..., embed=True)):
    try:
        return ingest_metrics_csv(csv_text)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/metrics/summary")
async def get_metrics_summary():
    return summarize_metrics()
