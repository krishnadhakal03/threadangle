import os
from pathlib import Path
import random
import re
import time

from .paid_provider_guard import PaidProviderBlockedError
from .runwayml_client import RunwayMLClient, RunwayMLQuotaError


def _clean_prompt_for_card(prompt: str, max_chars: int = 120) -> str:
    text = re.sub(r"\s+", " ", str(prompt or "")).strip()
    if len(text) <= max_chars:
        return text or "AI scene unavailable"
    return text[: max_chars - 1].rstrip() + "…"


def _write_local_graphic_fallback_clip(prompt: str, out_path: Path | None = None, duration: float = 4.0) -> str:
    """Create a free/local vertical fallback clip when paid AI video is blocked.

    This is deliberately simple and dependency-light. It prevents manual QA runs from
    failing just because Runway is disabled, and it proves the fallback chain is
    working without spending credits.
    """
    from PIL import Image, ImageDraw, ImageFont
    import numpy as np
    from moviepy.editor import ImageSequenceClip

    target = Path(out_path) if out_path else Path(f"local_ai_fallback_{int(time.time())}.mp4")
    target.parent.mkdir(parents=True, exist_ok=True)

    w, h = 720, 1280
    fps = 24
    frame_count = max(1, int(duration * fps))
    title = "FREE FALLBACK VISUAL"
    subtitle = _clean_prompt_for_card(prompt)

    try:
        title_font = ImageFont.truetype("arialbd.ttf", 54)
        body_font = ImageFont.truetype("arial.ttf", 34)
        small_font = ImageFont.truetype("arial.ttf", 24)
    except Exception:
        title_font = ImageFont.load_default()
        body_font = ImageFont.load_default()
        small_font = ImageFont.load_default()

    def wrap_text(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> list[str]:
        words = text.split()
        lines: list[str] = []
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip()
            bbox = draw.textbbox((0, 0), candidate, font=font)
            if bbox[2] - bbox[0] <= max_width or not current:
                current = candidate
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines[:5]

    frames = []
    for i in range(frame_count):
        progress = i / max(1, frame_count - 1)
        img = Image.new("RGB", (w, h), (7, 12, 22))
        draw = ImageDraw.Draw(img)

        # Simple animated gradient bars / motion card feel.
        glow = int(50 + 80 * progress)
        draw.rectangle([0, 0, w, h], fill=(7, 12, 22))
        draw.ellipse([-180 + int(progress * 90), 80, 540, 760], fill=(8, 70, 75))
        draw.ellipse([220, 520 - int(progress * 80), 980, 1320], fill=(36, 26, 90))
        draw.rounded_rectangle([54, 160, w - 54, h - 160], radius=42, fill=(13, 20, 35), outline=(50, 170, 180), width=3)

        draw.text((78, 220), title, font=title_font, fill=(255, 255, 255))
        draw.text((78, 292), "Runway blocked by safety guard", font=small_font, fill=(112, 255, 213))
        draw.text((78, 328), "No paid credits used", font=small_font, fill=(255, 220, 120))

        y = 450
        for line in wrap_text(draw, subtitle, body_font, w - 156):
            draw.text((78, y), line, font=body_font, fill=(245, 248, 255))
            y += 52

        # Bottom pulse bar.
        bar_w = int((w - 156) * (0.25 + 0.75 * progress))
        draw.rounded_rectangle([78, h - 250, 78 + bar_w, h - 226], radius=12, fill=(glow, 150, 255))
        draw.text((78, h - 210), "Local graphics fallback", font=small_font, fill=(210, 220, 240))

        frames.append(np.array(img))

    clip = ImageSequenceClip(frames, fps=fps)
    clip.write_videofile(
        str(target),
        fps=fps,
        codec="libx264",
        audio=False,
        preset="ultrafast",
        ffmpeg_params=["-pix_fmt", "yuv420p", "-movflags", "+faststart"],
        logger=None,
    )
    clip.close()
    return str(target)


def fetch_runwayml_clip(prompt: str, out_path: Path = None, num_frames: int = 24, seed: int = None, motion: str = "cinematic", model: str = None) -> str:
    """
    Generate a video clip using RunwayML when explicitly enabled.

    Safety behavior:
    If the backend paid-provider guard blocks Runway, create a local/free graphic
    fallback clip instead of failing the whole generation. This keeps manual QA
    no-spend runs moving and prevents accidental credit usage.

    Args:
        model: Runway model to use. Options: gen4.5, gen4_turbo, gen3a_turbo (cheaper).
               Defaults to env RUNWAYML_MODEL or gen4.5
    """
    try:
        client = RunwayMLClient(model=model)
        if seed is None:
            seed = random.randint(1, 999999)
        video_path = client.generate_video(prompt, num_frames=num_frames, seed=seed, motion=motion)
        if out_path:
            import shutil
            shutil.move(str(video_path), str(out_path))
            return str(out_path)
        return video_path
    except PaidProviderBlockedError as e:
        print(f"[RUNWAYML] Blocked by paid-provider guard; using local fallback clip instead: {e}")
        return _write_local_graphic_fallback_clip(prompt, out_path=out_path)
    except RunwayMLQuotaError as e:
        print(f"[RUNWAYML] Quota error; using local fallback clip instead: {e}")
        return _write_local_graphic_fallback_clip(prompt, out_path=out_path)
    except Exception as e:
        # If Runway is intentionally enabled, real API errors should still not kill
        # the free/manual QA path. Use fallback and log loudly.
        print(f"[RUNWAYML] Error; using local fallback clip instead: {e}")
        return _write_local_graphic_fallback_clip(prompt, out_path=out_path)
