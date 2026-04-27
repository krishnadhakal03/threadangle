from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from .schema import VideoFormat, MotionProfile


FORMAT_SPECS = {
    VideoFormat.short_9x16: {"width": 1080, "height": 1920, "fps": 30},
    VideoFormat.wide_16x9: {"width": 1920, "height": 1080, "fps": 30},
}


def format_spec(video_format: VideoFormat) -> dict[str, int]:
    return FORMAT_SPECS[video_format]


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    for name in (("arialbd.ttf" if bold else "arial.ttf"), "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()


def cover(img: Image.Image, width: int, height: int, scale_boost: float = 1.0) -> Image.Image:
    scale = max(width / img.width, height / img.height) * scale_boost
    resized = img.resize((max(1, int(img.width * scale)), max(1, int(img.height * scale))), Image.Resampling.LANCZOS)
    left = max(0, (resized.width - width) // 2)
    top = max(0, (resized.height - height) // 2)
    return resized.crop((left, top, left + width, top + height))


def contain_with_blur(img: Image.Image, width: int, height: int) -> Image.Image:
    bg = cover(img, width, height).filter(ImageFilter.GaussianBlur(18))
    scale = min(width / img.width, height / img.height)
    fg = img.resize((max(1, int(img.width * scale)), max(1, int(img.height * scale))), Image.Resampling.LANCZOS)
    bg.paste(fg, ((width - fg.width) // 2, (height - fg.height) // 2))
    return bg


def documentary_frame(path: Path, width: int, height: int, t: float, duration: float, label: str | None = None, motion_profile: MotionProfile | None = None) -> Image.Image:
    src = Image.open(path).convert("RGB")
    bg = cover(src, width, height, 1.05)
    drift_x = int(math.sin(t * 1.3) * 9)
    drift_y = int(math.cos(t * 1.1) * 12)
    if motion_profile == MotionProfile.documentary_dynamic:
        # Add pan across
        pan_progress = min(t / duration, 1.0)
        pan_x = int(pan_progress * 50)  # Pan up to 50px
        pan_y = int(pan_progress * 30)
        drift_x += pan_x
        drift_y += pan_y
    img = Image.new("RGB", (width, height), (10, 18, 30))
    img.paste(bg, (drift_x, drift_y))
    shade = Image.new("RGBA", (width, height), (0, 0, 0, 66))
    img = Image.alpha_composite(img.convert("RGBA"), shade).convert("RGB")
    if label:
        draw = ImageDraw.Draw(img)
        draw.rounded_rectangle((52, 68, width - 52, 150), radius=18, fill=(8, 18, 32))
        draw.text((78, 91), label, font=font(38, True), fill=(255, 255, 255))
    return img
