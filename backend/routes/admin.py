import os
from typing import Optional
from fastapi import APIRouter, Header, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from datetime import datetime, timedelta

from database import get_db
from models import User, Generation, Contact
from email_service import get_smtp_config, send_admin_test_email

router = APIRouter()

@router.get("/stats")
async def get_admin_stats(x_admin_password: str = Header(None), db: AsyncSession = Depends(get_db)):
    admin_password = os.getenv("ADMIN_PASSWORD")
    if not x_admin_password or x_admin_password != admin_password:
        raise HTTPException(status_code=401, detail="Invalid admin password")
    
    # Overview Stats
    total_users = (await db.execute(select(func.count(User.id)))).scalar()
    
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    users_today = (await db.execute(select(func.count(User.id)).where(User.created_at >= today))).scalar()
    
    total_generations = (await db.execute(select(func.count(Generation.id)))).scalar()
    generations_today = (await db.execute(select(func.count(Generation.id)).where(Generation.created_at >= today))).scalar()
    
    free_users = (await db.execute(select(func.count(User.id)).where(User.plan == "free"))).scalar()
    starter_users = (await db.execute(select(func.count(User.id)).where(User.plan == "starter"))).scalar()
    pro_users = (await db.execute(select(func.count(User.id)).where(User.plan == "pro"))).scalar()
    
    total_contacts = (await db.execute(select(func.count(Contact.id)))).scalar()
    contacts_today = (await db.execute(select(func.count(Contact.id)).where(Contact.created_at >= today))).scalar()
    
    # Recent items
    recent_users_res = await db.execute(select(User).order_by(User.created_at.desc()).limit(20))
    recent_users = [
        {"email": u.email, "plan": u.plan, "usage_count": u.usage_count, "created_at": u.created_at}
        for u in recent_users_res.scalars()
    ]
    
    # For generations, we need to join with User to get email
    recent_gens_res = await db.execute(
        select(Generation, User.email)
        .join(User, Generation.user_id == User.id)
        .order_by(Generation.created_at.desc())
        .limit(20)
    )
    recent_generations = [
        {"user_email": email, "platforms": f"{'Twitter ' if g.twitter_output else ''}{'LinkedIn ' if g.linkedin_output else ''}{'TikTok' if g.tiktok_output else ''}".strip(), 
         "input_type": g.input_type, "created_at": g.created_at}
        for g, email in recent_gens_res
    ]
    
    recent_contacts_res = await db.execute(select(Contact).order_by(Contact.created_at.desc()).limit(10))
    recent_contacts = [
        {"name": c.name, "email": c.email, "subject": c.subject, "created_at": c.created_at}
        for c in recent_contacts_res.scalars()
    ]
    
    return {
        "overview": {
            "total_users": total_users,
            "users_today": users_today,
            "total_generations": total_generations,
            "generations_today": generations_today,
            "free_plan_users": free_users,
            "starter_plan_users": starter_users,
            "pro_plan_users": pro_users,
            "total_contacts": total_contacts,
            "contacts_today": contacts_today
        },
        "recent_users": recent_users,
        "recent_generations": recent_generations,
        "recent_contacts": recent_contacts
    }


def _check_admin(x_admin_password: str):
    admin_password = os.getenv("ADMIN_PASSWORD")
    if not x_admin_password or x_admin_password != admin_password:
        raise HTTPException(status_code=401, detail="Invalid admin password")


# ─── User Management ──────────────────────────────────────────────────────────

@router.get("/users")
async def get_all_users(
    x_admin_password: str = Header(None),
    db: AsyncSession = Depends(get_db),
    search: str = "",
    limit: int = 100,
    offset: int = 0,
):
    _check_admin(x_admin_password)

    query = select(User)
    if search:
        query = query.where(User.email.ilike(f"%{search}%"))

    count_q = select(func.count(User.id))
    if search:
        count_q = count_q.where(User.email.ilike(f"%{search}%"))
    total = (await db.execute(count_q)).scalar()

    result = await db.execute(query.order_by(User.created_at.desc()).limit(limit).offset(offset))
    users = result.scalars().all()

    plan_defaults = {"free": 5, "solo": 30, "starter": 30, "founder": 100, "pro": 100}

    return {
        "total": total,
        "users": [
            {
                "id": u.id,
                "email": u.email,
                "name": u.name or "",
                "plan": u.plan,
                "usage_count": u.usage_count,
                "custom_limit": u.custom_limit,
                "plan_default_limit": plan_defaults.get(u.plan, 5),
                "usage_reset_date": u.usage_reset_date,
                "onboarding_completed": bool(u.onboarding_completed),
                "voice_learned": bool(u.voice_learned),
                "created_at": u.created_at,
                "stripe_customer_id": u.stripe_customer_id or "",
            }
            for u in users
        ],
    }


class UserUpdate(BaseModel):
    plan: Optional[str] = None
    usage_count: Optional[int] = None
    custom_limit: Optional[int] = None   # send -1 to clear (restore plan default)


class AdminTestEmailRequest(BaseModel):
    to_email: Optional[str] = None


@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    update_data: UserUpdate,
    x_admin_password: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    _check_admin(x_admin_password)

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if update_data.plan is not None:
        valid_plans = {"free", "solo", "starter", "founder", "pro"}
        if update_data.plan not in valid_plans:
            raise HTTPException(status_code=400, detail=f"Invalid plan. Must be one of: {', '.join(valid_plans)}")
        user.plan = update_data.plan

    if update_data.usage_count is not None:
        user.usage_count = max(0, update_data.usage_count)

    if update_data.custom_limit is not None:
        user.custom_limit = None if update_data.custom_limit < 0 else update_data.custom_limit

    await db.commit()
    return {"message": "User updated successfully"}


@router.post("/users/{user_id}/reset-usage")
async def reset_user_usage(
    user_id: int,
    x_admin_password: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    _check_admin(x_admin_password)

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.usage_count = 0
    await db.commit()
    return {"message": "Usage reset to 0"}


@router.post("/email/test")
async def send_test_email(
    payload: AdminTestEmailRequest,
    x_admin_password: str = Header(None),
):
    _check_admin(x_admin_password)

    target_email = payload.to_email or get_smtp_config()["username"]
    if not target_email:
        raise HTTPException(status_code=400, detail="No recipient email provided and SMTP user is not configured")

    ok = await send_admin_test_email(target_email)
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to send test email. Check SMTP credentials and logs.")

    return {"message": f"Test email sent to {target_email}"}
