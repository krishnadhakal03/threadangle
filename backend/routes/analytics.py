"""
Analytics dashboard — DB-only, zero API credits consumed.

Endpoints:
  GET /api/analytics/dashboard   — full overview
  GET /api/analytics/videos      — per-video performance table
  GET /api/analytics/credits     — credit & cost breakdown
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from database import get_db
from models import User, Generation, BatchJob
from auth import require_full_access_user

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/dashboard")
async def analytics_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_full_access_user),
):
    """
    Full analytics overview.

    Returns:
    - credit usage (runway + elevenlabs)
    - cost breakdown (avg per video, total spent)
    - model usage distribution
    - performance metrics (views, retention, CTR where available)
    - batch job summary
    """
    uid = current_user.id

    # ── Aggregate totals ──────────────────────────────────────────────────
    totals = await db.execute(
        select(
            func.count(Generation.id).label("total_videos"),
            func.sum(Generation.runway_credits_used).label("runway_credits"),
            func.sum(Generation.elevenlabs_credits_used).label("el_chars"),
            func.sum(Generation.total_cost_usd).label("total_cost"),
            func.avg(Generation.total_cost_usd).label("avg_cost"),
            func.avg(Generation.video_duration_seconds).label("avg_duration"),
            func.sum(Generation.youtube_views).label("total_views"),
            func.avg(Generation.youtube_retention).label("avg_retention"),
            func.avg(Generation.youtube_ctr).label("avg_ctr"),
        ).where(
            Generation.user_id == uid,
            Generation.status == "success",
        )
    )
    row = totals.one()

    total_videos   = int(row.total_videos or 0)
    runway_credits = float(row.runway_credits or 0)
    el_chars       = int(row.el_chars or 0)
    total_cost     = float(row.total_cost or 0)
    avg_cost       = float(row.avg_cost or 0)
    total_views    = int(row.total_views or 0)
    avg_retention  = float(row.avg_retention or 0)
    avg_ctr        = float(row.avg_ctr or 0)

    # Credit budget assumptions (adjust via env if needed)
    RUNWAY_BUDGET = 1000.0
    credits_remaining = max(0.0, RUNWAY_BUDGET - runway_credits)
    videos_remaining  = int(credits_remaining / avg_cost * 0.01) if avg_cost > 0 else 0

    # ── Model usage breakdown ─────────────────────────────────────────────
    # Note: per-scene model not stored at generation level yet — aggregate from
    # video_scenes_json in future. For now, show runway vs stock split.
    runway_videos = await db.execute(
        select(func.count(Generation.id))
        .where(Generation.user_id == uid, Generation.runway_credits_used > 0)
    )
    runway_vid_count = int(runway_videos.scalar() or 0)

    # ── Batch job summary ─────────────────────────────────────────────────
    batch_result = await db.execute(
        select(
            func.count(BatchJob.id).label("total_batches"),
            func.sum(BatchJob.completed_videos).label("batch_completed"),
            func.sum(BatchJob.failed_videos).label("batch_failed"),
        ).where(BatchJob.user_id == uid)
    )
    batch_row = batch_result.one()

    # ── Recent 5 videos ───────────────────────────────────────────────────
    recent_result = await db.execute(
        select(Generation)
        .where(Generation.user_id == uid, Generation.status == "success")
        .order_by(Generation.created_at.desc())
        .limit(5)
    )
    recent = recent_result.scalars().all()

    return {
        "summary": {
            "total_videos": total_videos,
            "total_views": total_views,
            "avg_retention_pct": round(avg_retention * 100, 1),
            "avg_ctr_pct": round(avg_ctr * 100, 2),
        },
        "credits": {
            "runway_used": round(runway_credits, 1),
            "runway_budget": RUNWAY_BUDGET,
            "runway_remaining": round(credits_remaining, 1),
            "elevenlabs_chars_used": el_chars,
            "videos_with_runway": runway_vid_count,
            "videos_stock_only": total_videos - runway_vid_count,
        },
        "cost": {
            "total_usd": round(total_cost, 4),
            "avg_per_video_usd": round(avg_cost, 4),
            "runway_spend_usd": round(runway_credits * 0.01, 4),
            "elevenlabs_spend_usd": round((el_chars / 1000.0) * 0.30, 4),
            "estimated_videos_remaining": videos_remaining,
        },
        "performance_tips": _generate_tips(avg_retention, avg_ctr, total_videos),
        "batch_summary": {
            "total_batches": int(batch_row.total_batches or 0),
            "batch_completed_videos": int(batch_row.batch_completed or 0),
            "batch_failed_videos": int(batch_row.batch_failed or 0),
        },
        "recent_videos": [
            {
                "id": v.id,
                "seo_title": v.seo_title or v.topic or "Untitled",
                "duration_s": v.video_duration_seconds,
                "runway_credits": v.runway_credits_used,
                "cost_usd": v.total_cost_usd,
                "views": v.youtube_views,
                "download_url": f"/api/generate/video/download/{v.video_file}" if v.video_file else None,
                "created_at": v.created_at.isoformat() if v.created_at else None,
            }
            for v in recent
        ],
    }


@router.get("/videos")
async def analytics_videos(
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_full_access_user),
):
    """Per-video performance table, paginated."""
    result = await db.execute(
        select(Generation)
        .where(Generation.user_id == current_user.id, Generation.status == "success")
        .order_by(Generation.created_at.desc())
        .limit(min(limit, 100))
        .offset(offset)
    )
    videos = result.scalars().all()

    count_result = await db.execute(
        select(func.count(Generation.id))
        .where(Generation.user_id == current_user.id, Generation.status == "success")
    )
    total = int(count_result.scalar() or 0)

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "videos": [
            {
                "id": v.id,
                "seo_title": v.seo_title or v.topic or "Untitled",
                "duration_s": v.video_duration_seconds,
                "runway_credits_used": v.runway_credits_used,
                "elevenlabs_chars": v.elevenlabs_credits_used,
                "cost_usd": v.total_cost_usd,
                "youtube_views": v.youtube_views,
                "youtube_retention_pct": round((v.youtube_retention or 0) * 100, 1),
                "youtube_ctr_pct": round((v.youtube_ctr or 0) * 100, 2),
                "batch_id": v.batch_id,
                "download_url": f"/api/generate/video/download/{v.video_file}" if v.video_file else None,
                "thumbnail_url": f"/api/generate/video/download/{v.video_thumbnail}" if v.video_thumbnail else None,
                "created_at": v.created_at.isoformat() if v.created_at else None,
            }
            for v in videos
        ],
    }


@router.patch("/videos/{generation_id}/performance")
async def update_video_performance(
    generation_id: int,
    views: int = 0,
    retention_pct: float = 0.0,
    ctr_pct: float = 0.0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_full_access_user),
):
    """
    Update real-world performance data for a video.
    Call this after manually recording YouTube analytics.
    """
    result = await db.execute(
        select(Generation).where(
            Generation.id == generation_id,
            Generation.user_id == current_user.id,
        )
    )
    gen = result.scalar_one_or_none()
    if not gen:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Video not found")

    gen.youtube_views = views
    gen.youtube_retention = retention_pct / 100.0
    gen.youtube_ctr = ctr_pct / 100.0
    await db.commit()
    return {"status": "updated", "id": generation_id}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _generate_tips(avg_retention: float, avg_ctr: float, total_videos: int) -> list:
    tips = []
    if total_videos < 5:
        tips.append("Generate at least 5 videos before drawing conclusions.")
    if avg_retention < 0.35:
        tips.append("Retention below 35% — try shorter hooks (2s max) and cut body length.")
    elif avg_retention >= 0.50:
        tips.append("Retention above 50% is excellent — double down on this script style!")
    if avg_ctr < 0.04:
        tips.append("CTR below 4% — A/B test thumbnail styles using /api/ab/variants.")
    elif avg_ctr >= 0.08:
        tips.append("CTR above 8% is outstanding — your thumbnail formula is working, replicate it.")
    if not tips:
        tips.append("Metrics look healthy! Keep consistent posting cadence.")
    return tips
