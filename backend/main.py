import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / ".env")

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from routes import auth, generate, payments, free, contact, admin, cms, blog
from routes.newsletter import router as newsletter_router
from routes.calendar import router as calendar_router
from routes.social_auth import router as social_auth_router
from routes.viral_video import router as viral_video_router
from routes.advanced_video import router as advanced_video_router
from routes.voice_gen import router as voice_gen_router
from routes.batch_generation import router as batch_router
from routes.analytics import router as analytics_router
from routes.ab_testing import router as ab_testing_router

import asyncio
from sqlalchemy import text

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="Threadangle API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── Startup env verification ───────────────────────────────────────────────
def verify_env_variables():
    required_vars = [
        'ANTHROPIC_API_KEY', 'STRIPE_SECRET_KEY', 'STRIPE_WEBHOOK_SECRET',
        'STRIPE_STARTER_PRICE_ID', 'STRIPE_PRO_PRICE_ID',
        'GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_SECRET', 'JWT_SECRET',
    ]
    smtp_user_present = bool(os.getenv("SMTP_USER") or os.getenv("ZOHO_EMAIL") or os.getenv("SMTP_FROM_EMAIL"))
    smtp_password_present = bool(os.getenv("SMTP_PASSWORD") or os.getenv("ZOHO_PASSWORD"))
    missing, present = [], []
    for var in required_vars:
        value = os.getenv(var)
        if not value or 'your-' in value.lower():
            missing.append(var)
        else:
            present.append(f"  [OK] {var} is set")
    if smtp_user_present:
        present.append("  [OK] SMTP user is set")
    else:
        missing.append("SMTP_USER or ZOHO_EMAIL")
    if smtp_password_present:
        present.append("  [OK] SMTP password is set")
    else:
        missing.append("SMTP_PASSWORD or ZOHO_PASSWORD")
    print("\n=== THREADANGLE ENV CHECK ===")
    for p in present:
        print(p)
    if missing:
        print(f"\n  [WARN] MISSING OR PLACEHOLDER VALUES:")
        for m in missing:
            print(f"  [!!] {m}")
    else:
        print("\n  [PASS] All environment variables present")
    print("==============================\n")

