import json
import logging
import os
import time as _time
import uuid
import io
import base64
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from urllib.parse import quote

import httpx

from fastapi import APIRouter, Depends, HTTPException, Body, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from database import get_db, AsyncSessionLocal
from models import User, Generation, HMRRenderJob
from utils.ai import extract_content_from_url, generate_content as ai_generate, build_prompt, parse_response, generate_video_plan, client as anthropic_client
from utils.youtube import is_youtube_url, get_youtube_transcript, get_video_metadata
from utils.voice_learning import analyze_user_voice, build_voice_prompt, should_trigger_voice_learning
from utils.hook_generator import generate_all_hook_variations
from utils.site_settings import get_plan_limit
from utils.character_manager import CharacterManager
from utils.hmr_artifact_manifest import assert_not_frozen_output
from utils.hmr_durable_jobs import create_hmr_render_job_record, hmr_job_to_progress, update_hmr_render_job_record
from utils.runwayml_client import RunwayMLClient
from utils.video_pipeline import (
    parse_script,
    parse_clip_to_clip_structure,
    scenes_from_rows,
    build_scene_plan,
    apply_stock_hook_framework_to_scene_rows,
    resolve_duration_seconds,
    fetch_scene_clips,
    assemble_video,
    make_scene_response,
    new_run_id,
    render_thumbnail,
)

# Import the TTS function directly
from routes.voice_gen import generate_voice, VoiceGenRequest
from utils.youtube_seo import generate_youtube_metadata
from auth import get_current_user

router = APIRouter()

logger = logging.getLogger(__name__)

# 5-minute cache for external API credit balance calls
_credits_cache: dict = {"data": None, "expires": 0.0}

# In-memory progress tracker: generation_id → {percent, message, step, updated_at}
# Populated by background tasks; cleared when generation reaches terminal state.
_task_progress: dict[int, dict] = {}


def is_video_dry_run_enabled() -> bool:
    return os.getenv("VIDEO_GENERATION_DRY_RUN", "1") == "1"


def is_audio_required_enabled() -> bool:
    # Safety default ON: prevent silent final videos unless explicitly disabled.
    return os.getenv("VIDEO_REQUIRE_AUDIO", "1") == "1"


def is_hybrid_motion_renderer_enabled() -> bool:
    return os.getenv("ENABLE_HYBRID_MOTION_RENDERER", "0") == "1"


def _is_valid_audio_file(path_value: Optional[str]) -> bool:
    if not path_value:
        return False
    try:
        p = Path(path_value)
        return p.exists() and p.is_file() and p.stat().st_size >= 1000
    except Exception:
        return False


def _log_scene_text_check(scene_idx: int, subtitle: str, on_screen_text: str, visual_description: str) -> None:
    sub_preview = str(subtitle or "")[:220].replace('"', '\\"')
    on_screen_preview = str(on_screen_text or "")[:220].replace('"', '\\"')
    vis_preview = str(visual_description or "")[:260].replace('"', '\\"')
    print(
        f"[SCENE_TEXT_CHECK] scene={scene_idx} "
        f"subtitle=\"{sub_preview}\" "
        f"on_screen_text=\"{on_screen_preview}\" "
        f"visual_description=\"{vis_preview}\""
    )


def _script_quality_issue(text: str) -> Optional[str]:
    script = (text or "").strip()
    words = re.findall(r"[A-Za-z0-9']+", script)
    char_count = len(script)
    word_count = len(words)

    min_chars = int(os.getenv("VIDEO_MIN_SCRIPT_CHARS", "80"))
    min_words = int(os.getenv("VIDEO_MIN_SCRIPT_WORDS", "12"))

    if char_count >= min_chars and word_count >= min_words:
        return None

    return (
        f"Script is too short for a quality voiceover ({word_count} words, {char_count} chars). "
        f"Please provide at least {min_words} words and {min_chars} characters."
    )


def _get_audio_duration_seconds(audio_path: Optional[str]) -> Optional[float]:
    if not _is_valid_audio_file(audio_path):
        return None
    try:
        from moviepy.editor import AudioFileClip
        clip = AudioFileClip(str(audio_path))
        duration = float(clip.duration or 0.0)
        clip.close()
        return duration if duration > 0 else None
    except Exception:
        return None


def _rebalance_scene_durations(original_durations: list[float], target_total: float) -> list[float]:
    if not original_durations:
        return []
    src_total = sum(max(0.5, float(d or 0.0)) for d in original_durations)
    if src_total <= 0:
        return original_durations

    # Keep adaptation bounded to avoid extreme pacing artifacts.
    ratio = max(0.7, min(1.35, float(target_total) / src_total))
    scaled = [max(2.0, float(d) * ratio) for d in original_durations]
    drift = target_total - sum(scaled)
    scaled[-1] = max(2.0, scaled[-1] + drift)
    return scaled


def _split_script_for_scenes(script_text: str, scene_count: int, durations: list[float]) -> list[str]:
    """
    Deterministic beat-aware segmentation for stock-mode captions.

    Goals:
    - One spoken idea per scene when possible
    - Never combine hook + step/payoff transition in one subtitle
    - Cap beat length (~12–16 words), split long beats at punctuation/comma/and/dash
    - Merge tiny beats (<4 words) into the next beat (unless a step/payoff marker)
    """
    raw = (script_text or "").strip()
    if scene_count <= 0:
        return []
    if not raw:
        return [""] * scene_count

    marker_pat = re.compile(
        r"\b(?:(?:STEP\s+(?:ONE|TWO|THREE))|(?:PAYOFF\s*[1-3]))\b\s*:?\s*",
        re.IGNORECASE,
    )

    def _is_marker_beat(t: str) -> bool:
        return bool(marker_pat.match((t or "").strip()))

    def _ensure_punct(t: str) -> str:
        t = (t or "").strip()
        if not t:
            return t
        if t[-1] not in ".!?":
            return t + "."
        return t

    beats = _segment_script_into_beats(raw)

    # 4) Choose hook/body/cta beats deterministically.
    if not beats:
        return [""] * scene_count

    # Identify the first marker beat boundary to prevent hook swallowing "Step one/Payoff 1".
    first_marker_idx = None
    for idx, b in enumerate(beats):
        if _is_marker_beat(b):
            first_marker_idx = idx
            break

    hook_beats = beats[:first_marker_idx] if first_marker_idx is not None else [beats[0]]
    body_beats = beats[first_marker_idx:] if first_marker_idx is not None else beats[1:]

    # Prefer a CTA beat from the tail.
    cta_beat = ""
    cta_tokens = {"follow", "subscribe", "download", "cta"}
    for j in range(len(body_beats) - 1, -1, -1):
        lower = body_beats[j].lower()
        if any(tok in lower for tok in cta_tokens):
            cta_beat = body_beats.pop(j)
            break
    if not cta_beat and body_beats:
        cta_beat = body_beats[-1]

    # If hook has multiple beats, keep the first as hook and push the rest into body (don’t overload hook).
    hook_primary = hook_beats[0] if hook_beats else ""
    hook_extras = hook_beats[1:] if len(hook_beats) > 1 else []
    if hook_extras:
        body_beats = hook_extras + body_beats

    print(
        "[SEGMENTATION] "
        f"total_beats={len(beats)} scene_count={scene_count} "
        f"hook_beats={len(hook_beats)} body_beats={len(body_beats)} cta_beat={'1' if bool(cta_beat) else '0'}"
    )

    # 5) Allocate beats to scenes (cap per-scene density; avoid empty scenes when possible).
    if scene_count == 1:
        return [_ensure_punct(hook_primary or " ".join(beats)).strip()]

    out: list[str] = [""] * scene_count
    out[0] = hook_primary

    # Reserve last scene for CTA if we have it; otherwise it will get whatever remains.
    body_scene_slots = max(0, scene_count - 2)
    last_idx = scene_count - 1

    # Fill body scenes sequentially.
    cursor = 0
    for sidx in range(1, 1 + body_scene_slots):
        if cursor >= len(body_beats):
            break
        out[sidx] = body_beats[cursor]
        cursor += 1

    # Remaining beats go to the last scene if CTA is absent; otherwise keep CTA there.
    out[last_idx] = cta_beat or (body_beats[cursor] if cursor < len(body_beats) else "")

    # If we still have leftover beats, we MUST merge (only when caller caps scene_count below total_beats).
    leftovers = body_beats[cursor + (1 if (not cta_beat and cursor < len(body_beats)) else 0):]
    if leftovers:
        target = last_idx if not body_scene_slots else (1 + body_scene_slots - 1)
        combined = (out[target] + " " + " ".join(leftovers)).strip()
        out[target] = combined

    # Final punctuation normalization.
    return [_ensure_punct(t).strip() if t else "" for t in out]


def _segment_script_into_beats(script_text: str) -> list[str]:
    """
    Deterministic beat segmentation with guardrails:
    - Beat length cap (~12–16 words) (default 14)
    - Split long beats at punctuation/comma/and/dash
    - Merge tiny beats (<4 words) forward (unless a marker beat)
    """
    raw = (script_text or "").strip()
    if not raw:
        return []

    MAX_BEAT_WORDS = 14
    MIN_BEAT_WORDS = 4

    marker_pat = re.compile(
        r"\b(?:(?:STEP\s+(?:ONE|TWO|THREE))|(?:PAYOFF\s*[1-3]))\b\s*:?\s*",
        re.IGNORECASE,
    )

    def _word_count(t: str) -> int:
        return len([w for w in re.split(r"\s+", (t or "").strip()) if w])

    def _is_marker_beat(t: str) -> bool:
        return bool(marker_pat.match((t or "").strip()))

    def _ensure_punct(t: str) -> str:
        t = (t or "").strip()
        if not t:
            return t
        if t[-1] not in ".!?":
            return t + "."
        return t

    def _split_long_beat(t: str) -> list[str]:
        t = (t or "").strip()
        if not t:
            return []
        if _word_count(t) <= MAX_BEAT_WORDS:
            return [t]

        clauses = [c.strip() for c in re.split(r"\s*(?:,|;|—|–|-|\band\b)\s*", t, flags=re.IGNORECASE) if c.strip()]
        if len(clauses) > 1:
            out: list[str] = []
            cur = ""
            for c in clauses:
                candidate = (cur + " " + c).strip() if cur else c
                if not cur or _word_count(candidate) <= MAX_BEAT_WORDS:
                    cur = candidate
                else:
                    out.append(cur)
                    cur = c
            if cur:
                out.append(cur)
            if all(_word_count(o) <= MAX_BEAT_WORDS for o in out):
                return out

        words = [w for w in re.split(r"\s+", t) if w]
        return [" ".join(words[i:i + MAX_BEAT_WORDS]).strip() for i in range(0, len(words), MAX_BEAT_WORDS)]

    text = re.sub(r"\s+", " ", raw.replace("\r", " ").replace("\n", " ")).strip()
    markers = list(marker_pat.finditer(text))
    segments: list[str] = []
    if markers:
        pre = text[: markers[0].start()].strip()
        if pre:
            segments.append(pre)
        for i, m in enumerate(markers):
            start = m.start()
            end = markers[i + 1].start() if i + 1 < len(markers) else len(text)
            seg = text[start:end].strip()
            if seg:
                segments.append(seg)
    else:
        segments = [text]

    beats: list[str] = []
    for seg in segments:
        parts = [p.strip() for p in re.split(r"(?<=[.!?])\s+", seg) if p.strip()]
        if not parts:
            parts = [seg.strip()]
        for p in parts:
            beats.extend(_split_long_beat(p))

    beats = [_ensure_punct(b) for b in beats if (b or "").strip()]

    merged: list[str] = []
    i = 0
    while i < len(beats):
        cur = beats[i].strip()
        if cur and (not _is_marker_beat(cur)) and _word_count(cur) < MIN_BEAT_WORDS and (i + 1) < len(beats):
            nxt = beats[i + 1].strip()
            if nxt:
                cur = _ensure_punct((cur.rstrip(".!?") + " " + nxt).strip())
                i += 1
        merged.append(cur)
        i += 1

    return [b for b in merged if b]


class EditContentRequest(BaseModel):
    platform: str
    edited_content: str


class GenerateVideoRequest(BaseModel):
    script: str = ""
    full_script: Optional[str] = None
    hook: str | None = None
    body: str | None = None
    cta: str | None = None
    duration_seconds: int = 45
    confirmed_plan: dict | None = None
    scene_mode: str = "auto"
    niche: str | None = None
    runway_model: str = "gen4.5"  # Options: gen4.5, gen4_turbo, gen3a_turbo (cheaper)
    dry_run: Optional[bool] = None   # overrides VIDEO_GENERATION_DRY_RUN env when provided
    max_scenes: Optional[int] = None  # overrides RUNWAYML_MAX_SCENES env when provided
    # Voice options
    tts_provider: str = "elevenlabs"  # "elevenlabs" | "free"
    voice_id: str = "pNInz6obpgDQGcFmaJgB"  # ElevenLabs "Adam" voice ID; ignored when tts_provider="free"
    # Image options
    image_provider: str = "pollinations"  # "pollinations" (free) | "gemini" (paid, requires billing)
    hmr_async: bool = False  # Future worker-safe HMR path; current route behavior stays direct.


