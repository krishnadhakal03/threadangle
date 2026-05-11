from __future__ import annotations

import argparse
import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

from routes.voice_gen import VoiceGenRequest, generate_voice
from utils.video_pipeline import (
    ASSETS_DIR,
    assemble_video,
    build_scene_plan,
    fetch_scene_clips,
    new_run_id,
    parse_script,
)


SAMPLE_SCRIPT = """HOOK:
Most students use AI the wrong way.

BODY:
Don't ask it to do your homework.
Ask it to explain hard topics, organize your notes, and quiz you before exams.
That turns AI into a study coach instead of a shortcut.

CTA:
Save this before your next study session.
"""


def _configure_local_no_credit_env(allow_silent: bool) -> None:
    os.environ["FREE_VIDEO_ALLOW_PAID_PROVIDERS"] = "0"
    os.environ["VIDEO_GENERATION_DRY_RUN"] = "0"
    os.environ["ENABLE_SERVER_VIDEO_RENDERING"] = os.getenv("ENABLE_SERVER_VIDEO_RENDERING", "true")
    os.environ["VIDEO_SCENE_MODE"] = "stock"
    os.environ["TTS_PROVIDER"] = os.getenv("TTS_PROVIDER", "free")
    os.environ["RUNWAYML_MAX_SCENES"] = "0"
    if allow_silent:
        os.environ["VIDEO_ALLOW_SILENT_FALLBACK"] = "1"


async def _render(script_text: str, allow_silent: bool) -> dict:
    run_id = f"local_free_{new_run_id()}"
    parts = parse_script(script_text)
    scenes = build_scene_plan(parts, duration_seconds=16)

    tts = generate_voice(
        VoiceGenRequest(
            text=f"{parts.hook} {parts.body} {parts.cta}".strip(),
            force_free=True,
            allow_silent=allow_silent,
        )
    )
    audio_path = tts.audio_file if tts and tts.audio_file else None
    audio_warning = getattr(tts, "warning", None) if tts else None

    fetched = await fetch_scene_clips(
        scenes,
        run_id=run_id,
        mode="stock",
        available_credits=0.0,
        max_scenes=0,
    )
    result = assemble_video(fetched, run_id=run_id, audio_path=audio_path)
    video_path = Path(result["video_path"]).resolve()
    return {
        "run_id": run_id,
        "video_path": str(video_path),
        "thumbnail_path": result.get("thumbnail_path"),
        "audio_provider": tts.provider if tts else "none",
        "audio_warning": audio_warning,
        "exists": video_path.exists(),
        "size_bytes": video_path.stat().st_size if video_path.exists() else 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate one local Free Footage MP4 with no paid providers.")
    parser.add_argument("--script-file", default=None, help="Optional UTF-8 script file. Defaults to the Issue #81 sample.")
    parser.add_argument("--allow-silent", action="store_true", help="Allow explicit silent fallback if gTTS and pyttsx3 fail.")
    args = parser.parse_args()

    load_dotenv(Path(__file__).resolve().parent / ".env")
    _configure_local_no_credit_env(args.allow_silent)

    if not os.getenv("PEXELS_API_KEY") and not os.getenv("PIXABAY_API_KEY"):
        raise SystemExit("Set PEXELS_API_KEY or PIXABAY_API_KEY in backend/.env before running local stock render.")

    script_text = Path(args.script_file).read_text(encoding="utf-8") if args.script_file else SAMPLE_SCRIPT
    print("[LOCAL_FREE_RENDER] No-credit mode: stock footage only, free TTS only, Runway/ElevenLabs disabled.")
    print(f"[LOCAL_FREE_RENDER] Output directory: {ASSETS_DIR.resolve()}")
    result = asyncio.run(_render(script_text, allow_silent=args.allow_silent))
    print("[LOCAL_FREE_RENDER] Result:")
    for key, value in result.items():
        print(f"  {key}: {value}")
    return 0 if result["exists"] and result["size_bytes"] > 1000 else 1


if __name__ == "__main__":
    raise SystemExit(main())
