import base64
import os
from pathlib import Path
from typing import Dict

from utils.openai_client import image_generate


THUMB_DIR = Path(__file__).resolve().parents[1] / "generated_videos" / "thumbnails"
THUMB_DIR.mkdir(parents=True, exist_ok=True)


def build_thumbnail_prompt(topic: str, niche: str) -> str:
    return (
        "High-contrast YouTube thumbnail, emotional trigger, bold 3-5 word text, "
        "sharp subject, dramatic lighting, viral style. "
        f"Topic: {topic}. Niche: {niche}."
    )


def generate_free_thumbnail(
    topic: str,
    niche: str = "general",
    bg_image: str | None = None,
) -> Dict[str, str]:
    """
    Zero-cost YouTube thumbnail composer (Pillow only).

    1280x720: dark gradient (or a dimmed video frame), bold 3-6 word
    headline with stroke, red accent bar. Good enough for drafts and
    free-tier users; the AI model stays available as a premium option.
    """
    from PIL import Image, ImageDraw, ImageFont, ImageFilter

    W, H = 1280, 720
    if bg_image and Path(bg_image).exists():
        bg = Image.open(bg_image).convert("RGB").resize((W, H))
        bg = bg.filter(ImageFilter.GaussianBlur(6))
        # Dim it so text pops
        dim = Image.new("RGB", (W, H), (8, 10, 18))
        bg = Image.blend(bg, dim, 0.55)
    else:
        bg = Image.new("RGB", (W, H), (10, 12, 20))
        draw_bg = ImageDraw.Draw(bg)
        # Vertical gradient navy -> near-black
        for y in range(H):
            t = y / H
            draw_bg.line(
                [(0, y), (W, y)],
                fill=(int(16 + 8 * t), int(22 + 10 * t), int(44 + 14 * t)),
            )
        # Red accent bar, left side
        draw_bg.rectangle([0, 0, 26, H], fill=(225, 29, 72))

    draw = ImageDraw.Draw(bg)

    def _font(size: int):
        for path in (
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
        ):
            if Path(path).exists():
                return ImageFont.truetype(path, size)
        return ImageFont.load_default()

    # Headline: first ~6 words, uppercased
    words = (topic or "New Video").strip().split()
    headline = " ".join(words[:6]).upper()
    # Wrap to max 2 lines
    lines: list[str] = []
    current = ""
    for w in headline.split():
        trial = f"{current} {w}".strip()
        if draw.textlength(trial, font=_font(120)) > W - 160:
            lines.append(current)
            current = w
        else:
            current = trial
    if current:
        lines.append(current)
    lines = lines[:2]

    y = H // 2 - (len(lines) * 150) // 2
    for line in lines:
        font = _font(120)
        tw = draw.textlength(line, font=font)
        x = (W - tw) / 2
        # Stroke = draw text multiple times offset in dark color
        for ox, oy in [(-4, 0), (4, 0), (0, -4), (0, 4), (-3, -3), (3, 3)]:
            draw.text((x + ox, y + oy), line, font=font, fill=(0, 0, 0))
        draw.text((x, y), line, font=font, fill=(255, 255, 255))
        y += 150

    # Niche tag, bottom-left
    tag = (niche or "general").upper()[:24]
    tag_font = _font(44)
    draw.text((70, H - 110), tag, font=tag_font, fill=(250, 204, 21))

    filename = f"thumb_free_{abs(hash(topic + niche))}.png"
    out_path = THUMB_DIR / filename
    bg.save(out_path, "PNG")
    return {
        "thumbnail_path": str(out_path),
        "thumbnail_url": f"/api/generate/thumbnail/download/{filename}",
        "prompt": f"free-composer: {headline}",
        "provider": "free",
    }


def generate_thumbnail(topic: str, niche: str, model: str = "free") -> Dict[str, str]:
    """
    Thumbnail entry point. Default is the free Pillow composer (zero cost).
    Pass model="gpt-image-1" (or another image model) for the paid AI version.
    """
    if not topic:
        raise ValueError("Topic is required for thumbnail generation.")

    if (model or "free").lower() in ("free", "pillow", "none"):
        return generate_free_thumbnail(topic, niche)

    prompt = build_thumbnail_prompt(topic, niche)
    image_b64 = image_generate(prompt=prompt, model=model, size="1024x1024")

    raw = base64.b64decode(image_b64)
    filename = f"thumb_{abs(hash(prompt))}.png"
    out_path = THUMB_DIR / filename
    out_path.write_bytes(raw)

    return {
        "thumbnail_path": str(out_path),
        "thumbnail_url": f"/api/generate/thumbnail/download/{filename}",
        "prompt": prompt,
        "provider": model,
    }
