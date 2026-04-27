from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from .formatting import documentary_frame, font
from .schema import StoryboardScene


def render_proof_image(scene: StoryboardScene, asset_path: Path, width: int, height: int, t: float, duration: float) -> Image.Image:
    return documentary_frame(asset_path, width, height, t, duration, scene.proof_label, scene.motion_profile)


def render_generated_card(scene: StoryboardScene, width: int, height: int, t: float = 0.0, duration: float = 3.0) -> Image.Image:
    style = scene.style or {}
    # Modern Fireship-style colors: dark bg, bright accents
    bg_base = tuple(style.get("bg", [10, 10, 20]))  # Dark blue-black
    fg = tuple(style.get("fg", [240, 240, 250]))  # Bright white
    accent = tuple(style.get("accent", [0, 255, 150]))  # Bright green
    
    # Create gradient background
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)
    
    # Animated gradient shift
    shift = int((t / duration) * 100) % 100
    for y in range(height):
        r = min(255, bg_base[0] + shift + y // 10)
        g = min(255, bg_base[1] + shift // 2)
        b = min(255, bg_base[2] + (y + shift) // 20)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    
    # Add particle effects
    import random
    random.seed(int(t * 10))  # Consistent per frame
    for _ in range(20):
        x = random.randint(0, width)
        y = random.randint(0, height)
        size = random.randint(1, 3)
        draw.ellipse([x, y, x + size, y + size], fill=accent)
    
    title = style.get("headline") or scene.caption_text or scene.narration_text
    subline = style.get("subline")
    
    # Add text shadow for depth
    shadow_offset = 2
    title_x, title_y = 72, height // 3
    draw.multiline_text((title_x + shadow_offset, title_y + shadow_offset), title, font=font(style.get("headline_size", 86), True), fill=(0, 0, 0), spacing=12)
    draw.multiline_text((title_x, title_y), title, font=font(style.get("headline_size", 86), True), fill=fg, spacing=12)
    
    if subline:
        sub_x, sub_y = 72, height // 3 + 240
        draw.text((sub_x + shadow_offset, sub_y + shadow_offset), subline, font=font(46, True), fill=(0, 0, 0))
        draw.text((sub_x, sub_y), subline, font=font(46, True), fill=accent)
    
    # Scene-specific enhancements
    if scene.scene_type == "hook":
        # Animated arrow
        arrow_progress = (t % 1.0) * 2 - 1  # Oscillate
        arrow_x = width - 150 + int(arrow_progress * 20)
        draw.polygon([(arrow_x, height // 2 - 50), (arrow_x + 50, height // 2), (arrow_x, height // 2 + 50)], fill=accent)
        
    elif scene.scene_type == "proof":
        # Animated checkmark
        check_progress = min(1.0, t / duration)
        check_x = width - 120
        check_y = height // 2
        if check_progress > 0.3:
            draw.line([(check_x, check_y), (check_x + 10, check_y + 10)], fill=accent, width=5)
        if check_progress > 0.6:
            draw.line([(check_x + 10, check_y + 10), (check_x + 20, check_y - 10)], fill=accent, width=5)
    
    # Terminal-style prompt scene
    if scene.scene_id == "prompt":
        # Terminal background
        term_x, term_y = 72, height - 300
        term_w, term_h = width - 144, 200
        draw.rectangle([term_x, term_y, term_x + term_w, term_y + term_h], fill=(0, 0, 0), outline=accent)
        
        # Typing animation
        prompt_text = ">>> AI.prompt(\"I spend $5 a day on coffee. Compare that with brewing at home and show me what I could save each month and each year.\")"
        chars_to_show = int((t / duration) * len(prompt_text))
        visible_text = prompt_text[:chars_to_show]
        draw.text((term_x + 20, term_y + 20), visible_text, font=font(32, False), fill=fg)
        
        # Cursor blink
        if int(t * 2) % 2 == 0:
            cursor_x = term_x + 20 + draw.textbbox((0, 0), visible_text, font=font(32, False))[2]
            draw.line([cursor_x, term_y + 15, cursor_x, term_y + 45], fill=accent, width=2)
    
    return img
