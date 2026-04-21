import uuid
from typing import Dict, List

from utils.video_pipeline import (
    parse_script,
    build_scene_plan,
    fetch_scene_clips,
    assemble_video,
    make_scene_response,
    resolve_duration_seconds,
)


BATCH_JOBS: Dict[str, Dict[str, object]] = {}


def create_job(items: List[Dict[str, object]]) -> str:
    job_id = f"batch_{uuid.uuid4().hex[:10]}"
    BATCH_JOBS[job_id] = {
        "status": "queued",
        "items": items,
        "results": [],
        "error": None,
    }
    return job_id


async def run_job(job_id: str) -> Dict[str, object]:
    job = BATCH_JOBS.get(job_id)
    if not job:
        return {"status": "missing"}

    job["status"] = "running"
    results = []
    try:
        for item in job["items"]:
            script = (item.get("script") or "").strip()
            hook = item.get("hook")
            body = item.get("body")
            cta = item.get("cta")
            duration = int(item.get("duration_seconds") or 12)

            parts = parse_script(script, hook=hook, body=body, cta=cta)
            duration_seconds = resolve_duration_seconds(parts, duration)
            scenes = build_scene_plan(parts, duration_seconds=duration_seconds)
            scenes = await fetch_scene_clips(scenes, run_id=job_id)
            render = assemble_video(scenes, run_id=f"{job_id}_{len(results)+1}")
            results.append({
                "success": True,
                "video_path": render.get("video_path"),
                "subtitle_path": render.get("subtitle_path"),
                "scenes": make_scene_response(scenes),
            })

        job["status"] = "done"
        job["results"] = results
    except Exception as exc:
        job["status"] = "failed"
        job["error"] = str(exc)

    return job