verify_env_variables()

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://localhost:5173",
        "http://localhost:5174",
        "https://localhost:5174",
        "http://localhost:5175",
        "http://localhost:3000",
        "https://kriangle.com",
        "https://www.kriangle.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routes
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(generate.router, prefix="/api/generate", tags=["Generation"])
app.include_router(payments.router, prefix="/api/payments", tags=["Payments"])
app.include_router(free.router, prefix="/api/free", tags=["Public SEO Tools"])
app.include_router(contact.router, prefix="/api/contact", tags=["Contact"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(cms.router, prefix="/api/cms", tags=["CMS"])
app.include_router(blog.router, prefix="/api/blog", tags=["Blog"])
app.include_router(newsletter_router, prefix="/api")
app.include_router(calendar_router, prefix="/api")
app.include_router(social_auth_router, prefix="", tags=["Social Auth"])
app.include_router(viral_video_router)
app.include_router(advanced_video_router)
app.include_router(voice_gen_router)
app.include_router(batch_router)
app.include_router(analytics_router)
app.include_router(ab_testing_router)

@app.get("/")
async def root():
    return {"message": "Threadangle API is running"}


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.on_event("startup")
async def run_migrations():
    """Add new columns to existing DB without dropping data."""
    async with engine.begin() as conn:
        for sql in [
            "ALTER TABLE generations ADD COLUMN status TEXT DEFAULT 'success'",
            "ALTER TABLE generations ADD COLUMN error_message TEXT",
            "ALTER TABLE generations ADD COLUMN video_run_id TEXT",
            "ALTER TABLE generations ADD COLUMN video_file TEXT",
            "ALTER TABLE generations ADD COLUMN video_duration_seconds INTEGER",
            "ALTER TABLE generations ADD COLUMN video_thumbnail TEXT",
            "ALTER TABLE generations ADD COLUMN video_scenes_json TEXT",
            "ALTER TABLE generations ADD COLUMN video_plan_json TEXT",
            "ALTER TABLE generations ADD COLUMN video_platform_meta_json TEXT",
            "ALTER TABLE generations ADD COLUMN seo_title TEXT",
            "ALTER TABLE generations ADD COLUMN seo_description TEXT",
            "ALTER TABLE generations ADD COLUMN seo_tags TEXT",
            "ALTER TABLE generations ADD COLUMN seo_hashtags TEXT",
            "ALTER TABLE generations ADD COLUMN thumbnail_text TEXT",
            "ALTER TABLE generations ADD COLUMN runway_credits_used REAL DEFAULT 0",
            "ALTER TABLE generations ADD COLUMN elevenlabs_credits_used INTEGER DEFAULT 0",
            "ALTER TABLE generations ADD COLUMN total_cost_usd REAL DEFAULT 0",
            "ALTER TABLE generations ADD COLUMN youtube_views INTEGER DEFAULT 0",
            "ALTER TABLE generations ADD COLUMN youtube_retention REAL DEFAULT 0",
            "ALTER TABLE generations ADD COLUMN youtube_ctr REAL DEFAULT 0",
            "ALTER TABLE generations ADD COLUMN batch_id TEXT",
            "ALTER TABLE generations ADD COLUMN topic TEXT",
        ]:
            try:
                await conn.execute(text(sql))
            except Exception:
                pass  # Column already exists

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # SQLite migration: add columns to existing tables if not present
    from sqlalchemy import text
    async with engine.begin() as conn:
        for column_def in ("google_id TEXT", "name TEXT"):
            try:
                await conn.execute(text(f"ALTER TABLE users ADD COLUMN {column_def}"))
            except Exception:
                pass  # Column already exists

    # Recovery: mark any orphaned 'processing' video rows as 'failed'.
    # These happen when the server restarts while a background generation task is running.
    from database import AsyncSessionLocal as _Session
    from models import Generation as _Gen
    from sqlalchemy import update as _update
    import logging as _logging
    _log = _logging.getLogger(__name__)
    async with _Session() as _sess:
        result = await _sess.execute(
            _update(_Gen)
            .where(_Gen.status == "processing")
            .values(status="failed", error_message="Orphaned: server restarted during generation. Please re-submit.")
            .returning(_Gen.id)
        )
        orphans = [row[0] for row in result.fetchall()]
        await _sess.commit()
    if orphans:
        _log.warning(f"[startup] Marked {len(orphans)} orphaned processing video(s) as failed: ids={orphans}")

    no_spend_flags = {
        "video_generation_dry_run": os.getenv("VIDEO_GENERATION_DRY_RUN", "1"),
        "server_rendering_enabled": os.getenv("ENABLE_SERVER_VIDEO_RENDERING", "0"),
        "hybrid_motion_renderer_enabled": os.getenv("ENABLE_HYBRID_MOTION_RENDERER", "0"),
        "runway_max_scenes": os.getenv("RUNWAYML_MAX_SCENES", "unset"),
        "free_paid_providers_enabled": os.getenv("FREE_VIDEO_ALLOW_PAID_PROVIDERS", "0"),
        "allow_paid_providers": os.getenv("ALLOW_PAID_PROVIDERS", "0"),
        "allow_runwayml": os.getenv("ALLOW_RUNWAYML", "0"),
        "allow_elevenlabs": os.getenv("ALLOW_ELEVENLABS", "0"),
        "allow_openai": os.getenv("ALLOW_OPENAI", "0"),
        "allow_anthropic": os.getenv("ALLOW_ANTHROPIC", "0"),
        "allow_gemini": os.getenv("ALLOW_GEMINI", "0"),
        "silent_fallback_enabled": os.getenv("VIDEO_ALLOW_SILENT_FALLBACK", "0"),
    }
    _log.warning("[startup.no_spend] %s", " ".join(f"{key}={value}" for key, value in no_spend_flags.items()))


# ── Development-only test endpoints ───────────────────────────────────────────
# Remove or gate these before going to production.

@app.get("/api/test/generate", tags=["Dev Tests"])
def test_generate():
    """Test endpoint — remove before production"""
    if os.getenv('ENVIRONMENT') == 'production':
        raise HTTPException(status_code=404)

    from utils.ai import generate_content
    try:
        result = generate_content(
            input_text="OpenAI released GPT-5 today. It scores 90% on bar exam, beats humans at coding, costs 50% less than GPT-4. Available to all users immediately. This changes everything for developers and businesses.",
            platforms=['twitter', 'linkedin', 'tiktok'],
            tone='bold'
        )
        return {
            "status": "success",
            "platforms_generated": list(result.keys()),
            "twitter_preview": result.get('twitter', '')[:300],
            "linkedin_preview": result.get('linkedin', '')[:300],
            "tiktok_preview": result.get('tiktok', '')[:300],
            "total_chars": sum(len(v) for v in result.values())
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}


async def test_email_endpoint():
    if os.getenv("ENVIRONMENT") == "production":
        raise HTTPException(status_code=404)
    from email_service import send_welcome_email
    try:
        result = await send_welcome_email("krishna.dhakal03@gmail.com")
        return {"status": "success" if result else "failed"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@app.get("/api/test/anthropic", tags=["Dev Tests"])
async def test_anthropic_endpoint():
    if os.getenv("ENVIRONMENT") == "production":
        raise HTTPException(status_code=404)
    try:
        from anthropic import AsyncAnthropic
        client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        msg = await client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=50,
            messages=[{"role": "user", "content": "Say 'Threadangle API working!' and nothing else."}],
        )
        return {"status": "success", "response": msg.content[0].text}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@app.get("/api/test/stripe", tags=["Dev Tests"])
async def test_stripe_endpoint():
    if os.getenv("ENVIRONMENT") == "production":
        raise HTTPException(status_code=404)
    try:
        import stripe
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
        products = stripe.Product.list(limit=3)
        return {"status": "success", "products": [p.name for p in products.data]}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

