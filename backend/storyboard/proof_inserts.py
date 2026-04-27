from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from .formatting import documentary_frame, font
from .schema import StoryboardScene


def render_proof_image(scene: StoryboardScene, asset_path: Path, width: int, height: int, t: float, duration: float) -> Image.Image:
    return documentary_frame(asset_path, width, height, t, duration, scene.proof_label, scene.motion_profile)


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
    
    # Add Fireship-style overlays
    if scene.scene_type == "hook":
        # Add arrow icon
        draw.polygon([(width - 150, height // 2 - 50), (width - 100, height // 2), (width - 150, height // 2 + 50)], fill=accent)
    elif scene.scene_type == "proof":
        # Add checkmark
        draw.line([(width - 120, height // 2), (width - 110, height // 2 + 10), (width - 100, height // 2 - 10)], fill=accent, width=5)
    # Add code-like snippet for prompt scene
    if scene.scene_id == "prompt":
        draw.text((72, height - 200), ">>> AI.prompt(\"coffee savings\")", font=font(36, False), fill=fg)
    
    return img