def build_hmr_ui_generation_smoke_plan(
    request: GenerateVideoRequest,
    *,
    generated_root: str | Path | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Validate HMR UI generation routing without invoking render work."""
    selected_mode = str(request.scene_mode or "").lower().strip()
    dry_run = request.dry_run if request.dry_run is not None else is_video_dry_run_enabled()
    output_root = Path(generated_root).expanduser().resolve() if generated_root else Path(__file__).resolve().parents[1] / "generated_videos"
    smoke_run_id = run_id or f"hmr_ui_smoke_{new_run_id()}"
    output_path = output_root / f"{smoke_run_id}.mp4"
    assert_not_frozen_output(output_path)
    from utils.first_three_seconds import build_first_3_seconds_plan
    from utils.hmr_render_jobs import create_hmr_render_job_state
    from utils.hmr_ui_productization import build_hmr_ui_productization_metadata
    from utils.pattern_interrupts import build_pattern_interrupt_plan

    selected_hook = request.hook or parse_script(request.full_script or request.script or "").hook
    first_3_seconds = build_first_3_seconds_plan(
        selected_hook=selected_hook or request.script,
        topic=request.niche or selected_hook,
    )
    pattern_interrupt_plan = build_pattern_interrupt_plan(
        [
            {
                "id": "hook",
                "template": "hook",
                "duration": 3.0,
                "caption_text": selected_hook or request.script,
            }
        ]
    )
    productization = build_hmr_ui_productization_metadata(
        generated_root=output_root,
        run_id=smoke_run_id,
        video_path=output_path,
    )
    hmr_mode_selected = selected_mode == "hybrid_motion"
    hmr_renderer_enabled = is_hybrid_motion_renderer_enabled()
    hmr_job = create_hmr_render_job_state(
        run_id=smoke_run_id,
        generation_id=None,
        artifact_paths=productization["artifact_paths"],
        active_worker=bool(request.hmr_async and hmr_mode_selected and hmr_renderer_enabled),
    )
    use_free_tts = hmr_mode_selected or str(getattr(request, "tts_provider", "elevenlabs")).lower() == "free"
    return {
        "route_entry_point": "/api/generate/video/free",
        "request_schema": "GenerateVideoRequest",
        "hmr_mode_selected": hmr_mode_selected,
        "hmr_renderer_enabled": hmr_renderer_enabled,
        "would_enter_hmr_render_branch": hmr_mode_selected and hmr_renderer_enabled,
        "dry_run": dry_run,
        "output_path": str(output_path),
        "output_folder": str(output_root),
        "frozen_guard_checked": True,
        "paid_providers_selected": {
            "elevenlabs": not (dry_run or use_free_tts),
            "runwayml": False if hmr_mode_selected else not dry_run and selected_mode in {"ai", "auto", "hybrid"},
            "paid_llm": False,
        },
        "free_tts_for_hmr": use_free_tts,
        "review_package_available_after_render": True,
        "platform_export_integration_ready": True,
        "productization": productization,
        "non_blocking_hmr_requested": bool(request.hmr_async),
        "non_blocking_hmr_active": bool(request.hmr_async and hmr_mode_selected and hmr_renderer_enabled),
        "async_execution_status": "background_task" if request.hmr_async and hmr_mode_selected and hmr_renderer_enabled else "direct_or_scaffold",
        "worker_active": bool(request.hmr_async and hmr_mode_selected and hmr_renderer_enabled),
        "durable_progress": bool(request.hmr_async and hmr_mode_selected and hmr_renderer_enabled),
        "progress_store": "hmr_render_jobs" if request.hmr_async and hmr_mode_selected and hmr_renderer_enabled else "_task_progress_in_memory_only",
        "truthfulness_note": "hmr_async queues a durable HMR background job when hybrid_motion mode and the HMR renderer are enabled.",
        "hmr_render_job": hmr_job.to_dict(),
        "first_3_seconds": first_3_seconds,
        "pattern_interrupt_plan": pattern_interrupt_plan,
        "render_invoked": False,
    }


class GenerateVideoPlanRequest(BaseModel):
    script: str = ""
    full_script: Optional[str] = None
    hook: str | None = None
    body: str | None = None
    cta: str | None = None
    duration_seconds: int = 45
    scene_mode: str = "auto"


class BatchVideoRequest(BaseModel):
    topics: list[str]
    duration: int = 45
    style: str = "auto"
    niche: str = "general"


@router.get("/video/mode")
async def get_video_mode(current_user: User = Depends(get_current_user)):
    dry_run = is_video_dry_run_enabled()
    return {
        "dry_run": dry_run,
        "mode_label": "Dry Run" if dry_run else "Live",
        "spend_protection": {
            "runway": dry_run,
            "elevenlabs": dry_run,
        },
    }


class VideoPreviewRequest(BaseModel):
    script: str
    full_script: Optional[str] = None
    hook: Optional[str] = None
    body: Optional[str] = None
    cta: Optional[str] = None
    duration: int = 45
    niche: str = "general"
    character_source: str = Field(default="generate", pattern="^(generate|upload|preset)$")
    preset_id: Optional[str] = None
    uploaded_image_base64: Optional[str] = None
    scene_mode: str = "auto"  # ai | hybrid | auto | stock — controls credit estimation in preview
    image_provider: str = "pollinations"  # "pollinations" (free) | "gemini" (paid)


class GenerateFromPreviewRequest(BaseModel):
    preview_id: str
    approved_scenes: list[dict[str, Any]]
    dry_run: bool = True  # SAFETY: default True — must be explicitly set False for live generation
    script: Optional[str] = None
    full_script: Optional[str] = None
    hook: Optional[str] = None
    body: Optional[str] = None
    cta: Optional[str] = None
    niche: str = "general"
    tts_provider: str = "free"  # "elevenlabs" | "free"
    voice_id: str = "pNInz6obpgDQGcFmaJgB"  # ElevenLabs "Adam"
    confirmed_plan: Optional[dict[str, Any]] = None


class RegenerateSceneImageRequest(BaseModel):
    scene_index: int
    scene_description: str
    character_profile: dict[str, Any] = {}
    image_provider: str = "pollinations"
    variation_token: Optional[str] = None


class RegenerateThumbnailRequest(BaseModel):
    video_id: int
    thumbnail_text: str


class SaveVideoEditorRequest(BaseModel):
    video_id: int
    captions: list[dict[str, Any]] = []
    caption_style: dict[str, Any] = {}
    thumbnail_text: Optional[str] = None
    seo: Optional[dict[str, Any]] = None
    platform_meta: Optional[dict[str, Any]] = None


@router.post("/")
async def run_generate(
    input_type: str = Body(..., embed=True),
    content: str = Body(..., embed=True),
    platforms: list = Body(..., embed=True),
    tone: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check Usage Limits (CMS-driven plan limits + per-user custom override)
    plan_limit = await get_plan_limit(db, current_user.plan)
    effective_limit = current_user.custom_limit if current_user.custom_limit is not None else plan_limit
    if effective_limit is not None and current_user.usage_count >= effective_limit:
        raise HTTPException(
            status_code=429,
            detail={
                "message": "Generation limit reached",
                "plan": current_user.plan,
                "limit": effective_limit,
                "used": current_user.usage_count,
                "upgrade_required": current_user.custom_limit is None and current_user.plan == "free",
            }
        )

    # Content Extraction — raises Exception with user-friendly message on failure
    extracted_text = content
    source_is_youtube = False
    video_metadata = None
    if input_type == "url":
        if not content.startswith("http"):
            raise HTTPException(status_code=400, detail="Please enter a valid URL starting with http:// or https://")

        if is_youtube_url(content):
            # YouTube: extract transcript + metadata
            transcript, yt_error = get_youtube_transcript(content, max_words=4000)
            if yt_error:
                # Save failed record (no credit deducted) then return error
                failed_gen = Generation(
                    user_id=current_user.id,
                    input_type="url",
                    input_content=content,
                    status="failed",
                    error_message=yt_error[:500],
                )
                db.add(failed_gen)
                await db.commit()
                raise HTTPException(status_code=400, detail=f"YouTube transcript error: {yt_error}")
            extracted_text = transcript
            source_is_youtube = True
            video_metadata = await get_video_metadata(content)
        else:
            # Regular URL: scrape article text
            try:
                extracted_text = await extract_content_from_url(content)
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
    else:
        if len(content.strip()) < 50:
            raise HTTPException(status_code=400, detail="Please enter at least 50 characters of text to generate from.")

    # AI Generation wrapped in try/except
    # Inject user's learned voice profile if available
    voice_prefix = ""
    if current_user.voice_learned and current_user.voice_profile:
        try:
            voice_profile = json.loads(current_user.voice_profile)
            voice_prefix = build_voice_prompt(voice_profile)
            print("🎤 Using learned voice profile")
        except Exception:
            print("⚠️ Failed to load voice profile — using default")

    # Inject niche context if available
    niche_context = ""
    if current_user.niche_tags:
        try:
            niche_list = json.loads(current_user.niche_tags)
            if niche_list:
                formatted = ", ".join(niche_list)
                niche_context = f"\n\nAUDIENCE CONTEXT:\nThis content targets the following niches: {formatted}.\nTailor vocabulary, references, examples, and pain points to resonate with this specific audience."
                print(f"🎯 Applying niche context: {formatted}")
        except Exception:
            pass

    # Map simplified platform names to their field names
    # Frontend sends 'reels' and 'shorts', expand to full field names
    REELS_FIELDS = ['reels_title', 'reels_description', 'reels_hashtags']
    SHORTS_FIELDS = ['shorts_title', 'shorts_description', 'shorts_tags']
    
    expanded_platforms = []
    for p in platforms:
        if p == 'reels':
            expanded_platforms.extend(REELS_FIELDS)
        elif p == 'shorts':
            expanded_platforms.extend(SHORTS_FIELDS)
        else:
            expanded_platforms.append(p)
    
    # Always generate Reels + Shorts metadata if not already included
    for field in REELS_FIELDS:
        if field not in expanded_platforms:
            expanded_platforms.append(field)
    for field in SHORTS_FIELDS:
        if field not in expanded_platforms:
            expanded_platforms.append(field)
    
    extended_platforms = expanded_platforms


    try:
        ai_output = ai_generate(extracted_text, extended_platforms, tone, is_youtube=source_is_youtube, voice_prefix=voice_prefix, niche_context=niche_context)
        if source_is_youtube:
            print("[Generate] Using video-enhanced prompt")
        if not ai_output:
            raise Exception("AI returned an empty response")

        # Extract Reels + Shorts metadata
        reels_title = ai_output.get("reels_title") or ""
        reels_description = ai_output.get("reels_description") or ""
        reels_hashtags = ai_output.get("reels_hashtags") or ""
        shorts_title = ai_output.get("shorts_title") or ""
        shorts_description = ai_output.get("shorts_description") or ""
        shorts_tags = ai_output.get("shorts_tags") or ""

        # --- PATCH: Generate TTS audio for the script ---
        script_text = ai_output.get("final_script") or ai_output.get("script") or extracted_text
        # Shadow video pipeline in /generate always uses stock + no TTS to prevent
        # credit leakage on every content generation. Use /video/free for full production video.
        dry_run = True
        audio_file_path = None
        print("[/generate] Shadow video pipeline: stock-only, no TTS (use /video/free for AI video).")

        # --- PATCH: Build video plan and assemble video with audio ---
        parts = parse_script(script_text)
        duration = resolve_duration_seconds(parts)
        scene_plan = build_scene_plan(parts, duration)
        run_id = new_run_id()
        fetch_mode = "stock" if dry_run else None
        scenes = await fetch_scene_clips(scene_plan, run_id, mode=fetch_mode)
        video_result = assemble_video(scenes, run_id, audio_path=audio_file_path)

        print(f"[VIDEO] Video generated: {video_result['video_path']}")
        if video_result.get('thumbnail_path'):
            print(f"[THUMBNAIL] Thumbnail generated: {video_result['thumbnail_path']}")

        # Success path — save record and charge credit
        new_gen = Generation(
            user_id=current_user.id,
            input_type=input_type,
            input_content=content,
            twitter_output=ai_output.get("twitter"),
            linkedin_output=ai_output.get("linkedin"),
            tiktok_output=ai_output.get("tiktok"),
            reels_title=reels_title or None,
            reels_description=reels_description or None,
            reels_hashtags=reels_hashtags or None,
            shorts_title=shorts_title or None,
            shorts_description=shorts_description or None,
            shorts_tags=shorts_tags or None,
            status="success",
            video_file=video_result["video_path"],
            video_duration_seconds=duration,
            video_thumbnail=video_result.get("thumbnail_path"),
        )
        current_user.usage_count += 1
        current_user.successful_generations_count = (current_user.successful_generations_count or 0) + 1
        db.add(new_gen)
        await db.commit()
        await db.refresh(new_gen)  # populate new_gen.id

        print(f"   User generation count: {current_user.successful_generations_count}")

        # Clean platforms for hook variations (remove field names, keep primary platforms)
        primary_platforms = [p for p in platforms if p not in ['reels', 'shorts']]

        # Hook variations — single extra Claude call for 5 alternatives per platform
        hook_variations_data = None
        try:
            hook_variations_data = generate_all_hook_variations(
                ai_output=ai_output,
                platforms=primary_platforms,
                reels_title=reels_title or None,
                reels_description=reels_description or None,
                shorts_title=shorts_title or None,
                shorts_description=shorts_description or None,
            )
            if hook_variations_data:
                new_gen.hook_variations = json.dumps(hook_variations_data)
                new_gen.hook_variations_generated = True
                await db.commit()
                print(f"✅ Hook variations saved for {list(hook_variations_data.keys())}")
        except Exception as hook_exc:
            print(f"⚠️ Hook generation failed (non-fatal): {hook_exc}")

        # Voice learning trigger — fires once, after the 3rd successful generation
        voice_just_learned = False
        if should_trigger_voice_learning(current_user):
            print("\n🎓 TRIGGERING VOICE LEARNING...")
            print("=" * 60)

            past_result = await db.execute(
                select(Generation)
                .where(
                    and_(
                        Generation.user_id == current_user.id,
                        Generation.status == "success",
                    )
                )
                .order_by(Generation.created_at.desc())
                .limit(5)
            )
            past_generations = past_result.scalars().all()

            if len(past_generations) >= 3:
                learned_profile = analyze_user_voice(past_generations)
                if learned_profile:
                    current_user.voice_profile = json.dumps(learned_profile)
                    current_user.voice_learned = True
                    current_user.voice_learned_at = datetime.utcnow()
                    await db.commit()
                    voice_just_learned = True
                    print("✅ Voice profile saved to database")
                    print("=" * 60 + "\n")

                    # Non-blocking email notification
                    try:
                        import asyncio
                        from email_service import send_voice_learned_email
                        asyncio.create_task(
                            send_voice_learned_email(current_user.email, current_user.name)
                        )
                    except Exception as email_err:
                        print(f"⚠️ Voice email failed: {email_err}")
                else:
                    print("❌ Voice analysis returned no profile")
                    print("=" * 60 + "\n")
            else:
                print(f"❌ Not enough successful generations ({len(past_generations)}/3)")
                print("=" * 60 + "\n")

        return {
            "success": True,
            "data": {p: ai_output.get(p) for p in ['twitter', 'linkedin', 'tiktok']},
            "reels_title": reels_title,
            "reels_description": reels_description,
            "reels_hashtags": reels_hashtags,
            "shorts_title": shorts_title,
            "shorts_description": shorts_description,
            "shorts_tags": shorts_tags,
            "hook_variations": hook_variations_data,
            "generation_id": new_gen.id,
            "video_metadata": video_metadata,
            "voice_just_learned": voice_just_learned,
            "usage": {
                "used": current_user.usage_count,
                "limit": 5 if current_user.plan == "free" else (30 if current_user.plan == "solo" else 100),
                "plan": current_user.plan,
            },
            "video_file": video_result["video_path"],
            "audio_file": audio_file_path,
        }

    except Exception as exc:
        # Failure path — save failed record, no credit deducted
        failed_gen = Generation(
            user_id=current_user.id,
            input_type=input_type,
            input_content=content,
            status="failed",
            error_message=str(exc)[:500],
        )
        db.add(failed_gen)
        await db.commit()

        return {
            "success": False,
            "error": "Generation failed. Please try again.",
            "credit_deducted": False,
        }

@router.put("/{generation_id}/edit")
async def update_edited_content(
    generation_id: int,
    req: EditContentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Save user's edited version of a generated content field."""
    PLATFORM_COLUMN_MAP = {
        "twitter": "twitter_content_edited",
        "linkedin": "linkedin_content_edited",
        "tiktok": "tiktok_content_edited",
        "reels_title": "reels_title_edited",
        "reels_description": "reels_description_edited",
        "reels_hashtags": "reels_hashtags_edited",
        "shorts_title": "shorts_title_edited",
        "shorts_description": "shorts_description_edited",
        "shorts_tags": "shorts_tags_edited",
    }
    if req.platform not in PLATFORM_COLUMN_MAP:
        raise HTTPException(status_code=400, detail="Invalid platform")

    result = await db.execute(
        select(Generation).where(
            and_(
                Generation.id == generation_id,
                Generation.user_id == current_user.id,
            )
        )
    )
    gen = result.scalar_one_or_none()
    if not gen:
        raise HTTPException(status_code=404, detail="Generation not found")

    setattr(gen, PLATFORM_COLUMN_MAP[req.platform], req.edited_content)
    gen.has_edits = True
    gen.last_edited_at = datetime.utcnow()
    await db.commit()

    print(f"✅ Saved {req.platform} edit for generation {generation_id}")
    return {"success": True, "platform": req.platform}


@router.get("/history")
async def get_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Generation)
        .where(Generation.user_id == current_user.id)
        .order_by(Generation.created_at.desc())
        .limit(50)
    )
    generations = result.scalars().all()
    return [
        {
            "id": g.id,
            "input_type": g.input_type,
            "input_content": g.input_content,
            "twitter_output": g.twitter_output,
            "linkedin_output": g.linkedin_output,
            "tiktok_output": g.tiktok_output,
            "twitter_content_edited": g.twitter_content_edited,
            "linkedin_content_edited": g.linkedin_content_edited,
            "tiktok_content_edited": g.tiktok_content_edited,
            "has_edits": bool(g.has_edits),
            "reels_title": g.reels_title,
            "reels_description": g.reels_description,
            "reels_hashtags": g.reels_hashtags,
            "reels_title_edited": g.reels_title_edited,
            "reels_description_edited": g.reels_description_edited,
            "reels_hashtags_edited": g.reels_hashtags_edited,
            "shorts_title": g.shorts_title,
            "shorts_description": g.shorts_description,
            "shorts_tags": g.shorts_tags,
            "shorts_title_edited": g.shorts_title_edited,
            "shorts_description_edited": g.shorts_description_edited,
            "shorts_tags_edited": g.shorts_tags_edited,
            "status": g.status or "success",
            "error_message": g.error_message,
            "created_at": g.created_at.isoformat() if g.created_at else None,
        }
        for g in generations
    ]


