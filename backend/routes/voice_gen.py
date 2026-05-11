import os
import requests
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from utils.render_guard import require_video_render_access


def _post_process_voice(file_path: str) -> None:
    """Tighten long pauses and normalize loudness for short-form narration."""
    if os.getenv("VOICE_POSTPROCESS", "1") != "1":
        return
    if not os.path.exists(file_path):
        return

    import tempfile
    import subprocess

    target_dir = os.path.dirname(os.path.abspath(file_path)) or "."
    with tempfile.NamedTemporaryFile(suffix=".wav", dir=target_dir, delete=False) as tmp:
        tmp_out = tmp.name

    # Remove oversized pauses across the track, then normalize to short-form loudness.
    af_primary = (
        "silenceremove=start_periods=1:start_duration=0.03:start_threshold=-42dB:"
        "stop_periods=-1:stop_duration=0.20:stop_threshold=-42dB:stop_silence=0.10,"
        "loudnorm=I=-16:TP=-1.5:LRA=10"
    )
    af_fallback = (
        "silenceremove=stop_periods=-1:stop_duration=0.30:stop_threshold=-40dB,"
        "loudnorm=I=-16:TP=-1.5:LRA=11"
    )

    try:
        try:
            subprocess.run(
                ["ffmpeg", "-y", "-i", file_path, "-af", af_primary, tmp_out],
                check=True,
                timeout=90,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            subprocess.run(
                ["ffmpeg", "-y", "-i", file_path, "-af", af_fallback, tmp_out],
                check=True,
                timeout=90,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        if os.path.exists(tmp_out) and os.path.getsize(tmp_out) > 1000:
            os.replace(tmp_out, file_path)
            print(f"[TTS] Post-processed audio: {file_path}")
        else:
            if os.path.exists(tmp_out):
                os.unlink(tmp_out)
    except Exception as exc:
        if os.path.exists(tmp_out):
            os.unlink(tmp_out)
        print(f"[TTS] Voice post-processing skipped: {exc}")

router = APIRouter(prefix="/api/generate", tags=["ViralVideo"])

# Premade voices confirmed working on ElevenLabs free tier (API key with TTS permission)
_ELEVENLABS_VOICE_NAMES: dict[str, str] = {
    "pNInz6obpgDQGcFmaJgB": "adam",
    "21m00Tcm4TlvDq8ikWAM": "rachel",
    "EXAVITQu4vr4xnSDxMaL": "bella",
    "AZnzlk1XvdvUeBnXmlld": "domi",
    "MF3mGyEYCl7XYWbV9V6O": "elli",
    "ErXwobaYiN019PkySvjV": "antoni",
    "TxGEqnHWrfWFTfGW9XjX": "josh",  # library voice — requires paid tier
}

class VoiceGenRequest(BaseModel):
    text: str
    voice_id: str = "pNInz6obpgDQGcFmaJgB"  # ElevenLabs "Adam" — confirmed working on free tier
    speed: float = 1.1
    model_id: str = "eleven_multilingual_v2"
    force_free: bool = False  # True = skip ElevenLabs, use free fallbacks regardless of API key
    allow_silent: bool = False

class VoiceGenResponse(BaseModel):
    audio_url: str
    audio_file: str
    provider: str
    warning: Optional[str] = None

@router.get("/voice/test")
def test_elevenlabs_key():
    """Validate ElevenLabs API key without consuming any credits.
    A TTS-only restricted key returns 401 'missing_permissions' on /v1/user —
    that is the correct setup and is reported as OK here.
    """
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        return {"status": "no_key", "message": "ELEVENLABS_API_KEY is not set in .env"}
    try:
        # Try /v1/user first; TTS-only keys get 401 missing_permissions which means KEY IS VALID
        resp = requests.get(
            "https://api.elevenlabs.io/v1/user",
            headers={"xi-api-key": api_key},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            sub = data.get("subscription") or {}
            return {
                "status": "ok",
                "user": data.get("first_name"),
                "tier": sub.get("tier"),
                "character_limit": sub.get("character_limit"),
                "characters_used": sub.get("character_count"),
                "tts_ready": True,
            }
        if resp.status_code == 401:
            detail = resp.json().get("detail") or {}
            if detail.get("status") == "missing_permissions":
                # Key is valid and correctly restricted to Text-to-Speech only
                return {
                    "status": "ok",
                    "message": "API key is valid. Restricted to Text-to-Speech (correct setup).",
                    "tts_ready": True,
                }
        return {"status": "error", "http_code": resp.status_code, "detail": resp.text[:400]}
    except Exception as ex:
        return {"status": "exception", "error": str(ex)}


@router.post(
    "/voice",
    response_model=VoiceGenResponse,
    dependencies=[Depends(require_video_render_access)],
)
def generate_voice(req: VoiceGenRequest):
    import hashlib, tempfile, subprocess
    api_key = os.getenv("ELEVENLABS_API_KEY")
    out_dir = "assets/voice_cache"
    os.makedirs(out_dir, exist_ok=True)
    text_hash = hashlib.sha256(req.text.encode("utf-8")).hexdigest()[:16]
    fallback_errors: list[str] = []

    # Try ElevenLabs if API key is set AND force_free is not requested
    if api_key and not req.force_free:
        voice_name = _ELEVENLABS_VOICE_NAMES.get(req.voice_id, req.voice_id[:8])
        el_filename = f"elevenlabs_{voice_name}_{text_hash}.wav"
        el_file_path = os.path.join(out_dir, el_filename)
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{req.voice_id}"
        headers = {
            "xi-api-key": api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "text": req.text,
            "model_id": req.model_id,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.7,
                "style": 0.6,
                "use_speaker_boost": True,
                "speed": req.speed
            }
        }
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            if response.status_code == 200:
                # Save as wav for MoviePy compatibility
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_mp3:
                    tmp_mp3.write(response.content)
                    tmp_mp3_path = tmp_mp3.name
                try:
                    subprocess.run(
                        ["ffmpeg", "-y", "-i", tmp_mp3_path, el_file_path],
                        check=True, timeout=60,
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    )
                finally:
                    if os.path.exists(tmp_mp3_path):
                        os.unlink(tmp_mp3_path)
                _post_process_voice(el_file_path)
                print(f"[TTS] ElevenLabs audio saved: {el_file_path} ({os.path.getsize(el_file_path)} bytes)")
                return VoiceGenResponse(
                    audio_url=f"/static/voice_cache/{el_filename}",
                    audio_file=el_file_path,
                    provider="elevenlabs"
                )
            else:
                print(f"[TTS] ElevenLabs non-200 response: HTTP {response.status_code} — {response.text[:200]}")
        except Exception as e:
            print(f"[TTS] ElevenLabs failed, falling back: {e}")

    # Free fallback chain: gTTS first, then pyttsx3, then optional explicit silent fallback.
    if req.force_free:
        print("[TTS] force_free=True - using free TTS fallbacks (no ElevenLabs credits consumed)")
    free_filename = f"voice_free_{text_hash}.wav"
    free_file_path = os.path.join(out_dir, free_filename)
    gtts_mp3_path = os.path.join(out_dir, f"voice_gtts_{text_hash}.mp3")
    try:
        try:
            from gtts import gTTS
        except ImportError as ie:
            fallback_errors.append(f"gTTS unavailable: {ie}")
            raise
        gTTS(text=req.text, lang="en").save(gtts_mp3_path)
        subprocess.run(
            ["ffmpeg", "-y", "-i", gtts_mp3_path, free_file_path],
            check=True,
            timeout=60,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        _post_process_voice(free_file_path)
        size = os.path.getsize(free_file_path) if os.path.exists(free_file_path) else 0
        if not os.path.exists(free_file_path) or size < 1000:
            raise Exception("gTTS audio file missing or too small")
        print(f"[TTS] gTTS audio saved: {free_file_path} ({size} bytes)")
        return VoiceGenResponse(
            audio_url=f"/static/voice_cache/{free_filename}",
            audio_file=free_file_path,
            provider="gtts",
        )
    except Exception as e:
        fallback_errors.append(f"gTTS failed: {e}")
        print(f"[TTS] gTTS failed, trying pyttsx3: {e}")
    finally:
        try:
            if os.path.exists(gtts_mp3_path):
                os.unlink(gtts_mp3_path)
        except Exception:
            pass
    try:
        try:
            import pyttsx3
        except ImportError as ie:
            print(f"[TTS] pyttsx3 not installed: {ie}")
            fallback_errors.append(f"pyttsx3 unavailable: {ie}")
            raise HTTPException(status_code=500, detail="pyttsx3 is not installed in the backend environment.")
        engine = pyttsx3.init()
        engine.setProperty('rate', 180)
        engine.save_to_file(req.text, free_file_path)
        engine.runAndWait()
        _post_process_voice(free_file_path)
        size = os.path.getsize(free_file_path) if os.path.exists(free_file_path) else 0
        print(f"[TTS] pyttsx3 audio saved: {free_file_path} ({size} bytes)")
        if not os.path.exists(free_file_path) or size < 1000:
            raise Exception("pyttsx3 audio file missing or too small")
        return VoiceGenResponse(
            audio_url=f"/static/voice_cache/{free_filename}",
            audio_file=free_file_path,
            provider="pyttsx3"
        )
    except Exception as e:
        fallback_errors.append(f"pyttsx3 failed: {e}")
        print(f"[TTS] pyttsx3 failed: {e}")
        if req.allow_silent:
            reason = "Free TTS failed; silent fallback selected. " + " | ".join(fallback_errors[-3:])
            print(f"[TTS] {reason}")
            return VoiceGenResponse(audio_url="", audio_file="", provider="silent", warning=reason[:500])
        reason = " | ".join(fallback_errors[-4:]) or str(e)
        raise HTTPException(status_code=500, detail=f"Voice generation failed (free fallbacks): {reason}")
