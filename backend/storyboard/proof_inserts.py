from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from .formatting import documentary_frame, font
from .schema import StoryboardScene


def render_proof_image(scene: StoryboardScene, asset_path: Path, width: int, height: int, t: float, duration: float) -> Image.Image:
    return documentary_frame(asset_path, width, height, t, duration, scene.proof_label)


def render_generated_card(scene: StoryboardScene, width: int, height: int) -> Image.Image:
    style = scene.style or {}
    bg = tuple(style.get("bg", [255, 255, 255]))
    fg = tuple(style.get("fg", [5, 15, 30]))
    accent = tuple(style.get("accent", [16, 185, 129]))
    img = Image.new("RGB", (width, height), bg)
    draw = ImageDraw.Draw(img)
    title = style.get("headline") or scene.caption_text or scene.narration_text
    subline = style.get("subline")
    draw.multiline_text((72, height // 3), title, font=font(style.get("headline_size", 86), True), fill=fg, spacing=12)
    if subline:
        draw.text((72, height // 3 + 240), subline, font=font(46, True), fill=accent)
    return img
