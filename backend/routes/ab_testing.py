"""
A/B Testing infrastructure — script-level only, zero Runway credits.

Generates 3 variant scripts with different hook styles.
User picks the best script, then manually generates videos via the
standard /api/generate endpoint. No auto-video generation here.

Endpoints:
  POST /api/ab/variants            — Generate 3 hook-style script variants
  GET  /api/ab/tests               — List user's A/B tests
  GET  /api/ab/tests/{test_id}     — Get test detail / variants
  POST /api/ab/tests/{test_id}/winner — Record winning variant
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth import require_full_access_user
from database import get_db
from models import ABTest, User
from utils.ai import generate_content  # existing Claude wrapper — text only

router = APIRouter(prefix="/api/ab", tags=["A/B Testing"])

_HOOK_STYLES: dict[str, str] = {
    "curiosity": (
        "Write a CURIOSITY hook — start with a mysterious question the viewer desperately "
        "wants answered (e.g. 'What if I told you...' / 'Nobody talks about this...'). "
        "Make the viewer feel they are missing a secret."
    ),
    "shocking_stat": (
        "Write a SHOCKING STATISTIC hook — open with a surprising, counterintuitive number "
        "or fact (e.g. '95% of creators fail because...' / 'In 30 days I went from 0 to...'). "
        "The stat must be startling enough to stop a scroll."
    ),
    "personal_story": (
        "Write a PERSONAL STORY hook — start with a relatable first-person mistake or "
        "transformation (e.g. 'I wasted 6 months until I discovered...' / 'The day I lost "
        "everything taught me...'). Create instant emotional connection."
    ),
}

_SCRIPT_SYSTEM_PROMPT = """You are an expert YouTube Shorts scriptwriter.
Write a {duration}-second {niche} script for the topic: "{topic}".

Hook style instruction: {hook_instruction}

Requirements:
- Hook: First 3 seconds MUST use the specified style above
- Body: 3 punchy, value-packed points (no filler words)
- CTA: Last 3 seconds — one call-to-action
- Length: exactly {word_count} words (for {duration}s at 2.5 words/sec)
- Format:
  [HOOK]
  <hook text>
  [BODY]
  <3 numbered points>
  [CTA]
  <call to action>

Tone: confident, fast-paced, no fluff."""


class GenerateVariantsRequest(BaseModel):
    topic: str = Field(..., min_length=3, max_length=200)
    niche: str = Field(default="AI & Productivity")
    duration_seconds: int = Field(default=60, ge=30, le=90)


class RecordWinnerRequest(BaseModel):
    winner_variant: Literal["curiosity", "shocking_stat", "personal_story"]
    reason: str = Field(default="", max_length=500)


@router.post("/variants")
async def generate_variants(
    req: GenerateVariantsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_full_access_user),
):
    """
    Generate 3 script variants with different hook styles for A/B testing.
    Uses Claude text API only — zero Runway/ElevenLabs credits consumed.
    """
    word_count = int(req.duration_seconds * 2.5)
    variants: dict[str, str] = {}

    for style, hook_instruction in _HOOK_STYLES.items():
        prompt = _SCRIPT_SYSTEM_PROMPT.format(
            duration=req.duration_seconds,
            niche=req.niche,
            topic=req.topic,
            hook_instruction=hook_instruction,
            word_count=word_count,
        )
        try:
            result = generate_content(
                input_text=prompt,
                platforms=["tiktok"],  # reuse existing generate_content wrapper
                tone="bold",
            )
            # generate_content returns {platform: text} — grab tiktok key
            script_text = result.get("tiktok") or result.get(next(iter(result), ""), "")
            variants[style] = script_text.strip()
        except Exception as exc:
            variants[style] = f"[Generation failed: {exc}]"

    # Persist to db
    test = ABTest(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        topic=req.topic,
        niche=req.niche,
        variants_json=json.dumps(variants),
        created_at=datetime.utcnow(),
    )
    db.add(test)
    await db.commit()
    await db.refresh(test)

    return {
        "test_id": test.id,
        "topic": req.topic,
        "niche": req.niche,
        "duration_seconds": req.duration_seconds,
        "variants": variants,
        "next_steps": (
            "Pick the best script above, then generate your video via "
            "POST /api/generate/video using the script text. "
            "Record the winner via POST /api/ab/tests/{test_id}/winner."
        ),
    }


@router.get("/tests")
async def list_ab_tests(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_full_access_user),
):
    """List user's A/B tests, most recent first."""
    result = await db.execute(
        select(ABTest)
        .where(ABTest.user_id == current_user.id)
        .order_by(ABTest.created_at.desc())
        .limit(min(limit, 100))
    )
    tests = result.scalars().all()

    return {
        "tests": [
            {
                "test_id": t.id,
                "topic": t.topic,
                "niche": t.niche,
                "winner_variant": t.winner_variant_id,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in tests
        ]
    }


@router.get("/tests/{test_id}")
async def get_ab_test(
    test_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_full_access_user),
):
    """Return full detail including all variant scripts."""
    result = await db.execute(
        select(ABTest).where(
            ABTest.id == test_id,
            ABTest.user_id == current_user.id,
        )
    )
    test = result.scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=404, detail="A/B test not found")

    variants: dict = {}
    try:
        variants = json.loads(test.variants_json or "{}")
    except json.JSONDecodeError:
        pass

    return {
        "test_id": test.id,
        "topic": test.topic,
        "niche": test.niche,
        "winner_variant": test.winner_variant_id,
        "variants": variants,
        "created_at": test.created_at.isoformat() if test.created_at else None,
    }


@router.post("/tests/{test_id}/winner")
async def record_winner(
    test_id: str,
    req: RecordWinnerRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_full_access_user),
):
    """Record which hook style won the A/B test."""
    result = await db.execute(
        select(ABTest).where(
            ABTest.id == test_id,
            ABTest.user_id == current_user.id,
        )
    )
    test = result.scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=404, detail="A/B test not found")

    test.winner_variant_id = req.winner_variant
    await db.commit()

    return {
        "test_id": test_id,
        "winner": req.winner_variant,
        "message": (
            f"Winner recorded: '{req.winner_variant}'. Use this hook style for your "
            f"next '{test.topic}' video to maximize engagement."
        ),
    }
