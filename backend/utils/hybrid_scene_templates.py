"""Frame-level scene templates for the Hybrid Motion Renderer.

The templates draw directly onto OpenCV/PIL canvases. They intentionally avoid
MoviePy TextClip and any ImageMagick dependency.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any, Callable

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


Color = tuple[int, int, int]


@dataclass(frozen=True)
class SafeArea:
    left: int
    top: int
    right: int
    bottom: int


def safe_area(width: int, height: int) -> SafeArea:
    return SafeArea(
        left=int(width * 0.075),
        top=int(height * 0.075),
        right=int(width * 0.925),
        bottom=int(height * 0.885),
    )


def pil_font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size=size)
        except Exception:
            continue
    return ImageFont.load_default()


def to_pil(canvas: np.ndarray) -> Image.Image:
    return Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))


def to_cv(image: Image.Image) -> np.ndarray:
    return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)


def ease_out(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 1.0 - (1.0 - t) ** 3


def ease_in_out(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 0.5 - 0.5 * math.cos(math.pi * t)


def draw_rounded_rect(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], radius: int, fill: Color, outline: Color | None = None, width: int = 1) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    if not text:
        return 0, 0
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0], box[3] - box[1]


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int, max_lines: int = 4) -> list[str]:
    words = re.findall(r"\S+", text or "")
    lines: list[str] = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip()
        if text_size(draw, trial, font)[0] <= max_width:
            current = trial
            continue
        if current:
            lines.append(current)
        current = word
        if len(lines) >= max_lines:
            break
    if current and len(lines) < max_lines:
        lines.append(current)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
    return lines


def draw_text_block(
    image: Image.Image,
    text: str,
    box: tuple[int, int, int, int],
    *,
    font_size: int = 78,
    fill: Color = (255, 255, 255),
    accent: Color = (72, 211, 137),
    align: str = "left",
    max_lines: int = 4,
    line_gap: int = 12,
) -> dict[str, Any]:
    draw = ImageDraw.Draw(image)
    x1, y1, x2, y2 = box
    font = pil_font(font_size, bold=True)
    lines = wrap_text(draw, text, font, x2 - x1, max_lines=max_lines)
    while lines and (len(lines) * font_size + (len(lines) - 1) * line_gap) > (y2 - y1) and font_size > 30:
        font_size -= 4
        font = pil_font(font_size, bold=True)
        lines = wrap_text(draw, text, font, x2 - x1, max_lines=max_lines)

    total_h = len(lines) * font_size + max(0, len(lines) - 1) * line_gap
    y = y1 + max(0, ((y2 - y1) - total_h) // 2)
    boxes = []
    for idx, line in enumerate(lines):
        w, h = text_size(draw, line, font)
        x = x1 if align == "left" else x1 + max(0, (x2 - x1 - w) // 2)
        color = accent if idx == len(lines) - 1 and len(lines) > 1 else fill
        draw.text((x + 3, y + 3), line, font=font, fill=(0, 0, 0))
        draw.text((x, y), line, font=font, fill=color)
        boxes.append((x, y, x + w, y + h))
        y += font_size + line_gap
    return {"lines": lines, "boxes": boxes, "cropped": y > y2 + line_gap}


def animated_background(canvas: np.ndarray, progress: float, palette: tuple[Color, Color] = ((8, 16, 28), (15, 62, 70))) -> None:
    h, w = canvas.shape[:2]
    base = np.zeros((h, w, 3), dtype=np.uint8)
    c1 = np.array(palette[0][::-1], dtype=np.float32)
    c2 = np.array(palette[1][::-1], dtype=np.float32)
    yy = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    grad = c1 * (1 - yy) + c2 * yy
    base[:] = grad[:, None, :]
    for i in range(5):
        cx = int((w * (0.15 + 0.2 * i) + math.sin(progress * math.pi * 2 + i) * 70) % w)
        cy = int(h * (0.18 + 0.14 * i))
        color = tuple(int(v) for v in ((55 + i * 20), (120 + i * 14), (150 + i * 8)))
        cv2.circle(base, (cx, cy), 80 + i * 18, color[::-1], -1, lineType=cv2.LINE_AA)
    blurred = cv2.GaussianBlur(base, (0, 0), 55)
    canvas[:] = cv2.addWeighted(canvas, 0.15, blurred, 0.85, 0)


def draw_caption_band(canvas: np.ndarray, caption: str, reserved_boxes: list[tuple[int, int, int, int]] | None = None) -> dict[str, Any]:
    if not caption:
        return {"caption": "", "boxes": [], "word_count": 0, "overlaps_key_number": False}
    h, w = canvas.shape[:2]
    image = to_pil(canvas)
    draw = ImageDraw.Draw(image)
    area = safe_area(w, h)
    words = re.findall(r"\S+", caption)[:4]
    text = " ".join(words)
    font = pil_font(48, bold=True)
    tw, th = text_size(draw, text, font)
    pad_x, pad_y = 34, 18
    x1 = max(area.left, (w - tw) // 2 - pad_x)
    x2 = min(area.right, x1 + tw + pad_x * 2)
    x1 = max(area.left, x2 - tw - pad_x * 2)
    y2 = area.bottom
    y1 = y2 - th - pad_y * 2

    overlaps = False
    for box in reserved_boxes or []:
        bx1, by1, bx2, by2 = box
        if not (x2 < bx1 or x1 > bx2 or y2 < by1 or y1 > by2):
            overlaps = True
            y2 = max(area.top + th + pad_y * 2, by1 - 24)
            y1 = y2 - th - pad_y * 2
    if overlaps:
        overlaps = any(
            not (x2 < bx1 or x1 > bx2 or y2 < by1 or y1 > by2)
            for bx1, by1, bx2, by2 in (reserved_boxes or [])
        )

    draw_rounded_rect(draw, (x1, y1, x2, y2), 26, (10, 13, 18), (255, 255, 255), 2)
    draw.text((x1 + pad_x, y1 + pad_y - 3), text, font=font, fill=(255, 255, 255))
    canvas[:] = to_cv(image)
    return {"caption": text, "boxes": [(x1, y1, x2, y2)], "word_count": len(words), "overlaps_key_number": overlaps}


def _scene_text(scene_config: dict[str, Any], *keys: str, default: str = "") -> str:
    for key in keys:
        val = str(scene_config.get(key) or "").strip()
        if val:
            return val
    return default


def hook_footage_overlay(frame_idx: int, scene_progress: float, canvas: np.ndarray, scene_config: dict[str, Any]) -> dict[str, Any]:
    h, w = canvas.shape[:2]
    if not scene_config.get("has_real_background"):
        animated_background(canvas, scene_progress, ((10, 17, 30), (31, 74, 82)))
    punch = 1.0 + 0.055 * (1.0 - ease_out(scene_progress))
    if punch > 1.002:
        resized = cv2.resize(canvas, None, fx=punch, fy=punch, interpolation=cv2.INTER_LINEAR)
        y = (resized.shape[0] - h) // 2
        x = (resized.shape[1] - w) // 2
        canvas[:] = resized[y:y + h, x:x + w]
    image = to_pil(canvas)
    draw = ImageDraw.Draw(image, "RGBA")
    draw.rectangle((0, 0, w, h), fill=(0, 0, 0, 82))
    area = safe_area(w, h)
    report = draw_text_block(
        image,
        _scene_text(scene_config, "headline", "caption_text", "source_text", default="Small habits get expensive"),
        (area.left, int(h * 0.22), area.right, int(h * 0.58)),
        font_size=88,
        accent=(115, 231, 185),
        max_lines=4,
    )
    canvas[:] = to_cv(image)
    return {"template": "hook_footage_overlay", "text_boxes": report["boxes"], "cropped": report["cropped"], "motion_score": 0.85}


def money_shock_math(frame_idx: int, scene_progress: float, canvas: np.ndarray, scene_config: dict[str, Any]) -> dict[str, Any]:
    h, w = canvas.shape[:2]
    animated_background(canvas, scene_progress, ((30, 20, 18), (76, 42, 30)))
    image = to_pil(canvas)
    draw = ImageDraw.Draw(image, "RGBA")
    area = safe_area(w, h)
    card = (area.left, int(h * 0.16), area.right, int(h * 0.70))
    draw_rounded_rect(draw, card, 38, (248, 250, 252), (226, 232, 240), 3)
    draw.line((card[0] + 50, card[1] + 170, card[2] - 50, card[1] + 170), fill=(210, 220, 230), width=4)
    font_label = pil_font(46, bold=True)
    font_num = pil_font(122, bold=True)
    draw.text((card[0] + 60, card[1] + 58), "DAILY COFFEE", font=font_label, fill=(58, 69, 83))
    count = int(150 * ease_out(scene_progress))
    number = f"${count}/mo"
    nw, nh = text_size(draw, number, font_num)
    num_box = ((w - nw) // 2, card[1] + 225, (w + nw) // 2, card[1] + 225 + nh)
    draw.text((num_box[0], num_box[1]), number, font=font_num, fill=(184, 48, 44))
    formula = _scene_text(scene_config, "formula", default="$5 x 30 = $150/mo")
    font_formula = pil_font(58, bold=True)
    fw, _ = text_size(draw, formula, font_formula)
    draw.text(((w - fw) // 2, card[1] + 430), formula, font=font_formula, fill=(20, 26, 36))
    canvas[:] = to_cv(image)
    return {"template": "money_shock_math", "key_number_boxes": [num_box], "cropped": False, "motion_score": 0.9}


def ai_prompt_mock(frame_idx: int, scene_progress: float, canvas: np.ndarray, scene_config: dict[str, Any]) -> dict[str, Any]:
    h, w = canvas.shape[:2]
    animated_background(canvas, scene_progress, ((8, 15, 28), (25, 50, 70)))
    image = to_pil(canvas)
    draw = ImageDraw.Draw(image, "RGBA")
    area = safe_area(w, h)
    browser = (area.left, int(h * 0.16), area.right, int(h * 0.78))
    draw_rounded_rect(draw, browser, 30, (246, 248, 252), (208, 216, 226), 3)
    draw_rounded_rect(draw, (browser[0] + 28, browser[1] + 28, browser[2] - 28, browser[1] + 90), 18, (226, 232, 240))
    for i, c in enumerate([(239, 68, 68), (245, 158, 11), (34, 197, 94)]):
        draw.ellipse((browser[0] + 48 + i * 42, browser[1] + 49, browser[0] + 72 + i * 42, browser[1] + 73), fill=c)
    prompt = _scene_text(scene_config, "prompt", "caption_text", default="Compare coffee shop runs with brewing at home.")
    typed_len = int(len(prompt) * min(1.0, scene_progress / 0.48))
    typed = prompt[:typed_len]
    font = pil_font(42, bold=False)
    prompt_box = (browser[0] + 58, browser[1] + 140, browser[2] - 58, browser[1] + 350)
    draw_rounded_rect(draw, prompt_box, 24, (16, 24, 39), None, 1)
    draw_text_block(image, typed, (prompt_box[0] + 34, prompt_box[1] + 22, prompt_box[2] - 34, prompt_box[3] - 22), font_size=39, fill=(241, 245, 249), max_lines=3)
    if scene_progress > 0.50:
        response_alpha = int(255 * ease_out((scene_progress - 0.50) / 0.50))
        resp_box = (browser[0] + 58, browser[1] + 390, browser[2] - 58, browser[1] + 690)
        draw_rounded_rect(draw, resp_box, 24, (236, 253, 245), (86, 196, 150), 3)
        response = _scene_text(scene_config, "response", default="Coffee shop: $150/mo\nHome brew: about $20/mo")
        font_resp = pil_font(49, bold=True)
        y = resp_box[1] + 52
        for line in response.splitlines():
            draw.text((resp_box[0] + 42, y), line, font=font_resp, fill=(8, 92, 69, response_alpha))
            y += 82
    if int(frame_idx / 8) % 2 == 0:
        draw.rectangle((prompt_box[0] + 42 + text_size(draw, typed[-18:], font)[0], prompt_box[1] + 50, prompt_box[0] + 50 + text_size(draw, typed[-18:], font)[0], prompt_box[1] + 96), fill=(255, 255, 255))
    canvas[:] = to_cv(image)
    return {"template": "ai_prompt_mock", "text_boxes": [browser], "cropped": False, "motion_score": 0.88}


def comparison_split(frame_idx: int, scene_progress: float, canvas: np.ndarray, scene_config: dict[str, Any]) -> dict[str, Any]:
    h, w = canvas.shape[:2]
    animated_background(canvas, scene_progress, ((15, 22, 34), (21, 68, 54)))
    image = to_pil(canvas)
    draw = ImageDraw.Draw(image, "RGBA")
    area = safe_area(w, h)
    gap = 28
    col_w = (area.right - area.left - gap) // 2
    slide = int((1.0 - ease_out(scene_progress)) * 220)
    left = (area.left - slide, int(h * 0.22), area.left + col_w - slide, int(h * 0.70))
    right = (area.left + col_w + gap + slide, int(h * 0.22), area.right + slide, int(h * 0.70))
    draw_rounded_rect(draw, left, 34, (255, 247, 237), (251, 146, 60), 4)
    draw_rounded_rect(draw, right, 34, (236, 253, 245), (52, 211, 153), 4)
    title_font = pil_font(48, bold=True)
    num_font = pil_font(92, bold=True)
    draw.text((left[0] + 42, left[1] + 52), "COFFEE SHOP", font=title_font, fill=(154, 52, 18))
    draw.text((right[0] + 42, right[1] + 52), "HOME BREW", font=title_font, fill=(6, 95, 70))
    draw.text((left[0] + 52, left[1] + 220), "$150", font=num_font, fill=(194, 65, 12))
    draw.text((right[0] + 52, right[1] + 220), "$20", font=num_font, fill=(5, 150, 105))
    draw.text((left[0] + 58, left[1] + 330), "per month", font=pil_font(42), fill=(120, 53, 15))
    draw.text((right[0] + 58, right[1] + 330), "per month", font=pil_font(42), fill=(6, 78, 59))
    canvas[:] = to_cv(image)
    return {"template": "comparison_split", "key_number_boxes": [left, right], "cropped": False, "motion_score": 0.8}


def payoff_number_reveal(frame_idx: int, scene_progress: float, canvas: np.ndarray, scene_config: dict[str, Any]) -> dict[str, Any]:
    h, w = canvas.shape[:2]
    animated_background(canvas, scene_progress, ((8, 18, 30), (12, 84, 73)))
    for i in range(36):
        ang = (i / 36.0) * math.tau + scene_progress * 1.4
        rad = 250 + 170 * math.sin(scene_progress * math.pi + i)
        cx = int(w / 2 + math.cos(ang) * rad)
        cy = int(h * 0.42 + math.sin(ang) * rad * 0.55)
        cv2.circle(canvas, (cx, cy), 4, (130, 245, 210), -1, lineType=cv2.LINE_AA)
    image = to_pil(canvas)
    draw = ImageDraw.Draw(image, "RGBA")
    count = int(1500 * ease_out(scene_progress))
    number = _scene_text(scene_config, "number", default=f"${count:,}")
    if "{count}" in number:
        number = number.format(count=f"{count:,}")
    font = pil_font(150, bold=True)
    nw, nh = text_size(draw, number, font)
    num_box = ((w - nw) // 2, int(h * 0.31), (w + nw) // 2, int(h * 0.31) + nh)
    draw.text((num_box[0] + 5, num_box[1] + 6), number, font=font, fill=(0, 0, 0, 180))
    draw.text((num_box[0], num_box[1]), number, font=font, fill=(167, 243, 208))
    sub = _scene_text(scene_config, "subline", default="a year from one small habit")
    sw, _ = text_size(draw, sub, pil_font(52, bold=True))
    draw.text(((w - sw) // 2, num_box[3] + 34), sub, font=pil_font(52, bold=True), fill=(255, 255, 255))
    canvas[:] = to_cv(image)
    return {"template": "payoff_number_reveal", "key_number_boxes": [num_box], "cropped": False, "motion_score": 0.92, "number_reveal": True}


def cta_callback(frame_idx: int, scene_progress: float, canvas: np.ndarray, scene_config: dict[str, Any]) -> dict[str, Any]:
    h, w = canvas.shape[:2]
    animated_background(canvas, scene_progress, ((11, 18, 32), (38, 68, 62)))
    image = to_pil(canvas)
    draw = ImageDraw.Draw(image, "RGBA")
    area = safe_area(w, h)
    draw_rounded_rect(draw, (area.left, int(h * 0.22), area.right, int(h * 0.68)), 42, (10, 14, 22), (115, 231, 185), 4)
    draw.text((area.left + 52, int(h * 0.27)), "REMEMBER THE COFFEE?", font=pil_font(48, bold=True), fill=(148, 163, 184))
    report = draw_text_block(
        image,
        _scene_text(scene_config, "headline", "caption_text", default="Comment coffee for the prompt"),
        (area.left + 52, int(h * 0.36), area.right - 52, int(h * 0.62)),
        font_size=max(38, int(w * 0.072)),
        accent=(115, 231, 185),
        max_lines=3,
        align="center",
    )
    canvas[:] = to_cv(image)
    return {"template": "cta_callback", "text_boxes": report["boxes"], "cropped": report["cropped"], "motion_score": 0.78}


TEMPLATES: dict[str, Callable[[int, float, np.ndarray, dict[str, Any]], dict[str, Any]]] = {
    "hook_footage_overlay": hook_footage_overlay,
    "money_shock_math": money_shock_math,
    "ai_prompt_mock": ai_prompt_mock,
    "comparison_split": comparison_split,
    "payoff_number_reveal": payoff_number_reveal,
    "cta_callback": cta_callback,
}


def get_template(name: str) -> Callable[[int, float, np.ndarray, dict[str, Any]], dict[str, Any]]:
    return TEMPLATES.get(name) or hook_footage_overlay
