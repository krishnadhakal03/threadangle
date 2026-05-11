# TODO: Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in backend/.env before testing Google OAuth
# Get credentials at: console.cloud.google.com
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
import httpx
import os

from database import get_db
from models import User
from auth import (
    BETA_WAITLIST_MESSAGE,
    beta_waitlist_mode_enabled,
    get_password_hash,
    user_has_beta_full_access,
    verify_password,
    create_access_token,
    get_current_user,
    require_full_access_user,
)
import secrets
from email_service import send_welcome_email, send_password_reset_email, send_beta_signup_notifications
from utils.site_settings import get_plan_limit

router = APIRouter()

class UserAuth(BaseModel):
    email: EmailStr
    password: str


def _auth_user_payload(user: User):
    beta_full_access = user_has_beta_full_access(user)
    return {
        "email": user.email,
        "name": user.name,
        "plan": user.plan,
        "usage_count": user.usage_count,
        "onboarding_completed": bool(user.onboarding_completed),
        "beta_full_access": beta_full_access,
        "beta_waitlist_mode": beta_waitlist_mode_enabled(),
        "beta_waitlist_message": None if beta_full_access else BETA_WAITLIST_MESSAGE,
    }


async def _send_signup_notifications_safely(user: User, signup_method: str):
    try:
        await send_beta_signup_notifications(
            user_email=user.email,
            signup_method=signup_method,
            name=user.name,
        )
    except Exception as exc:
        print(f"[beta-signup] notification failed for {user.email}: {type(exc).__name__}")


def _schedule_signup_notifications(user: User, signup_method: str):
    try:
        import asyncio
        asyncio.create_task(_send_signup_notifications_safely(user, signup_method))
    except Exception as exc:
        print(f"[beta-signup] notification scheduling failed: {type(exc).__name__}")

