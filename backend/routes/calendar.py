from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from database import get_db
from models import User, Generation
from auth import get_current_user
from datetime import datetime, date, time, timedelta
from typing import Optional
import json

router = APIRouter()


@router.get("/calendar/week")
async def get_calendar_week(
    start_date: Optional[str] = None,  # Format: YYYY-MM-DD
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get scheduled content for a specific week
    If no start_date provided, returns current week (Mon-Sun)
    """
    
    # Parse start date or use current Monday
    if start_date:
        try:
            week_start = datetime.strptime(start_date, "%Y-%m-%d").date()
        except:
            raise HTTPException(status_code=400, detail="Invalid date format")
    else:
        # Get current Monday
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
    
    # Calculate week end (Sunday)
    week_end = week_start + timedelta(days=6)
    
    print(f"📅 Getting calendar for week: {week_start} to {week_end}")
    
    # Get all scheduled items for this week
    result = await db.execute(
        select(Generation)
        .filter(
            and_(
                Generation.user_id == current_user.id,
                Generation.scheduled_date >= week_start,
                Generation.scheduled_date <= week_end
            )
        )
        .order_by(Generation.scheduled_date, Generation.scheduled_time)
    )
    scheduled_items = result.scalars().all()
    
    # Organize by date
    calendar = {}
    current_date = week_start
    
    while current_date <= week_end:
        date_str = current_date.strftime("%Y-%m-%d")
        
        day_items = []
        for item in scheduled_items:
            if item.scheduled_date == current_date:
                # Get content previews
                twitter_preview = None
                linkedin_preview = None
                tiktok_preview = None
                
                if item.twitter_content_edited:
                    twitter_preview = item.twitter_content_edited[:100]
                elif item.twitter_output:
                    content = item.twitter_output if isinstance(item.twitter_output, str) else json.dumps(item.twitter_output)
                    twitter_preview = content[:100]
                
                if item.linkedin_content_edited:
                    linkedin_preview = item.linkedin_content_edited[:100]
                elif item.linkedin_output:
                    content = item.linkedin_output if isinstance(item.linkedin_output, str) else json.dumps(item.linkedin_output)
                    linkedin_preview = content[:100]
                
                if item.tiktok_content_edited:
                    tiktok_preview = item.tiktok_content_edited[:100]
                elif item.tiktok_output:
                    content = item.tiktok_output if isinstance(item.tiktok_output, str) else json.dumps(item.tiktok_output)
                    tiktok_preview = content[:100]
                
                day_items.append({
                    "id": item.id,
                    "scheduled_date": item.scheduled_date.strftime("%Y-%m-%d"),
                    "scheduled_time": item.scheduled_time.strftime("%H:%M") if item.scheduled_time else None,
                    "posted": item.posted,
                    "posted_at": item.posted_at.isoformat() if item.posted_at else None,
                    "platforms": json.loads(item.scheduled_platforms) if item.scheduled_platforms else [],
                    "twitter_preview": twitter_preview,
                    "linkedin_preview": linkedin_preview,
                    "tiktok_preview": tiktok_preview,
                    "input_type": item.input_type,
                    "input_url": item.input_content if item.input_type == 'url' else None,
                })
        
        calendar[date_str] = day_items
        current_date += timedelta(days=1)
    
    return {
        "week_start": week_start.strftime("%Y-%m-%d"),
        "week_end": week_end.strftime("%Y-%m-%d"),
        "calendar": calendar,
        "total_scheduled": len(scheduled_items)
    }


@router.put("/generations/{generation_id}/schedule")
async def schedule_generation(
    generation_id: int,
    scheduled_date: str,  # YYYY-MM-DD
    scheduled_time: Optional[str] = "09:00",  # HH:MM
    platforms: Optional[list] = None,  # ["twitter", "linkedin"] or None for all
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Schedule a generation for posting on a specific date/time
    """
    
    # Get generation
    result = await db.execute(
        select(Generation).filter(
            and_(
                Generation.id == generation_id,
                Generation.user_id == current_user.id
            )
        )
    )
    generation = result.scalar_one_or_none()
    
    if not generation:
        raise HTTPException(status_code=404, detail="Generation not found")
    
    # Parse date
    try:
        schedule_date = datetime.strptime(scheduled_date, "%Y-%m-%d").date()
    except:
        raise HTTPException(status_code=400, detail="Invalid date format (use YYYY-MM-DD)")
    
    # Parse time
    try:
        schedule_time = datetime.strptime(scheduled_time, "%H:%M").time()
    except:
        raise HTTPException(status_code=400, detail="Invalid time format (use HH:MM)")
    
    # Update generation
    generation.scheduled_date = schedule_date
    generation.scheduled_time = schedule_time
    generation.scheduled_platforms = json.dumps(platforms if platforms else ["all"])
    
    await db.commit()
    
    print(f"✅ Scheduled generation {generation_id} for {schedule_date} at {schedule_time}")
    
    return {
        "success": True,
        "message": "Content scheduled",
        "scheduled_date": scheduled_date,
        "scheduled_time": scheduled_time
    }


@router.put("/generations/{generation_id}/mark-posted")
async def mark_as_posted(
    generation_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Mark a scheduled generation as posted
    """
    
    result = await db.execute(
        select(Generation).filter(
            and_(
                Generation.id == generation_id,
                Generation.user_id == current_user.id
            )
        )
    )
    generation = result.scalar_one_or_none()
    
    if not generation:
        raise HTTPException(status_code=404, detail="Generation not found")
    
    generation.posted = True
    generation.posted_at = datetime.utcnow()
    
    await db.commit()
    
    print(f"✅ Marked generation {generation_id} as posted")
    
    return {
        "success": True,
        "message": "Marked as posted",
        "posted_at": generation.posted_at.isoformat()
    }


@router.delete("/generations/{generation_id}/unschedule")
async def unschedule_generation(
    generation_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Remove scheduling from a generation
    """
    
    result = await db.execute(
        select(Generation).filter(
            and_(
                Generation.id == generation_id,
                Generation.user_id == current_user.id
            )
        )
    )
    generation = result.scalar_one_or_none()
    
    if not generation:
        raise HTTPException(status_code=404, detail="Generation not found")
    
    generation.scheduled_date = None
    generation.scheduled_time = None
    generation.scheduled_platforms = None
    generation.posted = False
    generation.posted_at = None
    
    await db.commit()
    
    print(f"✅ Unscheduled generation {generation_id}")
    
    return {
        "success": True,
        "message": "Unscheduled"
    }
