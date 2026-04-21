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


def generate_thumbnail(topic: str, niche: str, model: str = "gpt-image-1") -> Dict[str, str]:
    if not topic:
        raise ValueError("Topic is required for thumbnail generation.")

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
    }