@router.post("/signup")
async def signup(user_data: UserAuth, db: AsyncSession = Depends(get_db)):
    # Check if user exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")
    
    if len(user_data.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    # Create user
    new_user = User(
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        plan="free",
        usage_count=0,
        usage_reset_date=datetime.utcnow() + timedelta(days=30)
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # Send welcome email (non-blocking)
    try:
        import asyncio
        asyncio.create_task(send_welcome_email(new_user.email))
    except Exception:
        pass
    _schedule_signup_notifications(new_user, "email/password")
    
    token = create_access_token(data={"sub": new_user.email})
    return {
        "token": token,
        "user": _auth_user_payload(new_user),
    }

@router.post("/google")
async def google_auth(token_data: dict = Body(...), db: AsyncSession = Depends(get_db)):
    """Authenticate with Google OAuth access token."""
    google_token = token_data.get("token")
    email = token_data.get("email")
    name = token_data.get("name", "")
    google_id = token_data.get("google_id")

    if not google_token or not email:
        raise HTTPException(status_code=400, detail="Missing token or email")

    # Verify token with Google and cross-check the email
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {google_token}"},
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=400, detail="Invalid Google token")
    google_user = resp.json()
    if google_user.get("email") != email:
        raise HTTPException(status_code=400, detail="Token email mismatch")

    # Find or create user
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    is_new_user = False

    if not user:
        user = User(
            email=email,
            password_hash=None,
            google_id=google_id,
            name=name,
            plan="free",
            usage_count=0,
            usage_reset_date=datetime.utcnow() + timedelta(days=30),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        is_new_user = True
        # Send welcome email (non-blocking)
        try:
            import asyncio
            asyncio.create_task(send_welcome_email(user.email))
        except Exception:
            pass
        _schedule_signup_notifications(user, "Google")
    else:
        if not user.google_id:
            user.google_id = google_id
            user.name = name
            await db.commit()

    token = create_access_token(data={"sub": user.email})
    return {
        "access_token": token,
        "token_type": "bearer",
        "is_new_user": is_new_user,
        "user": _auth_user_payload(user),
    }

@router.post("/login")
async def login(user_data: UserAuth, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user_data.email))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    token = create_access_token(data={"sub": user.email})
    return {
        "token": token,
        "user": _auth_user_payload(user),
    }

@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    plan = current_user.plan
    plan_limit = await get_plan_limit(db, plan)
    usage_limit = current_user.custom_limit if current_user.custom_limit is not None else plan_limit
    return {
        "email": current_user.email,
        "name": current_user.name,
        "plan": plan,
        "usage_count": current_user.usage_count,
        "usage_limit": usage_limit,
        "custom_limit": current_user.custom_limit,
        "resets_on": current_user.usage_reset_date,
        "onboarding_completed": bool(current_user.onboarding_completed),
        "google_user": current_user.password_hash is None,
        "voice_learned": bool(current_user.voice_learned),
        "successful_generations_count": current_user.successful_generations_count or 0,
        "voice_samples_submitted": bool(current_user.voice_samples_submitted),
        "niche_tags": current_user.niche_tags or None,
        "beta_full_access": user_has_beta_full_access(current_user),
        "beta_waitlist_mode": beta_waitlist_mode_enabled(),
        "beta_waitlist_message": None if user_has_beta_full_access(current_user) else BETA_WAITLIST_MESSAGE,
    }

class UpdateNameReq(BaseModel):
    name: str

@router.put("/update-name")
async def update_name(req: UpdateNameReq, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if not req.name or not req.name.strip():
        raise HTTPException(status_code=400, detail="Name cannot be empty")
    current_user.name = req.name.strip()
    await db.commit()
    return {"message": "Name updated", "name": current_user.name}

class ChangePasswordReq(BaseModel):
    current_password: str
    new_password: str

@router.put("/change-password")
async def change_password(req: ChangePasswordReq, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if current_user.password_hash is None:
        raise HTTPException(status_code=400, detail="Google accounts cannot change password here")
    if not verify_password(req.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if len(req.new_password) < 8:
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters")
    current_user.password_hash = get_password_hash(req.new_password)
    await db.commit()
    return {"message": "Password changed successfully"}

@router.delete("/delete-account")
async def delete_account(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await db.delete(current_user)
    await db.commit()
    return {"message": "Account deleted"}

@router.patch("/onboarding-complete")
async def onboarding_complete(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    current_user.onboarding_completed = 1
    await db.commit()
    return {"message": "Onboarding completed"}

class ForgotPasswordReq(BaseModel):
    email: EmailStr

@router.post("/forgot-password")
async def forgot_password(req: ForgotPasswordReq, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()
    
    if user:
        token = secrets.token_urlsafe(32)
        user.reset_token = token # In production we should hash this
        user.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
        await db.commit()
        
        # Send reset email (non-blocking)
        try:
            import asyncio
            asyncio.create_task(send_password_reset_email(user.email, token))
        except Exception:
            pass
            
    return {"message": "If this email exists you will receive a reset link shortly"}

@router.get("/verify-reset-token")
async def verify_reset_token(token: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.reset_token == token))
    user = result.scalar_one_or_none()
    
    if not user or not user.reset_token_expiry or user.reset_token_expiry < datetime.utcnow():
        return {"valid": False}
        
    return {"valid": True}

class ResetPasswordReq(BaseModel):
    token: str
    new_password: str

@router.post("/reset-password")
async def reset_password(req: ResetPasswordReq, db: AsyncSession = Depends(get_db)):
    if len(req.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
        
    result = await db.execute(select(User).where(User.reset_token == req.token))
    user = result.scalar_one_or_none()
    
    if not user or not user.reset_token_expiry or user.reset_token_expiry < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired token")
        
    user.password_hash = get_password_hash(req.new_password)
    user.reset_token = None
    user.reset_token_expiry = None
    await db.commit()
    
    return {"message": "Password reset successful"}


class SaveNicheReq(BaseModel):
    niche_tags: list[str]

@router.post("/save-niche")
async def save_niche(req: SaveNicheReq, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    import json
    # Sanitize: keep only non-empty strings, max 20 niches
    clean_tags = [str(t).strip() for t in req.niche_tags if t and str(t).strip()][:20]
    current_user.niche_tags = json.dumps(clean_tags)
    await db.commit()
    return {"message": "Niche preferences saved", "niche_tags": clean_tags}


class SaveVoiceSamplesReq(BaseModel):
    urls: list[str] = []
    sample_text: str = ""

@router.post("/save-voice-samples")
async def save_voice_samples(req: SaveVoiceSamplesReq, current_user: User = Depends(require_full_access_user), db: AsyncSession = Depends(get_db)):
    import asyncio
    from utils.voice_learning import analyze_user_voice_from_samples

    # Sanitize inputs
    clean_urls = [u.strip() for u in req.urls if u and u.strip().startswith("http")][:5]
    sample_text = str(req.sample_text or "").strip()[:5000]

    if not clean_urls and len(sample_text) < 50:
        raise HTTPException(status_code=400, detail="Please provide at least one URL or a text sample of 50+ characters.")

    # Mark samples as submitted immediately so UI updates
    current_user.voice_samples_submitted = True
    await db.commit()

    # Run analysis in background — don't block the response
    user_id = current_user.id
    async def run_analysis():
        from database import AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            from sqlalchemy import select as sa_select
            result = await session.execute(sa_select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if not user:
                return
            try:
                profile = await asyncio.get_event_loop().run_in_executor(
                    None, analyze_user_voice_from_samples, clean_urls, sample_text
                )
                if profile:
                    import json
                    user.voice_profile = json.dumps(profile)
                    user.voice_learned = True
                    user.voice_samples_submitted = True
                    await session.commit()
            except Exception as e:
                print(f"[voice-samples] Background analysis error: {e}")

    asyncio.create_task(run_analysis())

    return {"message": "Voice samples received. AI is analyzing your writing style in the background.", "processing": True}