class ScheduleAutoPostRequest(BaseModel):
    platforms: list
    schedule_time: str
    enabled: bool


@router.post("/{generation_id}/schedule-auto-post")
async def schedule_auto_post(
    generation_id: int,
    request: ScheduleAutoPostRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Schedule automatic posting to social media platforms
    
    Args:
        generation_id: ID of the generation to auto-post
        request: ScheduleAutoPostRequest with platforms, schedule_time, enabled
    """
    
    # Get the generation
    result = await db.execute(
        select(Generation).where(
            and_(
                Generation.id == generation_id,
                Generation.user_id == current_user.id
            )
        )
    )
    generation = result.scalar_one_or_none()
    
    if not generation:
        raise HTTPException(status_code=404, detail="Generation not found")
    
    # Parse schedule time
    try:
        schedule_time_dt = datetime.fromisoformat(request.schedule_time.replace('Z', '+00:00'))
    except:
        raise HTTPException(status_code=400, detail="Invalid schedule time format")
    
    # Update generation with auto-posting config
    generation.auto_post_enabled = request.enabled
    generation.auto_post_platforms = json.dumps(request.platforms)
    generation.auto_post_time = schedule_time_dt
    generation.auto_posted = False
    generation.auto_posted_at = None
    generation.auto_post_results = None
    
    await db.commit()
    
    return {
        "success": True,
        "message": f"Auto-post scheduled for {schedule_time_dt.isoformat()}",
        "platforms": request.platforms
    }


async def _run_hmr_render_job_background(job_id: str) -> None:
    """Durable HMR background worker entry point; owns its own DB session."""
    async with AsyncSessionLocal() as session:
        job = await session.get(HMRRenderJob, job_id)
        if job is None:
            return
        generation = await session.get(Generation, job.generation_id)
        await update_hmr_render_job_record(
            session,
            job_id,
            status="processing",
            percent=15,
            step="rendering",
            message="HMR background render started.",
            render_invoked=True,
        )
        if generation is not None:
            generation.status = "processing"
        await session.commit()
        payload = dict(job.request_json or {})
        try:
            from utils.first_three_seconds import attach_first_3_seconds_to_report, build_first_3_seconds_plan
            from utils.hybrid_motion_renderer import render_hybrid_video
            from utils.hmr_ui_productization import materialize_hmr_ui_review_workflow
            from utils.pattern_interrupts import attach_pattern_interrupts_to_report, build_pattern_interrupt_plan

            generated_root = Path(payload["generated_root"])
            run_id = str(payload["run_id"])
            script_text = str(payload["script_text"])
            scenes = list(payload["scenes"])
            output_path = Path(payload["output_path"])
            first_3_seconds_plan = build_first_3_seconds_plan(
                selected_hook=str(payload.get("hook") or script_text),
                topic=payload.get("niche"),
            )
            pattern_interrupt_plan = build_pattern_interrupt_plan(scenes)
            hybrid_result = render_hybrid_video(
                scenes=scenes,
                script_text=script_text,
                output_path=output_path,
                audio_path=payload.get("audio_path"),
                fps=30,
                width=1080,
                height=1920,
                use_stock_backgrounds=False,
                use_free_tts=True,
                style_preset="documentary_money_short",
            )
            hybrid_result = attach_first_3_seconds_to_report(hybrid_result, first_3_seconds_plan)
            hybrid_result = attach_pattern_interrupts_to_report(hybrid_result, pattern_interrupt_plan)
            hybrid_result["first_3_seconds"] = first_3_seconds_plan
            productization = materialize_hmr_ui_review_workflow(
                generated_root=generated_root,
                run_id=run_id,
                video_path=hybrid_result["video_path"],
                render_result=hybrid_result,
                script_text=script_text,
                scenes=scenes,
            )
            result = {"hybrid_motion": hybrid_result, "hmr_productization": productization}
            generation = await session.get(Generation, job.generation_id)
            if generation is not None:
                generation.status = "success"
                generation.video_run_id = run_id
                generation.video_file = Path(hybrid_result["video_path"]).name
                generation.video_duration_seconds = int(float(hybrid_result.get("duration") or payload.get("duration_seconds") or 0))
                generation.video_scenes_json = json.dumps(scenes)
                generation.video_plan_json = json.dumps({"hmr_async": True})
            await update_hmr_render_job_record(
                session,
                job_id,
                status="success",
                percent=100,
                step="done",
                message="HMR background render complete.",
                result=result,
                render_invoked=True,
            )
            await session.commit()
        except Exception as exc:
            generation = await session.get(Generation, job.generation_id)
            if generation is not None:
                generation.status = "failed"
                generation.error_message = str(exc)[:500]
            await update_hmr_render_job_record(
                session,
                job_id,
                status="failed",
                percent=0,
                step="error",
                message="HMR background render failed.",
                error_message=str(exc)[:500],
                render_invoked=True,
            )
            await session.commit()


@router.post("/video/free")
async def generate_free_video(
    request: GenerateVideoRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    authoritative_script = (request.full_script or request.script or "").strip()
    if not authoritative_script and not (request.hook and request.body and request.cta):
        raise HTTPException(status_code=400, detail="Provide either full script or hook/body/cta.")

    parts = parse_script(
        full_script=authoritative_script,
        hook=request.hook,
        body=request.body,
        cta=request.cta,
    )
    confirmed_rows = []
    if request.confirmed_plan and isinstance(request.confirmed_plan, dict):
        maybe_rows = request.confirmed_plan.get("scenes")
        if isinstance(maybe_rows, list):
            confirmed_rows = maybe_rows

    timeline_scenes = scenes_from_rows(confirmed_rows) if confirmed_rows else parse_clip_to_clip_structure(authoritative_script)
    if timeline_scenes:
        duration_seconds = int(max(scene.end for scene in timeline_scenes))
    else:
        duration_seconds = resolve_duration_seconds(parts, request.duration_seconds)
    run_id = new_run_id()
    # Per-request dry_run overrides env; falls back to env flag
    dry_run = request.dry_run if request.dry_run is not None else is_video_dry_run_enabled()
    hybrid_motion_requested = (
        str(request.scene_mode or "").lower() == "hybrid_motion"
        and is_hybrid_motion_renderer_enabled()
    )

    platform_meta = None
    if request.confirmed_plan and isinstance(request.confirmed_plan, dict):
        platform_meta = request.confirmed_plan.get("platform_meta")



    # --- Generate TTS audio for the script (direct call, robust) ---
    # Batch 2A: FIX - Always use parsed parts to avoid [HOOK][BODY][CTA] markers in TTS
    from routes.voice_gen import generate_voice, VoiceGenRequest
    import os
    import time
    script_text = f"{parts.hook} {parts.body} {parts.cta}"
    audio_path = None
    use_free_tts = hybrid_motion_requested or (getattr(request, 'tts_provider', 'elevenlabs') == 'free')

    if hybrid_motion_requested and request.hmr_async:
        scenes = timeline_scenes or build_scene_plan(parts, duration_seconds=duration_seconds)
        scene_response = make_scene_response(scenes)
        generated_root = Path(__file__).resolve().parents[1] / "generated_videos"
        output_path = generated_root / f"{run_id}.mp4"
        from utils.hmr_ui_productization import build_hmr_ui_productization_metadata

        productization = build_hmr_ui_productization_metadata(
            generated_root=generated_root,
            run_id=run_id,
            video_path=output_path,
        )
        generation = Generation(
            user_id=current_user.id,
            input_type="video",
            input_content=(request.script or authoritative_script or "")[:5000],
            status="queued",
            video_run_id=run_id,
            video_duration_seconds=duration_seconds,
            video_scenes_json=json.dumps(scene_response),
            video_plan_json=json.dumps({"hmr_async": True, "scene_mode": "hybrid_motion"}),
            video_platform_meta_json=json.dumps(platform_meta) if platform_meta else None,
        )
        db.add(generation)
        await db.flush()
        job = await create_hmr_render_job_record(
            db,
            generation_id=generation.id,
            user_id=current_user.id,
            run_id=run_id,
            request_payload={
                "run_id": run_id,
                "script_text": script_text,
                "hook": parts.hook,
                "niche": request.niche,
                "duration_seconds": duration_seconds,
                "scenes": scene_response,
                "generated_root": str(generated_root),
                "output_path": str(output_path),
                "audio_path": None,
            },
            artifact_paths=productization["artifact_paths"],
        )
        await db.commit()
        background_tasks.add_task(_run_hmr_render_job_background, job.id)
        progress = hmr_job_to_progress(job)
        return {
            "success": True,
            "queued": True,
            "dry_run": dry_run,
            "generation_id": generation.id,
            "run_id": run_id,
            "hmr_async": True,
            "non_blocking_hmr_active": True,
            "async_execution_status": "background_task",
            "worker_active": True,
            "durable_progress": True,
            "progress_store": "hmr_render_jobs",
            "hmr_render_job": progress["hmr_render_job"],
            "progress": progress,
            "render_invoked": False,
        }

    if not dry_run:
        quality_issue = _script_quality_issue(script_text)
        if quality_issue:
            raise HTTPException(status_code=400, detail=quality_issue)

    if dry_run:
        print("[DRY-RUN] Skipping ElevenLabs TTS in /video/free endpoint.")
    else:
        tts_req = VoiceGenRequest(
            text=script_text,
            voice_id=getattr(request, 'voice_id', 'pNInz6obpgDQGcFmaJgB'),
            force_free=use_free_tts,
        )
        try:
            tts_result = generate_voice(tts_req)
            audio_path = tts_result.audio_file
            print(f"[TTS] Audio file generated: {audio_path}")
        except Exception as e:
            print(f"[TTS] Voice generation failed: {e}")
            audio_path = None

    # --- Ensure audio file exists and is valid ---
    if not dry_run and not _is_valid_audio_file(audio_path):
        print(f"[TTS] Audio file missing/invalid: {audio_path}")
        audio_path = None

    if not dry_run and is_audio_required_enabled() and not audio_path and not hybrid_motion_requested:
        raise HTTPException(
            status_code=400,
            detail=(
                "Voice generation failed, so rendering was stopped to avoid silent output and unnecessary cost. "
                "Please retry with Free TTS or check ElevenLabs setup."
            ),
        )


    try:
        scenes = timeline_scenes or build_scene_plan(parts, duration_seconds=duration_seconds)
        for scene in scenes:
            _log_scene_text_check(
                scene_idx=getattr(scene, "idx", 0),
                subtitle=getattr(scene, "subtitle", "") or getattr(scene, "source_text", ""),
                on_screen_text=getattr(scene, "on_screen_text", "") or getattr(scene, "subtitle", ""),
                visual_description=getattr(scene, "visual_description", ""),
            )
        if hybrid_motion_requested:
            from utils.first_three_seconds import attach_first_3_seconds_to_report, build_first_3_seconds_plan
            from utils.hybrid_motion_renderer import render_hybrid_video
            from utils.hmr_ui_productization import materialize_hmr_ui_review_workflow
            from utils.pattern_interrupts import attach_pattern_interrupts_to_report, build_pattern_interrupt_plan

            generated_root = Path(__file__).resolve().parents[1] / "generated_videos"
            hybrid_output_path = generated_root / f"{run_id}.mp4"
            first_3_seconds_plan = build_first_3_seconds_plan(
                selected_hook=parts.hook or script_text,
                topic=request.niche,
            )
            scene_response = make_scene_response(scenes)
            pattern_interrupt_plan = build_pattern_interrupt_plan(scene_response)
            hybrid_result = render_hybrid_video(
                scenes=scene_response,
                script_text=script_text,
                output_path=hybrid_output_path,
                audio_path=audio_path,
                fps=30,
                width=1080,
                height=1920,
                use_stock_backgrounds=True,
                use_free_tts=True,
                style_preset="documentary_money_short",
            )
            hybrid_result = attach_first_3_seconds_to_report(hybrid_result, first_3_seconds_plan)
            hybrid_result = attach_pattern_interrupts_to_report(hybrid_result, pattern_interrupt_plan)
            hybrid_result["first_3_seconds"] = first_3_seconds_plan
            hmr_productization = materialize_hmr_ui_review_workflow(
                generated_root=generated_root,
                run_id=run_id,
                video_path=hybrid_result["video_path"],
                render_result=hybrid_result,
                script_text=script_text,
                scenes=make_scene_response(scenes),
            )
            render_result = {
                "video_path": hybrid_result["video_path"],
                "subtitle_path": None,
                "thumbnail_path": None,
                "ffmpeg_error": None,
                "hybrid_motion": hybrid_result,
                "hmr_productization": hmr_productization,
            }
        else:
            # Accept scene_mode from request, fallback to env default
            scene_mode = "stock" if dry_run else (request.scene_mode or os.getenv('VIDEO_SCENE_MODE', 'auto'))
            available_credits = float(os.getenv("RUNWAYML_AVAILABLE_CREDITS", "750"))
            # Derive max_scenes from scene_mode if not explicitly set:
            # ai=all scenes, auto/hybrid=3, stock=0
            if request.max_scenes is not None:
                effective_max_scenes = request.max_scenes
            elif scene_mode == "ai":
                effective_max_scenes = len(scenes)  # unlimited - all scenes use Runway
            elif scene_mode in ("auto", "hybrid"):
                effective_max_scenes = 3
            else:
                effective_max_scenes = 0
            scenes = await fetch_scene_clips(
                scenes,
                run_id=run_id,
                mode=scene_mode,
                available_credits=available_credits,
                runway_model=request.runway_model,
                max_scenes=effective_max_scenes,
            )
            if not audio_path:
                print("[TTS] No valid audio file, video will be silent.")
            render_result = assemble_video(scenes, run_id=run_id, audio_path=audio_path)
    except RuntimeError as exc:
        print(f"[VIDEO] Runtime error: {exc}")
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        print(f"[VIDEO] Exception: {exc}")
        raise HTTPException(status_code=500, detail=f"Video generation failed: {str(exc)}")

    ffmpeg_warning = render_result.get("ffmpeg_error")
    filename = Path(render_result["video_path"]).name
    video_path = Path(render_result["video_path"])
    thumbnail_path = render_result.get("thumbnail_path")

    runway_credits_used = round(sum(float(getattr(s, "credits_cost", 0.0) or 0.0) for s in scenes), 2)
    if dry_run:
        runway_credits_used = 0.0
    elevenlabs_chars = 0 if (dry_run or use_free_tts) else len(script_text or "")
    runway_cost = runway_credits_used * 0.01
    elevenlabs_cost = (elevenlabs_chars / 1000.0) * 0.30
    total_cost = round(runway_cost + elevenlabs_cost, 4)

    seo_metadata = None
    try:
        seo_metadata = await generate_youtube_metadata(
            script=script_text,
            niche=request.niche or "general",
            duration=duration_seconds,
        )
    except Exception as seo_exc:
        print(f"[SEO] Metadata generation failed (non-fatal): {seo_exc}")
    
    # Rename video file with SEO title for easy social media posting
    if seo_metadata and isinstance(seo_metadata, dict) and seo_metadata.get("title"):
        seo_title = _strip_unwanted_year_tokens(seo_metadata.get("title", ""), script_text=script_text or "")
        seo_metadata["title"] = seo_title
        # Sanitize filename: keep alphanumeric, hyphens, underscores; replace spaces with hyphens
        safe_title = re.sub(r'[^a-zA-Z0-9\-_]', '', seo_title.replace(" ", "-").replace("_", "-"))[:50]
        safe_title = re.sub(r'-+', '-', safe_title).strip('-')
        if safe_title:
            new_filename = f"{safe_title}.mp4"
            new_video_path = video_path.parent / new_filename
            try:
                video_path.rename(new_video_path)
                filename = new_filename
                video_path = new_video_path
                print(f"[VIDEO] Renamed to: {filename}")
            except Exception as rename_exc:
                print(f"[VIDEO] Could not rename file (continuing with original): {rename_exc}")

    # Rename thumbnail to match video filename; re-render with bold title overlay
    if thumbnail_path and Path(thumbnail_path).exists():
        expected_thumb = str(video_path).replace(".mp4", ".jpg")
        if thumbnail_path != expected_thumb:
            try:
                Path(thumbnail_path).rename(expected_thumb)
                thumbnail_path = expected_thumb
            except Exception:
                pass  # retain original path if rename fails
        raw_thumb_text = (
            (seo_metadata or {}).get("thumbnail_text")
            or (seo_metadata or {}).get("title")
            or ""
        )
        raw_thumb_text = _strip_unwanted_year_tokens(raw_thumb_text, script_text=script_text or "")
        if isinstance(seo_metadata, dict) and (seo_metadata.get("thumbnail_text") or ""):
            seo_metadata["thumbnail_text"] = raw_thumb_text
        title_for_thumb = _prepare_thumbnail_text(raw_thumb_text, script_text=script_text)
        if title_for_thumb and Path(video_path).exists():
            try:
                thumbnail_path = render_thumbnail(str(video_path), title_for_thumb, thumbnail_path)
            except Exception as thumb_exc:
                print(f"[THUMBNAIL] Styled overlay failed (non-fatal): {thumb_exc}")

    stored_video_file, stored_thumb_file = _organize_run_assets(
        run_id=run_id,
        video_path=video_path,
        thumbnail_path=thumbnail_path,
        title=_strip_unwanted_year_tokens(
            (seo_metadata or {}).get("title") if isinstance(seo_metadata, dict) else None,
            script_text=script_text or "",
        ),
    )
    filename = stored_video_file
    thumbnail_path = stored_thumb_file

    generation = Generation(
        user_id=current_user.id,
        input_type="video",
        input_content=(request.script or "")[:5000],
        status="success",
        video_run_id=run_id,
        video_file=filename,
        video_duration_seconds=duration_seconds,
        video_thumbnail=thumbnail_path,
        video_scenes_json=json.dumps(make_scene_response(scenes)),
        video_plan_json=json.dumps(request.confirmed_plan) if request.confirmed_plan else None,
        video_platform_meta_json=json.dumps(platform_meta) if platform_meta else None,
        reels_title=(platform_meta or {}).get("reels", {}).get("title") if isinstance(platform_meta, dict) else None,
        reels_description=(platform_meta or {}).get("reels", {}).get("description") if isinstance(platform_meta, dict) else None,
        reels_hashtags=(platform_meta or {}).get("reels", {}).get("hashtags") if isinstance(platform_meta, dict) else None,
        shorts_title=(platform_meta or {}).get("youtube_shorts", {}).get("title") if isinstance(platform_meta, dict) else None,
        shorts_description=(platform_meta or {}).get("youtube_shorts", {}).get("description") if isinstance(platform_meta, dict) else None,
        shorts_tags=(platform_meta or {}).get("youtube_shorts", {}).get("hashtags") if isinstance(platform_meta, dict) else None,
        tiktok_output=(platform_meta or {}).get("tiktok") if isinstance(platform_meta, dict) else None,
        seo_title=(seo_metadata or {}).get("title") if isinstance(seo_metadata, dict) else None,
        seo_description=(seo_metadata or {}).get("description") if isinstance(seo_metadata, dict) else None,
        seo_tags=json.dumps((seo_metadata or {}).get("tags", [])) if isinstance(seo_metadata, dict) else None,
        seo_hashtags=json.dumps((seo_metadata or {}).get("hashtags", [])) if isinstance(seo_metadata, dict) else None,
        thumbnail_text=(seo_metadata or {}).get("thumbnail_text") if isinstance(seo_metadata, dict) else None,
        runway_credits_used=runway_credits_used,
        elevenlabs_credits_used=elevenlabs_chars,
        total_cost_usd=total_cost,
    )
    db.add(generation)
    await db.commit()
    await db.refresh(generation)

    return {
        "success": True,
        "dry_run": dry_run,
        "generation_id": generation.id,
        "run_id": run_id,
        "duration_seconds": duration_seconds,
        "parts": {
            "hook": parts.hook,
            "body": parts.body,
            "cta": parts.cta,
        },
        "scenes": make_scene_response(scenes),
        "download_url": f"/api/generate/video/download/{quote(str(filename), safe='/')}",
        "preview_url": f"/api/generate/video/download/{quote(str(filename), safe='/')}",
        "platform_meta": platform_meta,
        "seo": seo_metadata,
        "thumbnail_path": thumbnail_path,
        "thumbnail_url": f"/api/generate/video/thumbnail/{quote(str(_relative_generated_asset_path(thumbnail_path) or ''), safe='/')}" if thumbnail_path else None,
        "costs": {
            "runway_credits_used": runway_credits_used,
            "runway_cost_usd": round(runway_cost, 4),
            "elevenlabs_chars_used": elevenlabs_chars,
            "elevenlabs_cost_usd": round(elevenlabs_cost, 4),
            "total_cost_usd": total_cost,
        },
        "scene_strategy": [
            {
                "scene": s.idx,
                "part": s.part,
                "use_runway": bool(getattr(s, "use_runway", False)),
                "credits_cost": float(getattr(s, "credits_cost", 0.0) or 0.0),
                "reason": getattr(s, "allocation_reason", ""),
            }
            for s in scenes
        ],
        "hybrid_motion": render_result.get("hybrid_motion") if hybrid_motion_requested else None,
        "hmr_productization": render_result.get("hmr_productization") if hybrid_motion_requested else None,
        "warning": "Rendered without burned subtitles because ffmpeg subtitle step failed."
        if ffmpeg_warning else None,
    }


@router.post("/video/plan")
async def plan_video_content(
    request: GenerateVideoPlanRequest,
    current_user: User = Depends(get_current_user),
):
    script_seed = (request.full_script or request.script or "").strip()
    if not script_seed and request.hook and request.body and request.cta:
        script_seed = f"[HOOK]\n{request.hook.strip()}\n\n[BODY]\n{request.body.strip()}\n\n[CTA]\n{request.cta.strip()}".strip()

    if len(script_seed) < 20:
        raise HTTPException(status_code=400, detail="Please provide a fuller script or hook/body/cta.")

    seed_parts = parse_script(
        full_script=script_seed,
        hook=request.hook,
        body=request.body,
        cta=request.cta,
    )
    timeline_scenes = parse_clip_to_clip_structure(script_seed)

    if timeline_scenes:
        hook = timeline_scenes[0].subtitle if timeline_scenes else seed_parts.hook
        cta = timeline_scenes[-1].subtitle if timeline_scenes else seed_parts.cta
        body_lines = [s.subtitle for s in timeline_scenes[1:-1] if s.subtitle]
        body = " ".join(body_lines).strip() or seed_parts.body
        duration_seconds = int(max(scene.end for scene in timeline_scenes))

        return {
            "success": True,
            "duration_seconds": duration_seconds,
            "final_script": script_seed,
            "full_script": script_seed,
            "hook": hook,
            "body": body,
            "cta": cta,
            "retention_notes": ["Using provided clip-to-clip structure exactly as timeline."],
            "scenes": make_scene_response(timeline_scenes),
            "platform_meta": {
                "youtube_shorts": {"title": "", "description": "", "hashtags": ""},
                "reels": {"title": "", "description": "", "hashtags": ""},
                "tiktok": {"title": "", "description": "", "hashtags": ""},
            },
        }

    duration_seconds = resolve_duration_seconds(seed_parts, request.duration_seconds)

    try:
        planned = generate_video_plan(script_seed, duration_seconds=duration_seconds)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Video planning failed: {str(exc)}")

    final_script = (planned.get("final_script") or script_seed).strip()
    hook = (planned.get("hook") or request.hook or "").strip()
    body = (planned.get("body") or request.body or "").strip()
    cta = (planned.get("cta") or request.cta or "").strip()

    if not (hook and body and cta):
        parsed = parse_script(final_script, hook=hook or None, body=body or None, cta=cta or None)
        hook, body, cta = parsed.hook, parsed.body, parsed.cta

    scenes = planned.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        scenes = make_scene_response(
            build_scene_plan(
                parse_script(final_script, hook=hook, body=body, cta=cta),
                duration_seconds=duration_seconds,
                stock_mode=request.scene_mode == "stock",
            )
        )
    elif request.scene_mode == "stock":
        scenes = apply_stock_hook_framework_to_scene_rows(scenes, hook or seed_parts.hook or "")

    platform_meta = planned.get("platform_meta") if isinstance(planned.get("platform_meta"), dict) else {
        "youtube_shorts": {"title": "", "description": "", "hashtags": ""},
        "reels": {"title": "", "description": "", "hashtags": ""},
        "tiktok": {"title": "", "description": "", "hashtags": ""},
    }

    return {
        "success": True,
        "duration_seconds": duration_seconds,
        "final_script": final_script,
        "full_script": final_script,
        "hook": hook,
        "body": body,
        "cta": cta,
        "retention_notes": planned.get("retention_notes") or [],
        "scenes": scenes,
        "platform_meta": platform_meta,
    }


def _image_from_data_url(data_url: str):
    if not data_url:
        raise ValueError("Invalid image data URL")

    if str(data_url).startswith("http://") or str(data_url).startswith("https://"):
        try:
            response = httpx.get(str(data_url), timeout=10.0)
            response.raise_for_status()
            binary = response.content
        except Exception as exc:
            raise ValueError(f"Invalid remote image URL: {exc}")
    else:
        if "," not in data_url:
            raise ValueError("Invalid image data URL")
        payload = data_url.split(",", 1)[1]
        binary = base64.b64decode(payload)

    from PIL import Image

    return Image.open(io.BytesIO(binary)).convert("RGB")


def _normalize_scene_duration(value: Any, default: float = 3.0) -> float:
    try:
        val = float(value or default)
    except Exception:
        return float(default)
    return max(1.2, min(5.0, val))
_pexels_thumb_cache: dict[str, tuple[float, str]] = {}  # query → (expires, img_url)
_thumb_luma_cache: dict[str, tuple[float, float]] = {}  # img_url -> (expires, luma)


async def _get_stock_thumbnail(scene_description: str) -> str:
    """Fetch a real Pexels video thumbnail image URL for stock-mode preview scenes.
    Falls back to a Pexels search page URL if the API key is missing or the call fails.
    Results are cached in-process for 1 hour to avoid hammering the API during batch preview."""
    import urllib.parse
    words = re.findall(r"[a-zA-Z0-9]+", (scene_description or "").lower())
    stop = {"a", "an", "the", "is", "in", "on", "at", "to", "for", "of", "and", "or", "with", "that", "this", "are", "was", "be"}
    avoid_dark = {
        "dark", "black", "night", "shadow", "silhouette", "background", "gradient",
        "text", "animation", "graphics", "symbol", "symbols", "neon", "overlay",
    }
    keywords = [w for w in words if len(w) > 3 and w not in stop and w not in avoid_dark][:4]
    if not keywords:
        keywords = ["business", "technology", "person"]
    query = " ".join(keywords)

    # Return cached thumbnail if still fresh
    cached = _pexels_thumb_cache.get(query)
    if cached and _time.time() < cached[0]:
        return cached[1]

    api_key = os.getenv("PEXELS_API_KEY", "").strip()
    if api_key:
        try:
            async def _thumbnail_luma(img_url: str) -> float:
                cached_luma = _thumb_luma_cache.get(img_url)
                if cached_luma and _time.time() < cached_luma[0]:
                    return cached_luma[1]
                try:
                    async with httpx.AsyncClient(timeout=6.0) as img_client:
                        img_res = await img_client.get(img_url)
                        img_res.raise_for_status()
                    from PIL import Image, ImageStat
                    img = Image.open(io.BytesIO(img_res.content)).convert("L")
                    luma = float(ImageStat.Stat(img).mean[0])
                except Exception:
                    luma = 255.0
                _thumb_luma_cache[img_url] = (_time.time() + 3600.0, luma)
                return luma

            async with httpx.AsyncClient(timeout=6.0) as client:
                res = await client.get(
                    "https://api.pexels.com/v1/videos/search",
                    headers={"Authorization": api_key},
                    params={"query": query, "per_page": 8, "orientation": "portrait"},
                )
                if res.status_code == 200:
                    videos = res.json().get("videos", [])
                    if videos:
                        best_url = ""
                        best_score = float("inf")
                        min_luma = float(os.getenv("PREVIEW_THUMB_MIN_LUMA", "48"))
                        query_tokens = set(keywords)
                        learning_intent = bool(query_tokens.intersection({"ai", "learn", "learning", "beginner", "guide", "tutorial", "master", "prompt"}))
                        off_topic_tokens = {"traffic", "highway", "city", "road", "car", "street", "bridge", "building", "night", "skyline"}
                        for idx, v in enumerate(videos[:8]):
                            img_url = (v.get("image") or "").strip()
                            if not img_url:
                                continue
                            luma = await _thumbnail_luma(img_url)
                            meta_blob = " ".join([
                                str(v.get("url", "")),
                                str((v.get("user") or {}).get("name", "")),
                            ]).lower()
                            off_topic_overlap = sum(1 for t in off_topic_tokens if t in meta_blob)
                            # Prefer bright but not overexposed images; penalize dark thumbnails heavily.
                            dark_penalty = 800.0 if luma < min_luma else 0.0
                            luma_target_penalty = abs(145.0 - luma)
                            rank_penalty = idx * 6.0
                            intent_penalty = (off_topic_overlap * 45.0) if learning_intent else 0.0
                            score = dark_penalty + luma_target_penalty + rank_penalty + intent_penalty
                            if score < best_score:
                                best_score = score
                                best_url = img_url
                        if best_url:
                            _pexels_thumb_cache[query] = (_time.time() + 3600.0, best_url)
                            return best_url
        except Exception:
            pass  # fall through to placeholder

    # Fallback: static Pexels search page URL (no auth required)
    encoded = urllib.parse.quote(query)
    fallback = f"https://images.pexels.com/photos/search?q={encoded}&preview=true"
    _pexels_thumb_cache[query] = (_time.time() + 300.0, fallback)  # cache fallbacks for 5 min only
    return fallback


def _slugify(value: str, max_len: int = 60) -> str:
    text = re.sub(r"[^a-zA-Z0-9\-\s_]", "", str(value or "")).strip().replace("_", "-")
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    if not text:
        return ""
    return text[:max_len]


def _strip_unwanted_year_tokens(text: Optional[str], *, script_text: str) -> str:
    """
    Deterministically remove injected years (e.g. "2024") unless they appear in the script input.

    Used for SEO title / thumbnail text and any slug/rename inputs so filenames don't drift to stale years.
    """
    raw = str(text or "").strip()
    if not raw:
        return ""

    allowed_years = set(re.findall(r"\b(?:19|20)\d{2}\b", str(script_text or "")))

    def _repl(match: re.Match) -> str:
        year = match.group(0)
        return year if year in allowed_years else ""

    cleaned = re.sub(r"\b(?:19|20)\d{2}\b", _repl, raw)
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
    cleaned = re.sub(r"\s*[-–—]\s*$", "", cleaned).strip()
    cleaned = re.sub(r"^\s*[-–—]\s*", "", cleaned).strip()
    return cleaned


def _prepare_thumbnail_text(raw_title: str, script_text: Optional[str] = None) -> str:
    title_for_thumb = (raw_title or "").strip()
    if title_for_thumb:
        first_phrase = re.split(r"[?!.]", title_for_thumb)[0].strip()
        words = first_phrase.split()
        title_for_thumb = " ".join(words[:7]) if len(words) > 7 else (first_phrase or title_for_thumb)

    # If title is generic, append learning intent for educational scripts.
    script_tokens = set(re.findall(r"[a-zA-Z]{3,}", (script_text or "").lower()))
    title_tokens = set(re.findall(r"[a-zA-Z]{3,}", title_for_thumb.lower()))
    learning_signal = {"beginner", "beginners", "guide", "learn", "learning", "day", "days", "master"}

    if script_tokens.intersection(learning_signal) and not title_tokens.intersection(learning_signal):
        if title_for_thumb:
            title_for_thumb = f"{title_for_thumb} BEGINNER GUIDE"
        else:
            title_for_thumb = "BEGINNER AI GUIDE"

    title_for_thumb = re.sub(r"\s+", " ", title_for_thumb).strip()
    words = title_for_thumb.split()
    return " ".join(words[:9]) if len(words) > 9 else title_for_thumb


def _relative_generated_asset_path(path_value: Optional[str]) -> Optional[str]:
    if not path_value:
        return None
    generated_root = Path(__file__).resolve().parents[1] / "generated_videos"
    candidate = Path(str(path_value))
    try:
        if candidate.is_absolute():
            resolved = candidate.resolve()
            if generated_root.resolve() in resolved.parents:
                return str(resolved.relative_to(generated_root.resolve())).replace("\\", "/")
            return candidate.name
        return str(candidate).replace("\\", "/")
    except Exception:
        return candidate.name


def _organize_run_assets(
    *,
    run_id: str,
    video_path: Path,
    thumbnail_path: Optional[str],
    title: Optional[str],
) -> tuple[str, Optional[str]]:
    generated_root = Path(__file__).resolve().parents[1] / "generated_videos"
    raw_dir = generated_root / "raw"
    temp_dir = generated_root / "temp"
    cache_dir = generated_root / "cache"

    title_slug = _slugify(title or "", max_len=48)
    folder_name = f"{title_slug}-{run_id}" if title_slug else run_id
    run_dir = generated_root / folder_name
    run_dir.mkdir(parents=True, exist_ok=True)

    final_video_name = f"{title_slug}.mp4" if title_slug else f"{run_id}.mp4"
    final_video_path = run_dir / final_video_name

    try:
        video_path.replace(final_video_path)
    except Exception:
        final_video_path.write_bytes(video_path.read_bytes())
        try:
            video_path.unlink(missing_ok=True)
        except Exception:
            pass

    final_thumb_rel = None
    if thumbnail_path:
        thumb_src = Path(thumbnail_path)
        if thumb_src.exists():
            final_thumb_name = f"{title_slug}.jpg" if title_slug else f"{run_id}.jpg"
            final_thumb_path = run_dir / final_thumb_name
            try:
                thumb_src.replace(final_thumb_path)
            except Exception:
                final_thumb_path.write_bytes(thumb_src.read_bytes())
                try:
                    thumb_src.unlink(missing_ok=True)
                except Exception:
                    pass
            final_thumb_rel = str(final_thumb_path.relative_to(generated_root)).replace("\\", "/")

    for src_dir, label in ((raw_dir, "raw"), (temp_dir, "temp"), (cache_dir, "cache")):
        if not src_dir.exists():
            continue
        target = run_dir / label
        moved_any = False
        for path in src_dir.glob(f"{run_id}*"):
            target.mkdir(parents=True, exist_ok=True)
            moved_any = True
            dest = target / path.name
            try:
                path.replace(dest)
            except Exception:
                try:
                    if path.is_file():
                        dest.write_bytes(path.read_bytes())
                        path.unlink(missing_ok=True)
                except Exception:
                    pass
        if moved_any and not any(target.iterdir()):
            try:
                target.rmdir()
            except Exception:
                pass

    rel_video = str(final_video_path.relative_to(generated_root)).replace("\\", "/")
    return rel_video, final_thumb_rel
async def generate_character_profile(script: str, niche: str) -> dict[str, Any]:
    prompt = f"""Analyze this short-video script and return only valid JSON.

SCRIPT:
{script}

NICHE: {niche}

Return keys:
- age: one of [20s, 30s, 40s, 50s]
- gender: one of [male, female, non-binary]
- ethnicity: one of [caucasian, african, asian, hispanic, middle-eastern, mixed]
- hair: short plain descriptor
- clothing: short plain descriptor
- expression: one of [friendly, serious, neutral, excited]
- type: short descriptor like "professional person"
- style: short descriptor like "photorealistic"
"""

    try:
        response = anthropic_client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )
        profile_text = (response.content[0].text or "").strip()
        if profile_text.startswith("```"):
            profile_text = profile_text.strip("`")
            profile_text = profile_text.replace("json", "", 1).strip()
        parsed = json.loads(profile_text)
        if not isinstance(parsed, dict):
            raise ValueError("Profile is not an object")
        return parsed
    except Exception:
        return {
            "age": "30s",
            "gender": "female",
            "ethnicity": "mixed",
            "hair": "short dark",
            "clothing": "business casual",
            "expression": "friendly",
            "type": "professional person",
            "style": "photorealistic",
        }


@router.post("/video/preview")
async def generate_video_preview(
    request: VideoPreviewRequest,
    current_user: User = Depends(get_current_user),
):
    authoritative_script = (request.full_script or request.script or "").strip()
    if not authoritative_script and request.hook and request.body and request.cta:
        authoritative_script = f"[HOOK]\n{request.hook.strip()}\n\n[BODY]\n{request.body.strip()}\n\n[CTA]\n{request.cta.strip()}".strip()

    if not authoritative_script:
        raise HTTPException(status_code=400, detail="Provide an updated script or hook/body/cta before generating preview.")

    try:
        plan = generate_video_plan(script=authoritative_script, duration_seconds=request.duration)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Video planning failed: {str(exc)}")

    scenes = plan.get("scenes") if isinstance(plan, dict) else None
    if not isinstance(scenes, list) or not scenes:
        parsed = parse_script(
            authoritative_script,
            hook=request.hook,
            body=request.body,
            cta=request.cta,
        )
        fallback = build_scene_plan(
            parsed,
            duration_seconds=request.duration,
            stock_mode=request.scene_mode == "stock",
        )
        scenes = make_scene_response(fallback)
    elif request.scene_mode == "stock":
        scenes = apply_stock_hook_framework_to_scene_rows(
            scenes,
            request.hook or (request.full_script or request.script or ""),
        )

    if request.scene_mode == "stock":
        # In stock mode: no character or AI images needed — skip expensive AI calls
        character_profile = {
            "type": "professional person",
            "style": "photorealistic",
            "source": "stock_mode_skip",
        }
    elif request.character_source == "generate":
        character_profile = await generate_character_profile(authoritative_script, request.niche)
    elif request.character_source == "preset":
        character_profile = {"source": "preset", "character_id": request.preset_id}
    else:
        character_profile = {"source": "upload"}

    uploaded_image = None
    if request.uploaded_image_base64:
        try:
            uploaded_image = base64.b64decode(request.uploaded_image_base64)
        except Exception:
            uploaded_image = None

    char_manager = CharacterManager()
    preview_scenes = []
    for i, scene in enumerate(scenes):
        caption_text = scene.get("subtitle") or scene.get("source_text") or ""
        scene_description = scene.get("visual_description") or "Presenter speaking to camera"
        scene_duration = _normalize_scene_duration(scene.get("end", 5) - scene.get("start", 0), default=5)

        # In stock mode no runway credits are consumed and no character image is needed —
        # stock footage is chosen during full generation, not preview.
        # gen4.5 costs 12 credits/sec; gen4_turbo costs 5 credits/sec
        CREDITS_PER_SEC = 12  # gen4.5
        if request.scene_mode == "stock":
            method = "stock"
            credits_cost = 0
            # Fetch real Pexels thumbnail (async, cached 1h) -- no AI calls in stock mode
            stock_thumb = await _get_stock_thumbnail(scene_description)
            image_result = {
                "image_url": stock_thumb,
                "provider": "stock_preview",
                "credits_used": 0,
            }
        else:
            method = "image_to_video" if i == 0 else "extend"
            credits_cost = scene_duration * CREDITS_PER_SEC
            image_result = await char_manager.get_character_image_result(
                source=request.character_source if i == 0 else "generate",
                scene_description=scene_description,
                character_id=request.preset_id,
                uploaded_image=uploaded_image,
                character_profile=character_profile,
                image_provider=request.image_provider,
                variation_token=f"preview-scene-{i}",
            )

        preview_scenes.append(
            {
                "id": f"scene_{i}",
                "scene_index": i,
                "scene_type": scene.get("part") or "body",
                "description": scene_description,
                "caption_text": caption_text,
                "duration": scene_duration,
                "image_url": image_result["image_url"],
                "image_provider": image_result.get("provider"),
                "image_prompt": image_result.get("prompt_used"),
                "image_alternatives": [image_result["image_url"]],
                "method": method,
                "credits_cost": credits_cost,
                "character_source": request.character_source,
                "character_profile": character_profile,
            }
        )

    total_credits = sum(int(s["credits_cost"]) for s in preview_scenes)
    elevenlabs_cost = (len(authoritative_script) / 1000.0) * 0.30

    return {
        "preview_id": str(uuid.uuid4()),
        "scenes": preview_scenes,
        "character_profile": character_profile,
        "estimated_cost": {
            "credits": total_credits,
            "usd": round(total_credits * 0.01, 4),
            "elevenlabs_usd": round(elevenlabs_cost, 4),
            "total_usd": round((total_credits * 0.01) + elevenlabs_cost, 4),
        },
        "can_afford": total_credits <= (750 - int(current_user.usage_count or 0)),
        "instructions": "Review scenes, edit text, reorder, then approve for generation.",
    }


@router.post("/regenerate-scene-image")
async def regenerate_scene_image(
    request: RegenerateSceneImageRequest,
    current_user: User = Depends(get_current_user),
):
    manager = CharacterManager()
    result = await manager.get_character_image_result(
        source="generate",
        scene_description=request.scene_description,
        character_profile=request.character_profile,
        image_provider=request.image_provider,
        variation_token=request.variation_token,
    )
    return {
        "scene_index": request.scene_index,
        "image_url": result["image_url"],
        "provider": result.get("provider"),
        "prompt_used": result.get("prompt_used"),
    }


async def generate_video_from_approved_preview(preview_id: str, scenes: list[dict[str, Any]], user_id: int, dry_run: bool = True):
    # dry_run comes from the calller (request), NOT from env.
    # The env flag is only an emergency override: if env forces dry-run, respect it.
    env_dry_run = os.getenv("VIDEO_GENERATION_DRY_RUN", "1") == "1"
    effective_dry_run = dry_run or env_dry_run  # either flag = no spend

    async with AsyncSessionLocal() as session:
        generation = Generation(
            user_id=user_id,
            input_type="video",
            input_content=f"preview:{preview_id}",
            status="processing",
            video_plan_json=json.dumps({"preview_id": preview_id, "scenes": scenes, "dry_run": effective_dry_run}),
        )
        session.add(generation)
        await session.commit()
        await session.refresh(generation)
        generation_id = generation.id

        if effective_dry_run:
            generation.status = "success"
            generation.error_message = "Dry-run mode active. Set VIDEO_GENERATION_DRY_RUN=0 and disable Dry Run in Video Studio for live generation."
            await session.commit()
            return

        try:
            runway = RunwayMLClient()

            # ── Scene 0: image → video ────────────────────────────────────────
            task_ids = []
            clips = []
            credits_used = 0.0

            first = scenes[0]
            first_img = _image_from_data_url(first["image_url"])
            first_video = await runway.image_to_video(
                image=first_img,
                prompt=first.get("description", "presenter speaking"),
                duration=_normalize_scene_duration(first.get("duration", 5), default=5),
                model="gen4.5",
            )
            clips.append(first_video["video_url"])
            task_ids.append(first_video["task_id"])
            credits_used += float(first_video["credits_used"])

            # ── Scenes 1+: extend from previous OR independent image→video ────
            for scene in scenes[1:]:
                img_url = scene.get("image_url")
                method = scene.get("method", "generate")
                if method == "extend":
                    clip = await runway.extend_video(
                        previous_video_url=clips[-1],
                        prompt=scene.get("description", "continue motion"),
                        duration=_normalize_scene_duration(scene.get("duration", 5), default=5),
                        model="gen4.5",
                    )
                elif img_url:
                    # Independent image → video for scenes with their own image
                    clip = await runway.image_to_video(
                        image=_image_from_data_url(img_url),
                        prompt=scene.get("description", "presenter speaking"),
                        duration=_normalize_scene_duration(scene.get("duration", 5), default=5),
                        model="gen4.5",
                    )
                else:
                    # No image and not extend — fall back to extend from previous
                    clip = await runway.extend_video(
                        previous_video_url=clips[-1],
                        prompt=scene.get("description", "continue motion"),
                        duration=_normalize_scene_duration(scene.get("duration", 5), default=5),
                        model="gen4.5",
                    )
                clips.append(clip["video_url"])
                task_ids.append(clip.get("task_id", ""))
                credits_used += float(clip["credits_used"])

            # ── Persist results ───────────────────────────────────────────────
            generation.status = "success"
            generation.video_run_id = task_ids[0] if task_ids else None
            # Store all clip URLs as JSON in video_file so the frontend can retrieve them
            generation.video_file = json.dumps(clips)
            generation.video_scenes_json = json.dumps(scenes)
            generation.runway_credits_used = credits_used
            generation.total_cost_usd = round(credits_used * 0.01, 4)
            generation.error_message = None
            await session.commit()
        except Exception as exc:
            logger.error(f"[VideoGen] generation_id={generation_id} failed: {exc}", exc_info=True)
            try:
                generation.status = "failed"
                generation.error_message = str(exc)[:500]
                await session.commit()
            except Exception:
                async with AsyncSessionLocal() as recovery:
                    from sqlalchemy import update as sa_update
                    await recovery.execute(
                        sa_update(Generation)
                        .where(Generation.id == generation_id)
                        .values(status="failed", error_message=str(exc)[:500])
                    )
                    await recovery.commit()
async def generate_video_from_approved_preview(
    generation_id: int,
    preview_id: str,
    scenes: list[dict[str, Any]],
    user_id: int,
    dry_run: bool = True,
    script: Optional[str] = None,
    niche: str = "general",
    tts_provider: str = "free",
    voice_id: str = "21m00Tcm4TlvDq8ikWAM",
    confirmed_plan: Optional[dict[str, Any]] = None,
):
    """Background task: generate video from approved preview scenes.
    generation_id must reference a pre-created Generation row (status=queued).
    Progress is written to _task_progress[generation_id] throughout."""
    env_dry_run = os.getenv("VIDEO_GENERATION_DRY_RUN", "1") == "1"
    effective_dry_run = dry_run or env_dry_run  # either flag = no spend

    def _upd(percent: int, message: str, step: str = ""):
        _task_progress[generation_id] = {
            "percent": percent,
            "message": message,
            "step": step,
            "updated_at": datetime.utcnow().isoformat(),
        }

    _upd(5, "Starting...", "init")

    async with AsyncSessionLocal() as session:
        row = await session.execute(select(Generation).where(Generation.id == generation_id))
        generation = row.scalar_one_or_none()
        if not generation:
            logger.error(f"[VideoGen] generation_id={generation_id} not found in DB")
            _upd(0, "Internal error: generation record missing", "error")
            return

        generation.status = "processing"
        generation.video_plan_json = json.dumps({
            "preview_id": preview_id,
            "scenes": scenes,
            "dry_run": effective_dry_run,
            "script": script,
            "confirmed_plan": confirmed_plan,
        })
        await session.commit()

        if effective_dry_run:
            _upd(100, "Dry-run complete — no credits consumed.", "done")
            generation.status = "success"
            generation.video_scenes_json = json.dumps(scenes)
            generation.video_duration_seconds = int(sum(float(s.get("duration", 5) or 5) for s in scenes)) if scenes else None
            generation.error_message = "Dry-run mode active. Set VIDEO_GENERATION_DRY_RUN=0 and disable Dry Run in Video Studio for live generation."
            await session.commit()
            return

        all_stock_mode = bool(scenes) and all(str(scene.get("method", "")).lower() == "stock" for scene in scenes)
        if all_stock_mode:
            try:
                _upd(20, "Footage mode detected — building stock clips...", "stock")
                run_id = new_run_id()

                script_text = (script or "").strip() or " ".join(
                    str(scene.get("subtitle") or scene.get("source_text") or "").strip()
                    for scene in scenes
                ).strip()

                audio_path = None
                if script_text:
                    if effective_dry_run:
                        _upd(28, "Dry-run: skipping TTS.", "tts")
                    else:
                        try:
                            tts_result = generate_voice(
                                VoiceGenRequest(
                                    text=script_text,
                                    voice_id=voice_id,
                                    force_free=(tts_provider == "free"),
                                )
                            )
                            audio_path = tts_result.audio_file
                            _upd(35, "Voice track generated.", "tts")
                        except Exception as tts_exc:
                            logger.warning(f"[VideoGen] Stock-mode TTS failed, continuing silent: {tts_exc}")

                if not effective_dry_run and is_audio_required_enabled() and not _is_valid_audio_file(audio_path):
                    generation.status = "failed"
                    generation.error_message = (
                        "Voice generation failed, so rendering was stopped to avoid silent output and unnecessary cost. "
                        "Retry with Free TTS or fix ElevenLabs settings."
                    )
                    await session.commit()
                    _upd(0, generation.error_message, "error")
                    return

                source_durations = [float(_normalize_scene_duration(scene.get("duration", 5), default=5)) for scene in scenes]
                audio_duration = _get_audio_duration_seconds(audio_path) if not effective_dry_run else None
                if audio_duration and audio_duration > 0:
                    balanced_durations = _rebalance_scene_durations(source_durations, target_total=audio_duration)
                else:
                    balanced_durations = source_durations

                # Dynamic scene count (segmentation-first): prefer 1 beat per scene.
                # This is internal only: no schema/API changes.
                beats = _segment_script_into_beats(script_text)
                max_scenes = 6
                allocated_scene_count = min(max_scenes, len(beats)) if beats else len(scenes)
                merged_beats = max(0, (len(beats) - allocated_scene_count)) if beats else 0
                print(
                    "[SCENE_ALLOCATION] "
                    f"total_beats={len(beats)} scene_count={allocated_scene_count} merged_beats={merged_beats}"
                )

                # Build durations for the allocated scene count (keep deterministic; match total audio when available).
                if audio_duration and audio_duration > 0:
                    # Use equal durations that sum to the audio duration (avoid ratio caps that can create a huge last scene).
                    per = max(2.0, float(audio_duration) / float(max(1, allocated_scene_count)))
                    alloc_durations = [per] * allocated_scene_count
                    drift = float(audio_duration) - sum(alloc_durations)
                    alloc_durations[-1] = max(2.0, alloc_durations[-1] + drift)
                else:
                    total = float(sum(balanced_durations) or (allocated_scene_count * 5.0))
                    per = total / float(max(1, allocated_scene_count))
                    alloc_durations = [per] * allocated_scene_count

                scripted_scene_captions = _split_script_for_scenes(
                    script_text=script_text,
                    scene_count=allocated_scene_count,
                    durations=alloc_durations,
                )

                hook_source_scene = next((s for s in scenes if str(s.get("scene_type") or "").lower() == "hook"), scenes[0] if scenes else {})
                body_source_scenes = [
                    s for s in scenes
                    if str(s.get("scene_type") or "").lower() not in {"hook", "cta"}
                ]
                cta_source_scene = next((s for s in reversed(scenes) if str(s.get("scene_type") or "").lower() == "cta"), scenes[-1] if scenes else {})

                start_sec = 0.0
                scene_rows = []
                body_source_index = 0
                scene_count_changed = allocated_scene_count != len(scenes)
                for idx in range(1, len(scripted_scene_captions) + 1):
                    part = "hook" if idx == 1 else ("cta" if idx == len(scripted_scene_captions) else "body")
                    if part == "hook":
                        scene = hook_source_scene or {}
                    elif part == "cta":
                        scene = cta_source_scene or {}
                    else:
                        if body_source_scenes:
                            scene = body_source_scenes[min(body_source_index, len(body_source_scenes) - 1)]
                        else:
                            scene = hook_source_scene or cta_source_scene or {}
                        body_source_index += 1
                    duration = float(alloc_durations[idx - 1] if idx - 1 < len(alloc_durations) else 5.0)
                    end_sec = start_sec + duration
                    # Spoken/caption truth: store in subtitle/source_text (never in on_screen_text).
                    # Display-only on_screen_text may differ later (hook treatment), but in preview
                    # workflow we default it to the spoken line for safety.
                    spoken_text = str(
                        scripted_scene_captions[idx - 1]
                        or scene.get("subtitle")
                        or scene.get("source_text")
                        or ""
                    ).strip()
                    display_text = str(scene.get("on_screen_text") or spoken_text).strip()
                    visual_description = str(scene.get("description") or "Stock footage scene").strip()
                    # If we expanded preview scenes into more spoken beats, generic preview descriptions
                    # become misleading for body scenes. Use the spoken beat itself as the stock seed.
                    if scene_count_changed and part == "body":
                        visual_description = spoken_text or visual_description
                    scene_rows.append(
                        {
                            "scene": idx,
                            "start": start_sec,
                            "end": end_sec,
                            "part": part,
                            "source_text": spoken_text,
                            "subtitle": spoken_text,
                            "visual_description": visual_description,
                            "on_screen_text": display_text,
                            "energy": "curiosity",
                        }
                    )
                    _log_scene_text_check(
                        scene_idx=idx,
                        subtitle=spoken_text,
                        on_screen_text=display_text,
                        visual_description=visual_description,
                    )
                    start_sec = end_sec

                stock_scenes = scenes_from_rows(scene_rows)
                if not stock_scenes:
                    raise RuntimeError("Failed to build stock timeline from approved scenes")

                stock_scenes = await fetch_scene_clips(
                    stock_scenes,
                    run_id=run_id,
                    mode="stock",
                    available_credits=0.0,
                )
                _upd(75, "Assembling footage video...", "render")
                render_result = assemble_video(stock_scenes, run_id=run_id, audio_path=audio_path)

                seo_metadata = None
                if script_text:
                    try:
                        seo_metadata = await generate_youtube_metadata(
                            script=script_text,
                            niche=niche or "general",
                            duration=int(sum(float(s.get("duration", 5) or 5) for s in scenes)),
                        )
                    except Exception as seo_exc:
                        logger.warning(f"[VideoGen] SEO metadata failed in stock mode: {seo_exc}")

                video_path_obj = Path(render_result["video_path"])
                thumb_path = render_result.get("thumbnail_path")

                raw_thumb_text = (
                    (seo_metadata or {}).get("thumbnail_text")
                    or (seo_metadata or {}).get("title")
                    or ""
                )
                title_for_thumb = _prepare_thumbnail_text(raw_thumb_text, script_text=script_text)
                if title_for_thumb:
                    try:
                        thumb_path = render_thumbnail(str(video_path_obj), title_for_thumb, thumb_path)
                    except Exception as thumb_exc:
                        logger.warning(f"[VideoGen] Thumbnail overlay failed in stock mode: {thumb_exc}")

                stored_video_file, stored_thumb_file = _organize_run_assets(
                    run_id=run_id,
                    video_path=video_path_obj,
                    thumbnail_path=thumb_path,
                    title=(seo_metadata or {}).get("title"),
                )

                platform_meta = None
                if isinstance(confirmed_plan, dict):
                    maybe_meta = confirmed_plan.get("platform_meta")
                    if isinstance(maybe_meta, dict):
                        platform_meta = maybe_meta

                generation.status = "success"
                generation.video_run_id = run_id
                generation.video_file = stored_video_file
                generation.video_thumbnail = stored_thumb_file
                generation.video_duration_seconds = int(sum(float(s.get("duration", 5) or 5) for s in scenes))
                generation.video_scenes_json = json.dumps(scenes)
                generation.runway_credits_used = 0.0
                generation.elevenlabs_credits_used = 0 if effective_dry_run or tts_provider == "free" else len(script_text or "")
                generation.total_cost_usd = 0.0
                generation.video_platform_meta_json = json.dumps(platform_meta) if platform_meta else None
                generation.seo_title = (seo_metadata or {}).get("title") if isinstance(seo_metadata, dict) else None
                generation.seo_description = (seo_metadata or {}).get("description") if isinstance(seo_metadata, dict) else None
                generation.seo_tags = json.dumps((seo_metadata or {}).get("tags", [])) if isinstance(seo_metadata, dict) else None
                generation.seo_hashtags = json.dumps((seo_metadata or {}).get("hashtags", [])) if isinstance(seo_metadata, dict) else None
                generation.thumbnail_text = (seo_metadata or {}).get("thumbnail_text") if isinstance(seo_metadata, dict) else None
                generation.error_message = None
                await session.commit()
                _upd(100, "Footage video complete.", "done")
                _task_progress.pop(generation_id, None)
                return
            except Exception as exc:
                logger.error(f"[VideoGen] stock generation_id={generation_id} failed: {exc}", exc_info=True)
                _upd(0, f"Failed: {str(exc)[:120]}", "error")
                try:
                    generation.status = "failed"
                    generation.error_message = str(exc)[:500]
                    await session.commit()
                except Exception:
                    async with AsyncSessionLocal() as recovery:
                        from sqlalchemy import update as sa_update
                        await recovery.execute(
                            sa_update(Generation)
                            .where(Generation.id == generation_id)
                            .values(status="failed", error_message=str(exc)[:500])
                        )
                        await recovery.commit()
                return

        try:
            runway = RunwayMLClient()

            _upd(15, "Submitting scene 1 to RunwayML...", "runway")

            # ── Scene 0: image → video ────────────────────────────────────────
            task_ids = []
            clips = []
            credits_used = 0.0

            first = scenes[0]
            first_img = _image_from_data_url(first["image_url"])
            first_video = await runway.image_to_video(
                image=first_img,
                prompt=first.get("description", "presenter speaking"),
                duration=_normalize_scene_duration(first.get("duration", 5), default=5),
                model="gen4.5",
            )
            clips.append(first_video["video_url"])
            task_ids.append(first_video["task_id"])
            credits_used += float(first_video["credits_used"])

            # ── Scenes 1+: extend from previous OR independent image→video ────
            total_scenes = len(scenes)
            for idx, scene in enumerate(scenes[1:], start=1):
                pct = 15 + int((idx / total_scenes) * 55)
                _upd(pct, f"Rendering scene {idx + 1} of {total_scenes}...", "runway")

                img_url = scene.get("image_url")
                method = scene.get("method", "generate")
                if method == "extend":
                    clip = await runway.extend_video(
                        previous_video_url=clips[-1],
                        prompt=scene.get("description", "continue motion"),
                        duration=_normalize_scene_duration(scene.get("duration", 5), default=5),
                        model="gen4.5",
                    )
                elif img_url:
                    clip = await runway.image_to_video(
                        image=_image_from_data_url(img_url),
                        prompt=scene.get("description", "presenter speaking"),
                        duration=_normalize_scene_duration(scene.get("duration", 5), default=5),
                        model="gen4.5",
                    )
                else:
                    clip = await runway.extend_video(
                        previous_video_url=clips[-1],
                        prompt=scene.get("description", "continue motion"),
                        duration=_normalize_scene_duration(scene.get("duration", 5), default=5),
                        model="gen4.5",
                    )
                clips.append(clip["video_url"])
                task_ids.append(clip.get("task_id", ""))
                credits_used += float(clip["credits_used"])

            # ── Persist results ───────────────────────────────────────────────
            _upd(95, "Saving results...", "saving")
            generation.status = "success"
            generation.video_run_id = task_ids[0] if task_ids else None
            generation.video_file = json.dumps(clips)
            generation.video_scenes_json = json.dumps(scenes)
            generation.runway_credits_used = credits_used
            generation.total_cost_usd = round(credits_used * 0.01, 4)
            generation.error_message = None
            await session.commit()
            _upd(100, "Video generation complete!", "done")
            _task_progress.pop(generation_id, None)  # clean up on success
        except Exception as exc:
            logger.error(f"[VideoGen] generation_id={generation_id} failed: {exc}", exc_info=True)
            _upd(0, f"Failed: {str(exc)[:120]}", "error")
            try:
                generation.status = "failed"
                generation.error_message = str(exc)[:500]
                await session.commit()
            except Exception:
                async with AsyncSessionLocal() as recovery:
                    from sqlalchemy import update as sa_update
                    await recovery.execute(
                        sa_update(Generation)
                        .where(Generation.id == generation_id)
                        .values(status="failed", error_message=str(exc)[:500])
                    )
                    await recovery.commit()


@router.post("/video/generate-from-preview")
async def generate_video_from_preview(
    request: GenerateFromPreviewRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not request.approved_scenes:
        raise HTTPException(status_code=400, detail="No approved scenes provided")

    if not request.dry_run:
        preview_script = (request.full_script or request.script or "").strip()
        if not preview_script:
            preview_script = " ".join(
                str(
                    scene.get("caption_text")
                    or scene.get("on_screen_text")
                    or scene.get("subtitle")
                    or scene.get("description")
                    or ""
                ).strip()
                for scene in request.approved_scenes
            ).strip()
        quality_issue = _script_quality_issue(preview_script)
        if quality_issue:
            raise HTTPException(status_code=400, detail=quality_issue)

    # Pre-create the Generation row so we can return its ID immediately for polling.
    generation = Generation(
        user_id=current_user.id,
        input_type="video",
        input_content=f"preview:{request.preview_id}"[:5000],
        status="queued",
    )
    db.add(generation)
    await db.commit()
    await db.refresh(generation)
    generation_id = generation.id

    # Seed the progress tracker so the polling endpoint can respond instantly.
    _task_progress[generation_id] = {
        "percent": 2,
        "message": "Queued for processing...",
        "step": "queued",
        "updated_at": datetime.utcnow().isoformat(),
    }

    background_tasks.add_task(
        generate_video_from_approved_preview,
        generation_id=generation_id,
        preview_id=request.preview_id,
        scenes=request.approved_scenes,
        user_id=current_user.id,
        dry_run=request.dry_run,
        script=request.script,
        niche=request.niche,
        tts_provider=request.tts_provider,
        voice_id=request.voice_id,
        confirmed_plan=request.confirmed_plan,
    )

    return {
        "status": "queued",
        "generation_id": generation_id,
        "preview_id": request.preview_id,
        "message": "Video generation started in background.",
        "dry_run": request.dry_run,
    }


@router.get("/video/progress/{generation_id}")
async def get_video_generation_progress(
    generation_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Poll the progress of a background video generation task.
    Returns {generation_id, status, percent 0-100, message, step, updated_at}.
    Poll every 3-5 seconds while status is queued or processing."""
    row = await db.execute(
        select(Generation).where(
            and_(Generation.id == generation_id, Generation.user_id == current_user.id)
        )
    )
    generation = row.scalar_one_or_none()
    if not generation:
        raise HTTPException(status_code=404, detail="Generation not found")

    if generation.status == "success":
        _task_progress.pop(generation_id, None)
        return {
            "generation_id": generation_id,
            "status": "success",
            "percent": 100,
            "message": "Video generation complete!",
            "step": "done",
            "updated_at": generation.created_at.isoformat() if generation.created_at else None,
        }

    if generation.status == "failed":
        _task_progress.pop(generation_id, None)
        return {
            "generation_id": generation_id,
            "status": "failed",
            "percent": 0,
            "message": generation.error_message or "Generation failed.",
            "step": "error",
            "updated_at": None,
        }

    hmr_job_row = await db.execute(
        select(HMRRenderJob).where(HMRRenderJob.generation_id == generation_id)
    )
    hmr_job = hmr_job_row.scalar_one_or_none()
    if hmr_job is not None:
        progress = hmr_job_to_progress(hmr_job)
        return {"generation_id": generation_id, "status": hmr_job.status, **progress}

    # If the server restarted mid-job, in-memory progress is lost and the background task
    # will never finish. Mark stale rows as failed so the UI doesn't stay stuck forever.
    progress_entry = _task_progress.get(generation_id)
    if generation.status in {"queued", "processing"} and not progress_entry:
        try:
            created_at = generation.created_at
            if created_at:
                age_seconds = (datetime.utcnow() - created_at).total_seconds()
            else:
                age_seconds = 0
        except Exception:
            age_seconds = 0
        stale_after = int(os.getenv("VIDEO_PROGRESS_STALE_SECONDS", "300"))
        if age_seconds >= stale_after:
            generation.status = "failed"
            generation.error_message = (
                "Video generation was interrupted (server restart or worker crash). "
                "Please retry."
            )
            try:
                await db.commit()
            except Exception:
                pass
            return {
                "generation_id": generation_id,
                "status": "failed",
                "percent": 0,
                "message": generation.error_message,
                "step": "error",
                "updated_at": None,
            }

    progress = _task_progress.get(generation_id) or {
        "percent": 5,
        "message": "Processing...",
        "step": "processing",
        "updated_at": None,
    }
    return {"generation_id": generation_id, "status": generation.status, **progress}


@router.get("/video/characters/presets")
async def get_character_presets(current_user: User = Depends(get_current_user)):
    manager = CharacterManager()
    return {"presets": list(manager.preset_library.values())}


@router.post("/regenerate-thumbnail")
async def regenerate_thumbnail(
    request: RegenerateThumbnailRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    row = await db.execute(
        select(Generation).where(and_(Generation.id == request.video_id, Generation.user_id == current_user.id))
    )
    generation = row.scalar_one_or_none()
    if not generation:
        raise HTTPException(status_code=404, detail="Video generation not found")

    if not generation.video_file:
        raise HTTPException(status_code=400, detail="Video file not available")

    generated_root = Path(__file__).resolve().parents[1] / "generated_videos"
    video_path = (generated_root / generation.video_file).resolve()
    if generated_root.resolve() not in video_path.parents:
        raise HTTPException(status_code=400, detail="Invalid video path")
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found on disk")

    target_thumb = str(video_path).replace(".mp4", ".jpg")
    thumbnail_path = render_thumbnail(str(video_path), request.thumbnail_text, target_thumb)
    generation.video_thumbnail = _relative_generated_asset_path(thumbnail_path)
    generation.thumbnail_text = request.thumbnail_text
    await db.commit()

    return {
        "video_id": generation.id,
        "thumbnail_url": f"/api/generate/video/thumbnail/{quote(str(_relative_generated_asset_path(thumbnail_path) or ''), safe='/')}",
        "thumbnail_path": _relative_generated_asset_path(thumbnail_path),
    }


@router.post("/video/editor/save")
async def save_video_editor_changes(
    request: SaveVideoEditorRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    row = await db.execute(
        select(Generation).where(and_(Generation.id == request.video_id, Generation.user_id == current_user.id))
    )
    generation = row.scalar_one_or_none()
    if not generation:
        raise HTTPException(status_code=404, detail="Video generation not found")

    existing_meta = {}
    try:
        existing_meta = json.loads(generation.video_platform_meta_json) if generation.video_platform_meta_json else {}
    except Exception:
        existing_meta = {}

    editor_payload = {
        "captions": request.captions,
        "caption_style": request.caption_style,
        "updated_at": datetime.utcnow().isoformat(),
    }
    existing_meta["editor"] = editor_payload

    if isinstance(request.platform_meta, dict):
        for key, value in request.platform_meta.items():
            existing_meta[key] = value

    generation.video_platform_meta_json = json.dumps(existing_meta)

    if request.thumbnail_text is not None:
        generation.thumbnail_text = request.thumbnail_text

    if isinstance(request.seo, dict):
        if "title" in request.seo:
            generation.seo_title = request.seo.get("title")
        if "description" in request.seo:
            generation.seo_description = request.seo.get("description")

        tags = request.seo.get("tags")
        if isinstance(tags, list):
            generation.seo_tags = json.dumps(tags)
        elif isinstance(tags, str):
            generation.seo_tags = json.dumps([t.strip() for t in tags.split(",") if t.strip()])

        hashtags = request.seo.get("hashtags")
        if isinstance(hashtags, list):
            generation.seo_hashtags = json.dumps(hashtags)
        elif isinstance(hashtags, str):
            generation.seo_hashtags = json.dumps([h.strip() for h in hashtags.replace("\n", " ").split(" ") if h.strip()])

    await db.commit()
    return {"success": True, "video_id": generation.id}


@router.get("/video/history")
async def get_video_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Generation)
        .where(and_(Generation.user_id == current_user.id, Generation.input_type == "video"))
        .order_by(Generation.created_at.desc())
        .limit(50)
    )
    rows = result.scalars().all()

    history = []
    for g in rows:
        try:
            history.append(_serialize_video_history_row(g, include_heavy=False))
        except Exception as exc:
            logger.warning(f"[video.history] Failed to serialize row id={getattr(g, 'id', None)}: {exc}")
            history.append(_serialize_video_history_row_fallback(g, warning=str(exc)))

    return history


def _safe_json_loads(value: Any, *, expected_type: type | None = None, default: Any = None):
    if not value:
        return default
    try:
        parsed = json.loads(value)
    except Exception:
        return default
    if expected_type is not None and not isinstance(parsed, expected_type):
        return default
    return parsed


def _serialize_video_history_row(
    g: Generation,
    *,
    include_heavy: bool,
    warning: Optional[str] = None,
) -> dict[str, Any]:
    parsed_seo_tags = _safe_json_loads(g.seo_tags, expected_type=list, default=[]) or []
    parsed_seo_hashtags = _safe_json_loads(g.seo_hashtags, expected_type=list, default=[]) or []

    payload = {
        "id": g.id,
        "run_id": g.video_run_id,
        "duration_seconds": g.video_duration_seconds,
        "file": g.video_file,
        "video_url": f"/api/generate/video/download/{quote(str(g.video_file), safe='/')}" if g.video_file else None,
        "download_url": f"/api/generate/video/download/{quote(str(g.video_file), safe='/')}" if g.video_file else None,
        "thumbnail_url": f"/api/generate/video/thumbnail/{quote(str(_relative_generated_asset_path(g.video_thumbnail) or ''), safe='/')}" if g.video_thumbnail else None,
        "created_at": g.created_at.isoformat() if g.created_at else None,
        "status": g.status,
        "warning": warning or g.error_message,
        "seo": {
            "title": g.seo_title,
            "description": g.seo_description,
            "tags": parsed_seo_tags,
            "hashtags": parsed_seo_hashtags,
            "thumbnail_text": g.thumbnail_text,
        },
        "costs": {
            "runway_credits_used": g.runway_credits_used or 0,
            "elevenlabs_credits_used": g.elevenlabs_credits_used or 0,
            "total_cost_usd": g.total_cost_usd or 0,
        },
    }

    if not include_heavy:
        payload.update({
            "parts": None,
            "plan": None,
            "scenes": None,
            "platform_meta": None,
            "editor": None,
        })
        return payload

    parsed_plan = _safe_json_loads(g.video_plan_json, expected_type=dict, default=None)
    parsed_meta = _safe_json_loads(g.video_platform_meta_json, expected_type=dict, default=None)

    parsed_scenes = _safe_json_loads(g.video_scenes_json, expected_type=list, default=None)
    if not parsed_scenes and isinstance(parsed_plan, dict):
        fallback_scenes = parsed_plan.get("scenes")
        if isinstance(fallback_scenes, list) and fallback_scenes:
            parsed_scenes = fallback_scenes

    payload.update({
        "parts": {
            "hook": (parsed_plan or {}).get("hook"),
            "body": (parsed_plan or {}).get("body"),
            "cta": (parsed_plan or {}).get("cta"),
        } if isinstance(parsed_plan, dict) else None,
        "plan": parsed_plan,
        "scenes": parsed_scenes,
        "platform_meta": parsed_meta,
        "editor": (parsed_meta or {}).get("editor") if isinstance(parsed_meta, dict) else None,
    })
    return payload


def _serialize_video_history_row_fallback(g: Generation, warning: Optional[str] = None) -> dict[str, Any]:
    return {
        "id": g.id,
        "run_id": g.video_run_id,
        "duration_seconds": g.video_duration_seconds,
        "file": g.video_file,
        "video_url": f"/api/generate/video/download/{quote(str(g.video_file), safe='/')}" if g.video_file else None,
        "download_url": f"/api/generate/video/download/{quote(str(g.video_file), safe='/')}" if g.video_file else None,
        "thumbnail_url": f"/api/generate/video/thumbnail/{quote(str(_relative_generated_asset_path(g.video_thumbnail) or ''), safe='/')}" if g.video_thumbnail else None,
        "created_at": g.created_at.isoformat() if g.created_at else None,
        "status": g.status,
        "warning": warning or g.error_message,
        "seo": {
            "title": g.seo_title,
            "description": g.seo_description,
            "tags": [],
            "hashtags": [],
            "thumbnail_text": g.thumbnail_text,
        },
        "costs": {
            "runway_credits_used": g.runway_credits_used or 0,
            "elevenlabs_credits_used": g.elevenlabs_credits_used or 0,
            "total_cost_usd": g.total_cost_usd or 0,
        },
        "parts": None,
        "plan": None,
        "scenes": None,
        "platform_meta": None,
        "editor": None,
    }


@router.get("/video/history/{generation_id}")
async def get_video_history_item(
    generation_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    row = await db.execute(
        select(Generation).where(
            and_(
                Generation.id == generation_id,
                Generation.user_id == current_user.id,
                Generation.input_type == "video",
            )
        )
    )
    generation = row.scalar_one_or_none()
    if not generation:
        raise HTTPException(status_code=404, detail="Video history item not found")

    try:
        return _serialize_video_history_row(generation, include_heavy=True)
    except Exception as exc:
        logger.warning(f"[video.history.detail] Failed to serialize row id={generation_id}: {exc}")
        return _serialize_video_history_row_fallback(generation, warning=str(exc))


def _safe_remove_generated_file(path_value: Optional[str], generated_root: Path) -> None:
    if not path_value:
        return
    candidate = Path(str(path_value))
    try:
        resolved = candidate.resolve() if candidate.is_absolute() else (generated_root / candidate).resolve()
    except Exception:
        return
    if generated_root.resolve() not in resolved.parents:
        return
    if resolved.exists() and resolved.is_file():
        try:
            resolved.unlink()
        except Exception:
            pass


def _delete_generation_assets(generation: Generation) -> None:
    generated_root = Path(__file__).resolve().parents[1] / "generated_videos"
    raw_dir = generated_root / "raw"
    temp_dir = generated_root / "temp"
    cache_dir = generated_root / "cache"

    # Primary output files
    _safe_remove_generated_file(generation.video_file, generated_root)
    _safe_remove_generated_file(generation.video_thumbnail, generated_root)

    # Thumbnail may be absolute path; fallback by basename as well.
    if generation.video_thumbnail:
        _safe_remove_generated_file(Path(str(generation.video_thumbnail)).name, generated_root)

    # Remove run-specific artifacts in raw/temp/cache and main folder.
    run_id = (generation.video_run_id or "").strip()
    if run_id:
        for folder in (generated_root, raw_dir, temp_dir, cache_dir):
            if not folder.exists():
                continue
            for path in folder.glob(f"*{run_id}*"):
                try:
                    if path.is_file():
                        path.unlink()
                    elif path.is_dir():
                        for nested in path.rglob("*"):
                            if nested.is_file():
                                nested.unlink(missing_ok=True)
                        path.rmdir()
                except Exception:
                    pass


@router.delete("/video/{generation_id}")
async def _delete_video_history_item_core(
    generation_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    row = await db.execute(
        select(Generation).where(
            and_(
                Generation.id == generation_id,
                Generation.user_id == current_user.id,
                Generation.input_type == "video",
            )
        )
    )
    generation = row.scalar_one_or_none()
    if not generation:
        raise HTTPException(status_code=404, detail="Video history item not found")
    if generation.status in {"queued", "processing"}:
        raise HTTPException(status_code=409, detail="Cannot delete a video that is currently processing")

    _delete_generation_assets(generation)
    await db.delete(generation)
    await db.commit()
    _task_progress.pop(generation_id, None)

    return {
        "success": True,
        "deleted_id": generation_id,
        "message": "Video and related generated assets deleted.",
    }


@router.delete("/video/{generation_id}")
async def delete_video_history_item(
    generation_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _delete_video_history_item_core(generation_id=generation_id, current_user=current_user, db=db)


@router.delete("/video/history/{generation_id}")
async def delete_video_history_item_legacy_path(
    generation_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Backward-compatible alias path for clients that target /video/history/{id}.
    return await _delete_video_history_item_core(generation_id=generation_id, current_user=current_user, db=db)


@router.get("/analytics")
async def get_analytics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    total_videos_result = await db.execute(
        select(func.count(Generation.id)).where(
            and_(Generation.user_id == current_user.id, Generation.input_type == "video")
        )
    )
    total_videos = int(total_videos_result.scalar() or 0)

    runway_credits_result = await db.execute(
        select(func.sum(Generation.runway_credits_used)).where(
            and_(Generation.user_id == current_user.id, Generation.input_type == "video")
        )
    )
    runway_credits = float(runway_credits_result.scalar() or 0.0)

    avg_cost_result = await db.execute(
        select(func.avg(Generation.total_cost_usd)).where(
            and_(Generation.user_id == current_user.id, Generation.input_type == "video")
        )
    )
    avg_cost = float(avg_cost_result.scalar() or 0.0)

    recent_rows = await db.execute(
        select(Generation)
        .where(and_(Generation.user_id == current_user.id, Generation.input_type == "video"))
        .order_by(Generation.created_at.desc())
        .limit(20)
    )
    recent = recent_rows.scalars().all()

    return {
        "totalVideos": total_videos,
        "runwayCreditsUsed": round(runway_credits, 2),
        "avgCostPerVideo": round(avg_cost, 4),
        "recentVideos": [
            {
                "id": r.id,
                "title": r.seo_title,
                "duration": r.video_duration_seconds,
                "runwayCredits": r.runway_credits_used or 0,
                "totalCost": r.total_cost_usd or 0,
                "views": r.youtube_views or 0,
                "roi": round(((r.youtube_views or 0) * 0.001) / r.total_cost_usd, 2) if (r.total_cost_usd or 0) > 0 else None,
            }
            for r in recent
        ],
    }


@router.get("/video/credits")
async def get_api_credit_balances(current_user: User = Depends(get_current_user)):
    """Return live API credit balances for Runway ML, ElevenLabs, and Gemini. Cached 5 min."""
    from utils.runwayml_client import RUNWAYML_API_VERSION

    now = _time.time()
    if _credits_cache["data"] is not None and now < _credits_cache["expires"]:
        return _credits_cache["data"]

    result: dict = {
        "runway": {"balance": None, "ok": False, "error": None},
        "elevenlabs": {"used": None, "limit": None, "remaining": None, "ok": False, "error": None},
        "gemini": {"used_today": None, "daily_quota": None, "ok": False, "error": None},
        "huggingface": {"ok": False, "model": None, "error": None},
    }

    # --- Runway ML ---
    runway_key = os.getenv("RUNWAYML_API_KEY")
    if runway_key:
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(
                    "https://api.dev.runwayml.com/v1/team",
                    headers={
                        "Authorization": f"Bearer {runway_key}",
                        "X-Runway-Version": RUNWAYML_API_VERSION,
                    },
                )
            if resp.status_code == 200:
                data = resp.json()
                balance = data.get("creditBalance") or data.get("credits") or data.get("balance")
                result["runway"] = {"balance": balance, "ok": True, "error": None}
            else:
                result["runway"]["error"] = f"HTTP {resp.status_code}"
        except Exception as exc:
            result["runway"]["error"] = str(exc)[:80]
    else:
        result["runway"]["error"] = "API key not configured"

    # --- ElevenLabs ---
    el_key = os.getenv("ELEVENLABS_API_KEY")
    if el_key:
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(
                    "https://api.elevenlabs.io/v1/user",
                    headers={"xi-api-key": el_key},
                )
            if resp.status_code == 200:
                data = resp.json()
                sub = data.get("subscription") or {}
                used = sub.get("character_count")
                limit = sub.get("character_limit")
                remaining = (limit - used) if (limit is not None and used is not None) else None
                result["elevenlabs"] = {
                    "used": used,
                    "limit": limit,
                    "remaining": remaining,
                    "ok": True,
                    "error": None,
                }
            else:
                result["elevenlabs"]["error"] = f"HTTP {resp.status_code}"
        except Exception as exc:
            result["elevenlabs"]["error"] = str(exc)[:80]
    else:
        result["elevenlabs"]["error"] = "API key not configured"

    # --- Gemini (in-process daily generation counter) ---
    try:
        from integrations.gemini_images import _gemini_used_today
        result["gemini"] = {
            "used_today": _gemini_used_today,
            "daily_quota": int(os.getenv("GEMINI_DAILY_QUOTA", "500")),
            "ok": True,
            "error": None,
        }
    except Exception as exc:
        result["gemini"]["error"] = str(exc)[:80]

    # --- HuggingFace ---
    hf_token = os.getenv("HF_TOKEN", "").strip()
    hf_model = os.getenv("HF_IMAGE_MODEL", "black-forest-labs/FLUX.1-schnell")
    if hf_token:
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(
                    "https://huggingface.co/api/whoami",
                    headers={"Authorization": f"Bearer {hf_token}"},
                )
            if resp.status_code == 200:
                data = resp.json()
                result["huggingface"] = {
                    "ok": True,
                    "model": hf_model,
                    "username": data.get("name") or data.get("fullname"),
                    "error": None,
                }
            else:
                # Fine-grained tokens may not have permission for /api/whoami,
                # but still be valid for inference. Probe router inference directly.
                try:
                    probe_headers = {
                        "Authorization": f"Bearer {hf_token}",
                        "Content-Type": "application/json",
                        "Accept": "image/png",
                    }
                    probe_payload = {
                        "inputs": "simple portrait",
                        "parameters": {
                            "width": 64,
                            "height": 64,
                            "num_inference_steps": 1,
                            "guidance_scale": 0.0,
                        },
                    }
                    async with httpx.AsyncClient(timeout=20.0) as client:
                        probe = await client.post(
                            f"https://router.huggingface.co/hf-inference/models/{hf_model}",
                            headers=probe_headers,
                            json=probe_payload,
                        )

                    if probe.status_code in (200, 503):
                        # 503 means model cold-start loading, but token auth is accepted.
                        result["huggingface"] = {
                            "ok": True,
                            "model": hf_model,
                            "username": None,
                            "error": None,
                        }
                    elif probe.status_code == 401:
                        result["huggingface"]["error"] = "HTTP 401 — token invalid for HF inference"
                    else:
                        result["huggingface"]["error"] = f"HTTP {probe.status_code} — token present but inference probe failed"
                except Exception as probe_exc:
                    result["huggingface"]["error"] = f"whoami={resp.status_code}; probe error: {str(probe_exc)[:60]}"
        except Exception as exc:
            result["huggingface"]["error"] = str(exc)[:80]
    else:
        result["huggingface"]["error"] = "HF_TOKEN not set in .env"

    _credits_cache["data"] = result
    _credits_cache["expires"] = now + 300.0  # cache 5 minutes
    return result


async def _generate_single_video_background(batch_id: str, request: GenerateVideoRequest, user_id: int):
    """Background batch worker. Keeps requests serial in-process and avoids burning credits during development unless explicitly invoked."""
    async with AsyncSessionLocal() as session:
        seed_script = (request.full_script or request.script or "")[:5000]
        # Create processing placeholder row so status endpoint can see progress.
        placeholder = Generation(
            user_id=user_id,
            input_type="video",
            input_content=seed_script,
            status="processing",
            batch_id=batch_id,
            topic=seed_script[:120],
        )
        session.add(placeholder)
        await session.commit()
        await session.refresh(placeholder)

        try:
            dry_run = is_video_dry_run_enabled()
            authoritative_script = (request.full_script or request.script or "").strip()
            parts = parse_script(full_script=authoritative_script, hook=request.hook, body=request.body, cta=request.cta)
            duration_seconds = resolve_duration_seconds(parts, request.duration_seconds)
            run_id = new_run_id()
            script_text = authoritative_script or f"{parts.hook} {parts.body} {parts.cta}"

            audio_path = None
            if dry_run:
                print("[DRY-RUN] Skipping ElevenLabs TTS in background batch generation.")
            else:
                tts_result = generate_voice(VoiceGenRequest(text=script_text))
                audio_path = tts_result.audio_file if tts_result and tts_result.audio_file else None

            scenes = build_scene_plan(parts, duration_seconds=duration_seconds)
            for scene in scenes:
                _log_scene_text_check(
                    scene_idx=getattr(scene, "idx", 0),
                    subtitle=getattr(scene, "subtitle", "") or getattr(scene, "source_text", ""),
                    on_screen_text=getattr(scene, "on_screen_text", "") or getattr(scene, "subtitle", ""),
                    visual_description=getattr(scene, "visual_description", ""),
                )
            scenes = await fetch_scene_clips(
                scenes,
                run_id=run_id,
                mode="stock" if dry_run else (request.scene_mode or "auto"),
                available_credits=float(os.getenv("RUNWAYML_AVAILABLE_CREDITS", "750")),
            )
            render_result = assemble_video(scenes, run_id=run_id, audio_path=audio_path)

            runway_credits_used = round(sum(float(getattr(s, "credits_cost", 0.0) or 0.0) for s in scenes), 2)
            if dry_run:
                runway_credits_used = 0.0
            elevenlabs_chars = 0 if dry_run else len(script_text or "")
            runway_cost = runway_credits_used * 0.01
            elevenlabs_cost = (elevenlabs_chars / 1000.0) * 0.30
            total_cost = round(runway_cost + elevenlabs_cost, 4)

            seo_metadata = None
            try:
                seo_metadata = await generate_youtube_metadata(
                    script=script_text,
                    niche=request.niche or "general",
                    duration=duration_seconds,
                )
            except Exception:
                seo_metadata = None

            placeholder.status = "success"
            placeholder.video_run_id = run_id
            placeholder.video_file = Path(render_result["video_path"]).name
            placeholder.video_duration_seconds = duration_seconds
            placeholder.video_thumbnail = render_result.get("thumbnail_path")
            placeholder.video_scenes_json = json.dumps(make_scene_response(scenes))
            placeholder.runway_credits_used = runway_credits_used
            placeholder.elevenlabs_credits_used = elevenlabs_chars
            placeholder.total_cost_usd = total_cost
            placeholder.seo_title = (seo_metadata or {}).get("title") if isinstance(seo_metadata, dict) else None
            placeholder.seo_description = (seo_metadata or {}).get("description") if isinstance(seo_metadata, dict) else None
            placeholder.seo_tags = json.dumps((seo_metadata or {}).get("tags", [])) if isinstance(seo_metadata, dict) else None
            placeholder.seo_hashtags = json.dumps((seo_metadata or {}).get("hashtags", [])) if isinstance(seo_metadata, dict) else None
            placeholder.thumbnail_text = (seo_metadata or {}).get("thumbnail_text") if isinstance(seo_metadata, dict) else None

            await session.commit()
        except Exception as exc:
            placeholder.status = "failed"
            placeholder.error_message = str(exc)[:500]
            await session.commit()


@router.post("/video/batch")
async def generate_batch_videos(
    request: BatchVideoRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    if not request.topics:
        raise HTTPException(status_code=400, detail="Please provide at least one topic")

    batch_id = str(uuid.uuid4())
    for topic in request.topics:
        task_request = GenerateVideoRequest(
            script=topic,
            duration_seconds=request.duration,
            scene_mode=request.style,
            niche=request.niche,
        )
        background_tasks.add_task(_generate_single_video_background, batch_id, task_request, current_user.id)

    return {
        "batch_id": batch_id,
        "total_videos": len(request.topics),
        "status": "queued",
    }


@router.get("/video/batch/{batch_id}")
async def get_batch_status(
    batch_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = await db.execute(
        select(Generation)
        .where(and_(Generation.batch_id == batch_id, Generation.user_id == current_user.id))
        .order_by(Generation.created_at.asc())
    )
    videos = rows.scalars().all()

    completed = sum(1 for v in videos if v.status == "success")
    failed = sum(1 for v in videos if v.status == "failed")
    processing = sum(1 for v in videos if v.status == "processing")

    return {
        "batch_id": batch_id,
        "total": len(videos),
        "completed": completed,
        "failed": failed,
        "processing": processing,
        "videos": [
            {
                "id": v.id,
                "topic": v.topic,
                "status": v.status,
                "video_url": f"/api/generate/video/download/{quote(str(v.video_file), safe='/')}" if v.video_file and v.status == "success" else None,
            }
            for v in videos
        ],
    }


@router.get("/video/download/{filename:path}")
async def download_generated_video(
    filename: str,
):
    if not filename.lower().endswith(".mp4"):
        raise HTTPException(status_code=400, detail="Invalid file.")
    if ".." in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename.")

    generated_root = Path(__file__).resolve().parents[1] / "generated_videos"
    try:
        file_path = (generated_root / filename).resolve()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid filename.")
    if generated_root.resolve() not in file_path.parents:
        raise HTTPException(status_code=400, detail="Invalid filename.")
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Video not found.")

    return FileResponse(
        path=str(file_path),
        media_type="video/mp4",
        filename=filename,
    )


@router.get("/video/thumbnail/{filename:path}")
async def download_generated_thumbnail(
    filename: str,
):
    if not filename.lower().endswith((".jpg", ".jpeg", ".png")):
        raise HTTPException(status_code=400, detail="Invalid file.")
    if ".." in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename.")

    generated_root = Path(__file__).resolve().parents[1] / "generated_videos"
    try:
        file_path = (generated_root / filename).resolve()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid filename.")
    if generated_root.resolve() not in file_path.parents:
        raise HTTPException(status_code=400, detail="Invalid filename.")
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Thumbnail not found.")

    media_type = "image/png" if filename.lower().endswith(".png") else "image/jpeg"
    return FileResponse(path=str(file_path), media_type=media_type, filename=filename)
