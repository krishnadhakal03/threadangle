"""Frame-level scene templates for the Hybrid Motion Renderer.

The templates draw directly onto OpenCV/PIL canvases. They intentionally avoid
MoviePy TextClip and any ImageMagick dependency.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Callable

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


Color = tuple[int, int, int]
_ANIMATED_BG_CACHE: dict[tuple[int, int, tuple[Color, Color]], np.ndarray] = {}


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


@lru_cache(maxsize=96)
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


def to_cv_rgb(image: Image.Image) -> np.ndarray:
    return to_cv(image.convert("RGB"))


def scene_cache(scene_config: dict[str, Any]) -> dict[str, Any]:
    cache = scene_config.get("_template_cache")
    return cache if isinstance(cache, dict) else {}


def paste_overlay_clipped(image: Image.Image, overlay: Image.Image, xy: tuple[int, int]) -> None:
    x, y = xy
    src_x1 = max(0, -x)
    src_y1 = max(0, -y)
    dst_x = max(0, x)
    dst_y = max(0, y)
    src_x2 = min(overlay.width, image.width - dst_x + src_x1)
    src_y2 = min(overlay.height, image.height - dst_y + src_y1)
    if src_x2 <= src_x1 or src_y2 <= src_y1:
        return
    image.alpha_composite(overlay.crop((src_x1, src_y1, src_x2, src_y2)), (dst_x, dst_y))


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


def fit_font(draw: ImageDraw.ImageDraw, text: str, size: int, max_width: int, *, min_size: int = 24, bold: bool = True) -> ImageFont.ImageFont:
    font = pil_font(size, bold=bold)
    while text_size(draw, text, font)[0] > max_width and size > min_size:
        size -= 3
        font = pil_font(size, bold=bold)
    return font


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
    render_scale = 0.35
    bw = max(32, int(w * render_scale))
    bh = max(48, int(h * render_scale))
    cache_key = (bw, bh, palette)
    cached = _ANIMATED_BG_CACHE.get(cache_key)
    if cached is None:
        base = np.zeros((bh, bw, 3), dtype=np.uint8)
        c1 = np.array(palette[0][::-1], dtype=np.float32)
        c2 = np.array(palette[1][::-1], dtype=np.float32)
        yy = np.linspace(0, 1, bh, dtype=np.float32)[:, None]
        grad = c1 * (1 - yy) + c2 * yy
        base[:] = grad[:, None, :]
        _ANIMATED_BG_CACHE[cache_key] = base
    else:
        base = cached.copy()
    for i in range(5):
        cx = int((bw * (0.15 + 0.2 * i) + math.sin(progress * math.pi * 2 + i) * 70 * render_scale) % bw)
        cy = int(bh * (0.18 + 0.14 * i))
        color = tuple(int(v) for v in ((55 + i * 20), (120 + i * 14), (150 + i * 8)))
        cv2.circle(base, (cx, cy), max(4, int((80 + i * 18) * render_scale)), color[::-1], -1, lineType=cv2.LINE_AA)
    blurred = cv2.GaussianBlur(base, (0, 0), max(1, 55 * render_scale))
    if blurred.shape[0] != h or blurred.shape[1] != w:
        blurred = cv2.resize(blurred, (w, h), interpolation=cv2.INTER_LINEAR)
    canvas[:] = cv2.addWeighted(canvas, 0.15, blurred, 0.85, 0)


def draw_caption_band(
    canvas: np.ndarray,
    caption: str,
    reserved_boxes: list[tuple[int, int, int, int]] | None = None,
    caption_style: dict[str, Any] | None = None,
    animation_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not caption:
        return {"caption": "", "boxes": [], "word_count": 0, "overlaps_key_number": False, "emphasis_words": []}
    caption = re.sub(r"(?i)\b(?:hook|body|cta)\s*:\s*", "", str(caption or "")).strip()
    if not caption:
        return {"caption": "", "boxes": [], "word_count": 0, "overlaps_key_number": False, "emphasis_words": []}
    h, w = canvas.shape[:2]
    image = to_pil(canvas)
    draw = ImageDraw.Draw(image)
    area = safe_area(w, h)
    max_words = int((caption_style or {}).get("max_words_per_chunk", 4) or 4)
    words = re.findall(r"\S+", caption)[:max(1, max_words)]
    text = " ".join(words)
    scale = float((animation_state or {}).get("scale", 1.0) or 1.0)
    font_size = int(round(62 * max(0.9, min(1.18, scale))))
    font = pil_font(font_size, bold=True)
    tw, th = text_size(draw, text, font)
    while tw > (area.right - area.left) - 16 and font_size > 38:
        font_size -= 3
        font = pil_font(font_size, bold=True)
        tw, th = text_size(draw, text, font)
    pad_x, pad_y = 34, 18
    x1 = max(area.left, (w - tw) // 2 - pad_x)
    x2 = min(area.right, x1 + tw + pad_x * 2)
    x1 = max(area.left, x2 - tw - pad_x * 2)

    box_h = th + pad_y * 2
    candidates = [
        area.bottom - box_h,
        int(h * 0.72),
        int(h * 0.12),
        int(h * 0.52),
    ]

    def overlaps_reserved(candidate: tuple[int, int, int, int]) -> bool:
        cx1, cy1, cx2, cy2 = candidate
        return any(
            not (cx2 < bx1 or cx1 > bx2 or cy2 < by1 or cy1 > by2)
            for bx1, by1, bx2, by2 in (reserved_boxes or [])
        )

    selected = None
    for y1_try in candidates:
        y1_try = max(area.top, min(area.bottom - box_h, y1_try))
        candidate = (x1, y1_try, x2, y1_try + box_h)
        if not overlaps_reserved(candidate):
            selected = candidate
            break
    if selected is None:
        y1_try = max(area.top, min(area.bottom - box_h, candidates[0]))
        selected = (x1, y1_try, x2, y1_try + box_h)
    x1, y1, x2, y2 = selected
    overlaps = overlaps_reserved(selected)

    draw_rounded_rect(draw, (x1, y1, x2, y2), 26, (10, 13, 18), (255, 255, 255), 2)
    emphasis_words: list[str] = []
    action_words = {"save", "saved", "compare", "comment", "send", "prompt", "audit", "coffee"}
    action_words.update(str(word).lower() for word in (caption_style or {}).get("emphasis_keywords", []) or [])
    highlight_style = str((caption_style or {}).get("highlight_style") or "")
    x = x1 + pad_x
    y = y1 + pad_y - 3
    space_w, _ = text_size(draw, " ", font)
    for word in words:
        clean = re.sub(r"[^A-Za-z0-9$]", "", word).lower()
        emphasized = bool(re.search(r"[$0-9]", word)) or clean in action_words
        if emphasized and highlight_style == "yellow_pop":
            fill = (255, 222, 89)
        else:
            fill = (115, 231, 185) if emphasized else (255, 255, 255)
        draw.text((x, y), word, font=font, fill=fill)
        if emphasized:
            emphasis_words.append(word)
        ww, _ = text_size(draw, word, font)
        x += ww + space_w
    canvas[:] = to_cv(image)
    return {
        "caption": text,
        "boxes": [(x1, y1, x2, y2)],
        "word_count": len(words),
        "overlaps_key_number": overlaps,
        "emphasis_words": emphasis_words,
        "caption_style": (caption_style or {}).get("id"),
        "bounce_phase": (animation_state or {}).get("phase"),
        "animation_scale": (animation_state or {}).get("scale", 1.0),
    }


def _scene_text(scene_config: dict[str, Any], *keys: str, default: str = "") -> str:
    for key in keys:
        val = str(scene_config.get(key) or "").strip()
        if val:
            return val
    return default


def _draw_paper_texture(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], color: Color = (252, 248, 238)) -> None:
    x1, y1, x2, y2 = box
    draw_rounded_rect(draw, box, max(18, int((x2 - x1) * 0.045)), color, (230, 222, 205), max(1, int((x2 - x1) * 0.006)))
    for i in range(20):
        y = y1 + int((i + 1) * (y2 - y1) / 22)
        alpha = 22 + (i % 3) * 8
        draw.line((x1 + 18, y, x2 - 18, y + (i % 2)), fill=(174, 160, 135, alpha), width=1)
    for i in range(34):
        x = x1 + 16 + (i * 47) % max(1, (x2 - x1 - 32))
        y = y1 + 18 + (i * 71) % max(1, (y2 - y1 - 36))
        draw.ellipse((x, y, x + 2, y + 1), fill=(126, 112, 91, 35))


def _draw_realistic_grocery_props(image: Image.Image, area: SafeArea, progress: float) -> None:
    draw = ImageDraw.Draw(image, "RGBA")
    w, h = image.size
    table_y = int(h * 0.74)
    draw.rectangle((0, table_y, w, h), fill=(52, 42, 34, 210))
    for i in range(8):
        x = int(w * (i / 7))
        draw.line((x, table_y, x - int(w * 0.12), h), fill=(78, 62, 48, 120), width=max(1, int(w * 0.004)))

    bag_x = area.left + int(w * 0.03 * math.sin(progress * math.tau))
    bag_y = int(h * 0.46)
    bag_w = int(w * 0.36)
    bag_h = int(h * 0.33)
    draw.polygon(
        [(bag_x, bag_y + bag_h), (bag_x + int(bag_w * 0.12), bag_y + int(bag_h * 0.12)), (bag_x + int(bag_w * 0.92), bag_y), (bag_x + bag_w, bag_y + bag_h)],
        fill=(190, 142, 86, 245),
    )
    draw.polygon(
        [(bag_x + int(bag_w * 0.12), bag_y + int(bag_h * 0.12)), (bag_x + int(bag_w * 0.24), bag_y + int(bag_h * 0.04)), (bag_x + int(bag_w * 0.92), bag_y), (bag_x + int(bag_w * 0.76), bag_y + int(bag_h * 0.13))],
        fill=(226, 178, 108, 235),
    )
    draw.line((bag_x + int(bag_w * 0.28), bag_y + int(bag_h * 0.05), bag_x + int(bag_w * 0.38), bag_y - int(h * 0.04), bag_x + int(bag_w * 0.55), bag_y + int(bag_h * 0.04)), fill=(127, 89, 52, 220), width=max(2, int(w * 0.009)))

    apple = (bag_x + int(bag_w * 0.18), bag_y - int(h * 0.02), bag_x + int(bag_w * 0.36), bag_y + int(h * 0.08))
    draw.ellipse(apple, fill=(181, 44, 48, 245))
    draw.ellipse((apple[0] + int(w * 0.025), apple[1] + int(h * 0.015), apple[0] + int(w * 0.055), apple[1] + int(h * 0.035)), fill=(250, 226, 210, 110))
    draw.ellipse((bag_x + int(bag_w * 0.46), bag_y - int(h * 0.04), bag_x + int(bag_w * 0.72), bag_y + int(h * 0.055)), fill=(42, 126, 75, 240))
    draw.rectangle((bag_x + int(bag_w * 0.62), bag_y - int(h * 0.065), bag_x + int(bag_w * 0.82), bag_y - int(h * 0.01)), fill=(38, 116, 72, 230))

    cart_x = area.right - int(w * 0.38)
    cart_y = int(h * 0.61)
    cart_w = int(w * 0.30)
    cart_h = int(h * 0.13)
    draw.line((cart_x, cart_y, cart_x + cart_w, cart_y + int(cart_h * 0.18)), fill=(190, 198, 205, 230), width=max(2, int(w * 0.010)))
    draw.line((cart_x + int(cart_w * 0.08), cart_y + cart_h, cart_x + cart_w, cart_y + int(cart_h * 0.18)), fill=(190, 198, 205, 230), width=max(2, int(w * 0.010)))
    for i in range(5):
        x = cart_x + int(cart_w * (0.16 + i * 0.15))
        draw.line((x, cart_y + int(cart_h * 0.08), x - int(w * 0.02), cart_y + cart_h), fill=(220, 226, 232, 160), width=max(1, int(w * 0.004)))
    draw.line((cart_x + cart_w, cart_y + int(cart_h * 0.18), cart_x + cart_w + int(w * 0.07), cart_y - int(h * 0.035)), fill=(190, 198, 205, 230), width=max(2, int(w * 0.01)))
    for cx in (cart_x + int(cart_w * 0.18), cart_x + int(cart_w * 0.84)):
        draw.ellipse((cx, cart_y + cart_h, cx + int(w * 0.05), cart_y + cart_h + int(w * 0.05)), fill=(24, 31, 42, 230))


def grocery_receipt_hook(frame_idx: int, scene_progress: float, canvas: np.ndarray, scene_config: dict[str, Any]) -> dict[str, Any]:
    h, w = canvas.shape[:2]
    if scene_config.get("has_real_background"):
        image = to_pil(canvas).convert("RGBA")
        draw = ImageDraw.Draw(image, "RGBA")
        area = safe_area(w, h)
        loss_number = _scene_text(scene_config, "price_text", "hook_number", default="$2,080/year")
        headline = _scene_text(scene_config, "headline", default="I found a grocery leak")
        draw_rounded_rect(draw, (area.left, int(h * 0.12), area.right, int(h * 0.31)), 26, (0, 0, 0, 150), None, 1)
        number_font = fit_font(draw, loss_number, max(54, int(w * 0.15)), area.right - area.left - int(w * 0.10), min_size=max(34, int(w * 0.09)), bold=True)
        nw, nh = text_size(draw, loss_number, number_font)
        number_box = (area.left + int(w * 0.05), int(h * 0.145), area.right - int(w * 0.05), int(h * 0.145) + nh + int(h * 0.035))
        draw.text((number_box[0] + max(0, (number_box[2] - number_box[0] - nw) // 2), number_box[1]), loss_number, font=number_font, fill=(255, 245, 200))
        report = draw_text_block(
            image,
            headline,
            (area.left + int(w * 0.04), int(h * 0.235), area.right - int(w * 0.04), int(h * 0.37)),
            font_size=max(24, int(w * 0.060)),
            fill=(255, 255, 255),
            accent=(255, 226, 142),
            max_lines=2,
        )
        canvas[:] = to_cv_rgb(image)
        return {
            "template": "grocery_receipt_hook",
            "text_boxes": report["boxes"],
            "key_number_boxes": [number_box],
            "cropped": report["cropped"],
            "motion_score": 0.88,
            "postability_signals": {
                "hook_treatment": "real_asset_grocery_loss_overlay",
                "foreground_layers": 1,
                "early_number_snap": True,
                "visual_realism": "real_asset_minimal_overlay",
                "real_asset_primary_visual": True,
            },
        }
    animated_background(canvas, scene_progress, ((8, 15, 20), (22, 70, 62)))
    image = to_pil(canvas).convert("RGBA")
    draw = ImageDraw.Draw(image, "RGBA")
    area = safe_area(w, h)

    for i in range(3):
        alpha = int(16 + 10 * math.sin(scene_progress * math.tau + i))
        x = int(w * (0.20 + i * 0.28))
        draw.line((x, int(h * 0.14), x + int(w * 0.10), int(h * 0.84)), fill=(115, 231, 185, max(8, alpha)), width=max(1, int(w * 0.003)))

    snap = ease_out(min(1.0, scene_progress / 0.34))
    panel = (area.left, int(h * 0.095), area.right, int(h * 0.675))
    panel_shift = int(h * 0.045 * (1.0 - snap))
    panel = (panel[0], panel[1] + panel_shift, panel[2], panel[3] + panel_shift)
    draw_rounded_rect(draw, (panel[0] + int(w * 0.018), panel[1] + int(h * 0.018), panel[2] + int(w * 0.018), panel[3] + int(h * 0.018)), 34, (0, 0, 0, 82), None, 1)
    draw_rounded_rect(draw, panel, 34, (246, 250, 246), (188, 212, 204), max(1, int(w * 0.004)))

    label = _scene_text(scene_config, "store_name", default="COFFEE HABIT")
    label_font = fit_font(draw, label, max(20, int(w * 0.052)), panel[2] - panel[0] - int(w * 0.12), min_size=max(15, int(w * 0.038)), bold=True)
    lw, lh = text_size(draw, label, label_font)
    label_box = ((w - lw) // 2 - int(w * 0.035), panel[1] + int(h * 0.05), (w + lw) // 2 + int(w * 0.035), panel[1] + int(h * 0.05) + lh + int(h * 0.018))
    draw_rounded_rect(draw, label_box, max(12, int(w * 0.026)), (11, 18, 32), None, 1)
    draw.text(((w - lw) // 2, label_box[1] + int(h * 0.008)), label, font=label_font, fill=(255, 255, 255))

    daily = _scene_text(scene_config, "daily_number", default="$5/DAY")
    yearly = _scene_text(scene_config, "yearly_number", "hook_number", default="$1,200/YEAR")
    daily_scale = 1.0 + 0.06 * (1.0 - ease_out(min(1.0, scene_progress / 0.24)))
    yearly_reveal = ease_out(min(1.0, max(0.0, scene_progress - 0.26) / 0.34))
    daily_font = fit_font(draw, daily, max(60, int(w * 0.19)), panel[2] - panel[0] - int(w * 0.12), min_size=max(42, int(w * 0.12)), bold=True)
    yearly_font = fit_font(draw, yearly, max(58, int(w * 0.165)), panel[2] - panel[0] - int(w * 0.12), min_size=max(38, int(w * 0.108)), bold=True)
    dw, dh = text_size(draw, daily, daily_font)
    yw, yh = text_size(draw, yearly, yearly_font)
    daily_y = panel[1] + int(h * 0.16)
    yearly_y = panel[1] + int(h * 0.32)
    daily_box = ((w - dw) // 2, daily_y, (w + dw) // 2, daily_y + dh)
    yearly_box = ((w - yw) // 2, yearly_y, (w + yw) // 2, yearly_y + yh)
    if daily_scale > 1.002:
        daily_img = Image.new("RGBA", (max(1, dw), max(1, dh)), (0, 0, 0, 0))
        daily_draw = ImageDraw.Draw(daily_img)
        daily_draw.text((0, 0), daily, font=daily_font, fill=(16, 24, 39))
        scaled = daily_img.resize((int(dw * daily_scale), int(dh * daily_scale)), Image.Resampling.BICUBIC)
        image.alpha_composite(scaled, ((w - scaled.size[0]) // 2, daily_y - (scaled.size[1] - dh) // 2))
    else:
        draw.text((daily_box[0], daily_box[1]), daily, font=daily_font, fill=(16, 24, 39))
    draw.line((panel[0] + int(w * 0.12), panel[1] + int(h * 0.285), panel[2] - int(w * 0.12), panel[1] + int(h * 0.285)), fill=(207, 219, 214), width=max(2, int(w * 0.006)))
    year_layer = Image.new("RGBA", (max(1, yw), max(1, yh)), (0, 0, 0, 0))
    year_draw = ImageDraw.Draw(year_layer)
    year_draw.text((0, 0), yearly, font=yearly_font, fill=(184, 48, 44, int(255 * yearly_reveal)))
    year_scale = 0.92 + 0.08 * yearly_reveal
    year_scaled = year_layer.resize((max(1, int(yw * year_scale)), max(1, int(yh * year_scale))), Image.Resampling.BICUBIC)
    image.alpha_composite(year_scaled, ((w - year_scaled.size[0]) // 2, yearly_y + int(h * 0.018 * (1.0 - yearly_reveal))))

    sub = _scene_text(scene_config, "subline", default="before tips + snacks")
    sub_font = fit_font(draw, sub, max(18, int(w * 0.052)), panel[2] - panel[0] - int(w * 0.14), min_size=max(14, int(w * 0.036)), bold=True)
    sw, sh = text_size(draw, sub, sub_font)
    sub_box = ((w - sw) // 2 - int(w * 0.035), panel[1] + int(h * 0.482), (w + sw) // 2 + int(w * 0.035), panel[1] + int(h * 0.482) + sh + int(h * 0.022))
    draw_rounded_rect(draw, sub_box, max(12, int(w * 0.028)), (224, 247, 237), None, 1)
    draw.text(((w - sw) // 2, sub_box[1] + int(h * 0.010)), sub, font=sub_font, fill=(11, 95, 72))

    number_box = yearly_box
    report = {"boxes": [label_box, daily_box, yearly_box, sub_box], "cropped": False}
    canvas[:] = to_cv_rgb(image)
    return {
        "template": "grocery_receipt_hook",
        "text_boxes": report["boxes"],
        "key_number_boxes": [number_box],
        "cropped": report["cropped"],
        "motion_score": 0.93,
        "postability_signals": {
            "hook_treatment": "realistic_grocery_receipt_loss",
            "foreground_layers": 4,
            "early_number_snap": True,
            "visual_realism": "textured_receipt_grocery_props",
        },
    }


def grocery_reveal_scene(frame_idx: int, scene_progress: float, canvas: np.ndarray, scene_config: dict[str, Any]) -> dict[str, Any]:
    h, w = canvas.shape[:2]
    if scene_config.get("has_real_background"):
        image = to_pil(canvas).convert("RGBA")
        draw = ImageDraw.Draw(image, "RGBA")
        area = safe_area(w, h)
        headline = _scene_text(scene_config, "headline", default="Same cart. Quiet leak.")
        panel = (area.left, int(h * 0.13), area.right, int(h * 0.42))
        draw_rounded_rect(draw, panel, 28, (0, 0, 0, 145), None, 1)
        report = draw_text_block(
            image,
            headline,
            (panel[0] + int(w * 0.045), panel[1] + int(h * 0.030), panel[2] - int(w * 0.045), panel[1] + int(h * 0.14)),
            font_size=max(28, int(w * 0.070)),
            fill=(255, 255, 255),
            accent=(255, 226, 142),
            max_lines=2,
        )
        rows = scene_config.get("leak_rows") or [("Impulse extras", "$18"), ("Brand swaps", "$13"), ("Repeat snacks", "$9")]
        y = panel[1] + int(h * 0.155)
        row_font = pil_font(max(15, int(w * 0.040)), bold=True)
        for label, value in rows[:3]:
            draw.text((panel[0] + int(w * 0.055), y), str(label), font=row_font, fill=(240, 245, 240))
            value_font = pil_font(max(15, int(w * 0.043)), bold=True)
            vw, _ = text_size(draw, str(value), value_font)
            draw.text((panel[2] - vw - int(w * 0.055), y), str(value), font=value_font, fill=(255, 226, 142))
            y += int(h * 0.055)
        canvas[:] = to_cv_rgb(image)
        return {
            "template": "grocery_reveal_scene",
            "text_boxes": report["boxes"],
            "cropped": report["cropped"],
            "motion_score": 0.84,
            "postability_signals": {
                "scene_treatment": "real_asset_grocery_reveal_overlay",
                "foreground_layers": 1,
                "visual_realism": "real_asset_minimal_overlay",
                "real_asset_primary_visual": True,
            },
        }
    animated_background(canvas, scene_progress, ((22, 31, 28), (80, 74, 50)))
    image = to_pil(canvas).convert("RGBA")
    draw = ImageDraw.Draw(image, "RGBA")
    area = safe_area(w, h)
    _draw_realistic_grocery_props(image, area, scene_progress)

    phone_w = int(w * 0.55)
    phone_h = int(h * 0.54)
    px = area.right - phone_w + int(w * 0.06 * (1 - ease_out(scene_progress)))
    py = int(h * 0.17)
    draw.ellipse((px - int(w * 0.04), py + phone_h - int(h * 0.02), px + phone_w + int(w * 0.04), py + phone_h + int(h * 0.05)), fill=(0, 0, 0, 88))
    draw_rounded_rect(draw, (px, py, px + phone_w, py + phone_h), max(24, int(w * 0.065)), (17, 24, 32), (84, 94, 106), max(2, int(w * 0.006)))
    screen = (px + int(w * 0.035), py + int(h * 0.04), px + phone_w - int(w * 0.035), py + phone_h - int(h * 0.04))
    draw_rounded_rect(draw, screen, max(18, int(w * 0.050)), (248, 250, 247), None, 1)
    draw.text((screen[0] + int(w * 0.04), screen[1] + int(h * 0.035)), "WEEKLY CART", font=pil_font(max(18, int(w * 0.048))), fill=(43, 52, 64))
    rows = scene_config.get("leak_rows") or [("Impulse extras", "$18"), ("Brand swaps", "$13"), ("Repeat snacks", "$9")]
    y = screen[1] + int(h * 0.105)
    row_font = pil_font(max(15, int(w * 0.040)), bold=True)
    for label, value in rows:
        draw_rounded_rect(draw, (screen[0] + int(w * 0.035), y, screen[2] - int(w * 0.035), y + int(h * 0.066)), max(10, int(w * 0.025)), (238, 242, 238), None, 1)
        draw.text((screen[0] + int(w * 0.06), y + int(h * 0.018)), str(label), font=row_font, fill=(50, 58, 70))
        value_font = pil_font(max(15, int(w * 0.042)), bold=True)
        vw, _ = text_size(draw, str(value), value_font)
        draw.text((screen[2] - vw - int(w * 0.06), y + int(h * 0.018)), str(value), font=value_font, fill=(186, 58, 48))
        y += int(h * 0.083)

    headline = _scene_text(scene_config, "headline", default="It was repeat grocery extras")
    report = draw_text_block(
        image,
        headline,
        (area.left, int(h * 0.16), px - int(w * 0.045), int(h * 0.45)),
        font_size=max(30, int(w * 0.078)),
        accent=(255, 226, 142),
        max_lines=3,
    )
    canvas[:] = to_cv_rgb(image)
    return {
        "template": "grocery_reveal_scene",
        "text_boxes": report["boxes"],
        "cropped": report["cropped"],
        "motion_score": 0.88,
        "postability_signals": {
            "scene_treatment": "phone_cart_breakdown",
            "foreground_layers": 4,
            "visual_realism": "grocery_bag_cart_phone",
        },
    }


def grocery_ai_comparison(frame_idx: int, scene_progress: float, canvas: np.ndarray, scene_config: dict[str, Any]) -> dict[str, Any]:
    h, w = canvas.shape[:2]
    capture_paths = [
        str(path)
        for path in (scene_config.get("resolved_asset_paths") or [])
        if str(path).strip()
    ]
    capture_path = scene_config.get("resolved_asset_path")
    if capture_paths:
        step_index = min(len(capture_paths) - 1, int(scene_progress * len(capture_paths)))
        capture_path = capture_paths[step_index]
    if capture_path:
        cache = scene_cache(scene_config)
        cache_key = f"capture:{capture_path}:{w}x{h}"
        capture = cache.get(cache_key)
        if capture is None:
            try:
                capture = Image.open(str(capture_path)).convert("RGB").resize((w, h), Image.Resampling.LANCZOS)
                cache[cache_key] = capture
            except Exception:
                capture = None
        if capture is not None:
            image = capture.convert("RGBA")
            save_box = (int(w * 0.53), int(h * 0.705), int(w * 0.90), int(h * 0.785))
            canvas[:] = to_cv_rgb(image)
            return {
                "template": "grocery_ai_comparison",
                "text_boxes": [(int(w * 0.36), int(h * 0.07), int(w * 0.93), int(h * 0.85))],
                "key_number_boxes": [save_box],
                "cropped": False,
                "motion_score": 0.82,
                "postability_signals": {
                    "motion_interruption": "ai_receipt_capture_reveal",
                    "scene_treatment": "playwright_receipt_audit_capture",
                    "visual_realism": (
                        "real_html_capture_ai_receipt_audit_motion"
                        if capture_paths
                        else "real_html_capture_ai_receipt_audit"
                    ),
                    "resolved_capture_used": True,
                    "visible_interaction": bool(scene_config.get("visible_interaction")),
                    "playwright_motion_mode": scene_config.get("playwright_motion_mode") or "static_capture",
                },
            }
    animated_background(canvas, scene_progress, ((14, 21, 31), (26, 62, 58)))
    image = to_pil(canvas).convert("RGBA")
    draw = ImageDraw.Draw(image, "RGBA")
    area = safe_area(w, h)
    panel = (area.left, int(h * 0.12), area.right, int(h * 0.77))
    draw_rounded_rect(draw, (panel[0] + int(w * 0.02), panel[1] + int(h * 0.025), panel[2] + int(w * 0.02), panel[3] + int(h * 0.025)), 34, (0, 0, 0, 86), None, 1)
    draw_rounded_rect(draw, panel, 34, (246, 248, 250), (205, 214, 224), max(2, int(w * 0.004)))
    draw_rounded_rect(draw, (panel[0] + int(w * 0.035), panel[1] + int(h * 0.03), panel[2] - int(w * 0.035), panel[1] + int(h * 0.088)), 16, (226, 232, 240), None, 1)
    for i, c in enumerate([(239, 68, 68), (245, 158, 11), (34, 197, 94)]):
        draw.ellipse((panel[0] + int(w * (0.065 + 0.038 * i)), panel[1] + int(h * 0.048), panel[0] + int(w * (0.087 + 0.038 * i)), panel[1] + int(h * 0.060)), fill=c)
    draw.text((panel[0] + int(w * 0.19), panel[1] + int(h * 0.046)), "AI receipt audit", font=pil_font(max(16, int(w * 0.038)), bold=True), fill=(71, 85, 105))

    prompt = _scene_text(scene_config, "prompt", default="Find cheaper swaps for these repeat grocery items.")
    prompt_box = (panel[0] + int(w * 0.055), panel[1] + int(h * 0.13), panel[2] - int(w * 0.055), panel[1] + int(h * 0.27))
    draw_rounded_rect(draw, prompt_box, 20, (18, 27, 42), None, 1)
    typed = prompt[: int(len(prompt) * min(1.0, scene_progress / 0.42))]
    draw_text_block(image, typed, (prompt_box[0] + int(w * 0.035), prompt_box[1] + int(h * 0.018), prompt_box[2] - int(w * 0.035), prompt_box[3] - int(h * 0.015)), font_size=max(20, int(w * 0.046)), fill=(241, 245, 249), max_lines=2)

    rows = scene_config.get("swap_rows") or [("Brand cereal", "$8.49", "store brand", "$4.19"), ("Snack packs", "$11.80", "bulk bag", "$6.40"), ("Drinks", "$13.20", "home pack", "$7.10")]
    y = panel[1] + int(h * 0.33)
    alpha = int(255 * ease_out(max(0.0, (scene_progress - 0.35) / 0.65)))
    for idx, (old, old_price, new, new_price) in enumerate(rows[:3]):
        row = (panel[0] + int(w * 0.055), y, panel[2] - int(w * 0.055), y + int(h * 0.095))
        draw_rounded_rect(draw, row, 18, (255, 255, 255, alpha), (218, 226, 234), max(1, int(w * 0.003)))
        draw.text((row[0] + int(w * 0.035), row[1] + int(h * 0.018)), str(old), font=pil_font(max(14, int(w * 0.034)), bold=True), fill=(55, 65, 81, alpha))
        draw.text((row[0] + int(w * 0.035), row[1] + int(h * 0.052)), str(old_price), font=pil_font(max(13, int(w * 0.032)), bold=True), fill=(190, 58, 48, alpha))
        arrow_x = row[0] + int(w * 0.42)
        draw.line((arrow_x, row[1] + int(h * 0.047), arrow_x + int(w * 0.10), row[1] + int(h * 0.047)), fill=(70, 90, 110, alpha), width=max(2, int(w * 0.006)))
        draw.polygon([(arrow_x + int(w * 0.10), row[1] + int(h * 0.047)), (arrow_x + int(w * 0.075), row[1] + int(h * 0.032)), (arrow_x + int(w * 0.075), row[1] + int(h * 0.062))], fill=(70, 90, 110, alpha))
        draw.text((row[0] + int(w * 0.57), row[1] + int(h * 0.018)), str(new), font=pil_font(max(14, int(w * 0.034)), bold=True), fill=(30, 105, 78, alpha))
        draw.text((row[0] + int(w * 0.57), row[1] + int(h * 0.052)), str(new_price), font=pil_font(max(13, int(w * 0.032)), bold=True), fill=(30, 130, 90, alpha))
        y += int(h * 0.115)

    save = _scene_text(scene_config, "savings_number", default="$40/week")
    save_font = fit_font(draw, save, max(32, int(w * 0.082)), panel[2] - panel[0] - int(w * 0.18), min_size=max(24, int(w * 0.060)), bold=True)
    sw, sh = text_size(draw, save, save_font)
    save_box = (panel[0] + int(w * 0.16), panel[3] - int(h * 0.115), panel[2] - int(w * 0.16), panel[3] - int(h * 0.035))
    draw_rounded_rect(draw, save_box, 18, (220, 252, 235), (72, 187, 120), max(2, int(w * 0.004)))
    draw.text((save_box[0] + max(0, (save_box[2] - save_box[0] - sw) // 2), save_box[1] + int(h * 0.017)), save, font=save_font, fill=(8, 118, 79))

    canvas[:] = to_cv_rgb(image)
    return {
        "template": "grocery_ai_comparison",
        "text_boxes": [panel],
        "key_number_boxes": [save_box],
        "cropped": False,
        "motion_score": 0.90,
        "postability_signals": {
            "motion_interruption": "ai_swap_panel_reveal",
            "scene_treatment": "screen_capture_style_ai_panel",
            "visual_realism": "dense_ai_receipt_audit",
        },
    }


def grocery_savings_payoff(frame_idx: int, scene_progress: float, canvas: np.ndarray, scene_config: dict[str, Any]) -> dict[str, Any]:
    h, w = canvas.shape[:2]
    capture_path = scene_config.get("resolved_asset_path")
    if capture_path:
        cache = scene_cache(scene_config)
        cache_key = f"capture:{capture_path}:{w}x{h}"
        capture = cache.get(cache_key)
        if capture is None:
            try:
                capture = Image.open(str(capture_path)).convert("RGB").resize((w, h), Image.Resampling.LANCZOS)
                cache[cache_key] = capture
            except Exception:
                capture = None
        if capture is not None:
            image = capture.convert("RGBA")
            number = _scene_text(scene_config, "number", "payoff_number", default="$2,080")
            draw = ImageDraw.Draw(image, "RGBA")
            area = safe_area(w, h)
            num_font = fit_font(draw, number, max(58, int(w * 0.18)), area.right - area.left - int(w * 0.16), min_size=max(38, int(w * 0.11)), bold=True)
            nw, nh = text_size(draw, number, num_font)
            num_box = ((w - nw) // 2, int(h * 0.245), (w + nw) // 2, int(h * 0.245) + nh)
            canvas[:] = to_cv_rgb(image)
            return {
                "template": "grocery_savings_payoff",
                "key_number_boxes": [num_box],
                "cropped": False,
                "motion_score": 0.84,
                "number_reveal": True,
                "postability_signals": {
                    "scene_treatment": "playwright_savings_dashboard_capture",
                    "foreground_layers": 1,
                    "share_energy": True,
                    "visual_realism": "real_html_capture_savings_dashboard",
                    "resolved_capture_used": True,
                },
            }
    animated_background(canvas, scene_progress, ((10, 18, 30), (18, 80, 66)))
    image = to_pil(canvas).convert("RGBA")
    draw = ImageDraw.Draw(image, "RGBA")
    area = safe_area(w, h)

    reveal = ease_out(min(1.0, scene_progress / 0.50))
    panel = (area.left + int(w * 0.025), int(h * 0.145 + h * 0.035 * (1.0 - reveal)), area.right - int(w * 0.025), int(h * 0.665 + h * 0.035 * (1.0 - reveal)))
    draw_rounded_rect(draw, (panel[0] + int(w * 0.016), panel[1] + int(h * 0.016), panel[2] + int(w * 0.016), panel[3] + int(h * 0.016)), 34, (0, 0, 0, 78), None, 1)
    draw_rounded_rect(draw, panel, 34, (246, 250, 247), (190, 214, 206), max(1, int(w * 0.004)))

    label = _scene_text(scene_config, "label", default="12 MONTHS LATER")
    label_font = fit_font(draw, label, max(20, int(w * 0.052)), panel[2] - panel[0] - int(w * 0.12), min_size=max(14, int(w * 0.036)), bold=True)
    lw, _ = text_size(draw, label, label_font)
    draw.text(((w - lw) // 2, panel[1] + int(h * 0.055)), label, font=label_font, fill=(58, 69, 83))

    number = _scene_text(scene_config, "number", "payoff_number", default="$1,200/year")
    num_font = fit_font(draw, number, max(60, int(w * 0.175)), panel[2] - panel[0] - int(w * 0.10), min_size=max(38, int(w * 0.11)), bold=True)
    nw, nh = text_size(draw, number, num_font)
    num_y = panel[1] + int(h * 0.175)
    num_box = ((w - nw) // 2, num_y, (w + nw) // 2, num_y + nh)
    draw.text((num_box[0], num_box[1]), number, font=num_font, fill=(184, 48, 44))

    sub = _scene_text(scene_config, "subline", default="gone before tips + snacks")
    sub_font = fit_font(draw, sub, max(20, int(w * 0.055)), panel[2] - panel[0] - int(w * 0.12), min_size=max(15, int(w * 0.038)), bold=True)
    sw, _ = text_size(draw, sub, sub_font)
    draw.text(((w - sw) // 2, num_box[3] + int(h * 0.025)), sub, font=sub_font, fill=(23, 83, 68))

    bar = (panel[0] + int(w * 0.08), panel[3] - int(h * 0.115), panel[2] - int(w * 0.08), panel[3] - int(h * 0.075))
    draw_rounded_rect(draw, bar, max(8, int(w * 0.018)), (219, 228, 224), None, 1)
    fill = (bar[0], bar[1], bar[0] + int((bar[2] - bar[0]) * reveal), bar[3])
    draw_rounded_rect(draw, fill, max(8, int(w * 0.018)), (115, 231, 185), None, 1)
    canvas[:] = to_cv_rgb(image)
    return {
        "template": "grocery_savings_payoff",
        "key_number_boxes": [num_box],
        "cropped": False,
        "motion_score": 0.94,
        "number_reveal": True,
        "postability_signals": {
            "scene_treatment": "realistic_phone_savings_estimate",
            "foreground_layers": 4,
            "share_energy": True,
            "visual_realism": "phone_app_grocery_payoff",
        },
    }


def hook_footage_overlay(frame_idx: int, scene_progress: float, canvas: np.ndarray, scene_config: dict[str, Any]) -> dict[str, Any]:
    h, w = canvas.shape[:2]
    if not scene_config.get("has_real_background"):
        animated_background(canvas, scene_progress, ((12, 18, 26), (44, 82, 70)))
    punch = 1.0 + 0.11 * (1.0 - ease_out(scene_progress))
    if punch > 1.002:
        resized = cv2.resize(canvas, None, fx=punch, fy=punch, interpolation=cv2.INTER_LINEAR)
        y = (resized.shape[0] - h) // 2
        x = (resized.shape[1] - w) // 2
        canvas[:] = resized[y:y + h, x:x + w]
    image = to_pil(canvas)
    draw = ImageDraw.Draw(image, "RGBA")
    draw.rectangle((0, 0, w, h), fill=(0, 0, 0, 58))
    area = safe_area(w, h)

    snap = ease_out(min(1.0, scene_progress / 0.32))
    drift = math.sin(scene_progress * math.tau) * w * 0.018
    receipt_w = int(w * 0.38)
    receipt_h = int(h * 0.36)
    receipt_x = int(w * (0.58 + 0.12 * (1.0 - snap)) + drift)
    receipt_y = int(h * (0.27 - 0.035 * (1.0 - snap)))
    receipt = (receipt_x, receipt_y, receipt_x + receipt_w, receipt_y + receipt_h)
    draw_rounded_rect(draw, receipt, max(12, int(w * 0.035)), (250, 248, 240), (255, 255, 255), max(1, int(w * 0.006)))
    for i in range(5):
        y = receipt_y + int(receipt_h * (0.18 + i * 0.12))
        line_w = int(receipt_w * (0.68 - 0.05 * (i % 2)))
        draw.line((receipt_x + int(w * 0.035), y, receipt_x + int(w * 0.035) + line_w, y), fill=(112, 96, 82, 210), width=max(1, int(w * 0.008)))
    receipt_price_text = _scene_text(scene_config, "receipt_price_text", default="$5.00")
    if receipt_price_text:
        draw.text((receipt_x + int(w * 0.04), receipt_y + int(receipt_h * 0.78)), receipt_price_text, font=pil_font(max(14, int(w * 0.075))), fill=(168, 43, 40))

    cup_x = int(w * (0.61 + 0.04 * (1.0 - snap)))
    cup_y = int(h * (0.52 + 0.025 * math.sin(scene_progress * math.tau * 1.4)))
    cup_w = int(w * 0.28)
    cup_h = int(h * 0.23)
    draw.ellipse((cup_x + int(cup_w * 0.05), cup_y - int(cup_h * 0.11), cup_x + int(cup_w * 0.95), cup_y + int(cup_h * 0.12)), fill=(248, 250, 252), outline=(210, 218, 228), width=max(1, int(w * 0.008)))
    draw_rounded_rect(draw, (cup_x + int(cup_w * 0.12), cup_y, cup_x + int(cup_w * 0.88), cup_y + cup_h), max(12, int(w * 0.04)), (245, 245, 240), (214, 220, 228), max(1, int(w * 0.008)))
    draw_rounded_rect(draw, (cup_x + int(cup_w * 0.25), cup_y + int(cup_h * 0.38), cup_x + int(cup_w * 0.75), cup_y + int(cup_h * 0.62)), max(8, int(w * 0.025)), (47, 103, 91), None, 1)
    for i in range(3):
        sx = cup_x + int(cup_w * (0.28 + i * 0.17))
        sy = cup_y - int(cup_h * (0.20 + 0.04 * i))
        draw.arc((sx, sy, sx + int(w * 0.08), sy + int(h * 0.12)), 105, 245, fill=(255, 255, 255, 130), width=max(1, int(w * 0.006)))

    price_text = _scene_text(scene_config, "price_text", "hook_number", default="$5/day = $1,825/year?")
    pad_x = int(w * 0.035)
    pad_y = int(h * 0.014)
    price_font = fit_font(draw, price_text, max(18, int(w * 0.092)), area.right - area.left - pad_x * 2, min_size=max(14, int(w * 0.060)), bold=True)
    tw, th = text_size(draw, price_text, price_font)
    price_w = min(area.right - area.left, tw + pad_x * 2)
    price_x = area.left + int((area.right - area.left - price_w) * 0.5)
    price_y = int(h * (0.16 + 0.035 * (1.0 - snap)))
    price_box = (price_x, price_y, price_x + price_w, price_y + th + pad_y * 2)
    draw_rounded_rect(draw, price_box, max(14, int(w * 0.045)), (250, 250, 250), (115, 231, 185), max(2, int(w * 0.01)))
    draw.text((price_x + max(0, (price_w - tw) // 2), price_y + pad_y - 2), price_text, font=price_font, fill=(19, 24, 33))

    for i in range(5):
        streak_y = int(h * (0.12 + i * 0.13) + math.sin(scene_progress * math.tau + i) * h * 0.015)
        streak_x = int(w * ((scene_progress * 1.4 + i * 0.21) % 1.15) - w * 0.15)
        draw.line((streak_x, streak_y, streak_x + int(w * 0.22), streak_y - int(h * 0.035)), fill=(115, 231, 185, 70), width=max(1, int(w * 0.01)))

    report = draw_text_block(
        image,
        _scene_text(scene_config, "headline", "caption_text", "source_text", default="Small habits get expensive"),
        (area.left, int(h * 0.50), int(w * 0.61), int(h * 0.75)),
        font_size=max(30, int(w * 0.100)),
        accent=(115, 231, 185),
        max_lines=3,
    )
    canvas[:] = to_cv(image)
    return {
        "template": "hook_footage_overlay",
        "text_boxes": report["boxes"],
        "key_number_boxes": [price_box],
        "cropped": report["cropped"],
        "motion_score": 0.94,
        "postability_signals": {
            "hook_treatment": "price_snap_receipt_coffee",
            "foreground_layers": 3,
            "early_number_snap": True,
        },
    }


def money_shock_math(frame_idx: int, scene_progress: float, canvas: np.ndarray, scene_config: dict[str, Any]) -> dict[str, Any]:
    h, w = canvas.shape[:2]
    animated_background(canvas, scene_progress, ((12, 18, 30), (36, 64, 58)))
    image = to_pil(canvas).convert("RGBA")
    draw = ImageDraw.Draw(image, "RGBA")
    area = safe_area(w, h)

    card_scale = 0.985 + 0.015 * ease_out(min(1.0, scene_progress / 0.30))
    base_card = (area.left + int(w * 0.02), int(h * 0.125), area.right - int(w * 0.02), int(h * 0.70))
    cx = (base_card[0] + base_card[2]) // 2
    cy = (base_card[1] + base_card[3]) // 2
    half_w = int((base_card[2] - base_card[0]) * card_scale / 2)
    half_h = int((base_card[3] - base_card[1]) * card_scale / 2)
    card = (cx - half_w, cy - half_h, cx + half_w, cy + half_h)
    draw_rounded_rect(draw, (card[0] + int(w * 0.016), card[1] + int(h * 0.016), card[2] + int(w * 0.016), card[3] + int(h * 0.016)), 34, (0, 0, 0, 80), None, 1)
    draw_rounded_rect(draw, card, 34, (248, 250, 252), (210, 220, 230), max(1, int(w * 0.004)))

    label = _scene_text(scene_config, "label", default="MONTHLY MATH")
    label_font = fit_font(draw, label, max(19, int(w * 0.052)), card[2] - card[0] - int(w * 0.12), min_size=max(14, int(w * 0.036)), bold=True)
    draw.text((card[0] + int(w * 0.06), card[1] + int(h * 0.045)), label, font=label_font, fill=(58, 69, 83))

    dot_progress = ease_out(min(1.0, scene_progress / 0.72))
    dot_size = max(8, int(w * 0.025))
    gap = max(10, int(w * 0.022))
    start_x = card[0] + int(w * 0.075)
    start_y = card[1] + int(h * 0.12)
    for i in range(20):
        col = i % 5
        row = i // 5
        x = start_x + col * (dot_size + gap)
        y = start_y + row * (dot_size + gap)
        active = i < int(20 * dot_progress)
        fill = (17, 148, 111) if active else (213, 222, 230)
        draw.ellipse((x, y, x + dot_size, y + dot_size), fill=fill)

    formula_alpha = int(255 * ease_out(min(1.0, max(0.0, scene_progress - 0.18) / 0.32)))
    formula = _scene_text(scene_config, "formula", default="$5 x 20 WORKDAYS")
    formula_font = fit_font(draw, formula, max(31, int(w * 0.088)), card[2] - card[0] - int(w * 0.12), min_size=max(22, int(w * 0.060)), bold=True)
    fw, fh = text_size(draw, formula, formula_font)
    formula_box = ((w - fw) // 2, card[1] + int(h * 0.275), (w + fw) // 2, card[1] + int(h * 0.275) + fh)
    draw.text((formula_box[0], formula_box[1]), formula, font=formula_font, fill=(18, 24, 38, formula_alpha))

    number = _scene_text(scene_config, "number", "monthly_number", default="$100/MONTH")
    font_num = fit_font(draw, number, max(56, int(w * 0.16)), card[2] - card[0] - int(w * 0.10), min_size=max(36, int(w * 0.10)), bold=True)
    nw, nh = text_size(draw, number, font_num)
    num_y = card[1] + int(h * 0.395)
    num_box = ((w - nw) // 2, num_y, (w + nw) // 2, num_y + nh)
    number_alpha = int(255 * ease_out(min(1.0, max(0.0, scene_progress - 0.34) / 0.36)))
    draw.text((num_box[0], num_box[1]), number, font=font_num, fill=(184, 48, 44, number_alpha))

    explainer = _scene_text(scene_config, "subline", default="every workday coffee run")
    explainer_font = fit_font(draw, explainer, max(16, int(w * 0.044)), card[2] - card[0] - int(w * 0.14), min_size=max(13, int(w * 0.032)), bold=True)
    ew, eh = text_size(draw, explainer, explainer_font)
    explainer_box = ((w - ew) // 2 - int(w * 0.035), card[3] - int(h * 0.085), (w + ew) // 2 + int(w * 0.035), card[3] - int(h * 0.085) + eh + int(h * 0.020))
    draw_rounded_rect(draw, explainer_box, max(10, int(w * 0.025)), (234, 246, 242), None, 1)
    draw.text(((w - ew) // 2, explainer_box[1] + int(h * 0.009)), explainer, font=explainer_font, fill=(30, 94, 74))

    canvas[:] = to_cv_rgb(image)
    return {
        "template": "money_shock_math",
        "key_number_boxes": [num_box],
        "cropped": False,
        "motion_score": 0.93,
        "postability_signals": {
            "motion_interruption": "price_check_sweep",
        },
    }


def ai_prompt_mock(frame_idx: int, scene_progress: float, canvas: np.ndarray, scene_config: dict[str, Any]) -> dict[str, Any]:
    h, w = canvas.shape[:2]
    animated_background(canvas, scene_progress, ((8, 15, 28), (25, 50, 70)))
    area = safe_area(w, h)
    browser = (area.left, int(h * 0.16), area.right, int(h * 0.78))
    prompt_box = (browser[0] + 58, browser[1] + 140, browser[2] - 58, browser[1] + 350)
    cache = scene_cache(scene_config)
    overlay = cache.get("ai_prompt_static_overlay")
    if overlay is None:
        overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        static_draw = ImageDraw.Draw(overlay, "RGBA")
        draw_rounded_rect(static_draw, browser, 30, (246, 248, 252), (208, 216, 226), 3)
        draw_rounded_rect(static_draw, (browser[0] + 28, browser[1] + 28, browser[2] - 28, browser[1] + 90), 18, (226, 232, 240))
        for i, c in enumerate([(239, 68, 68), (245, 158, 11), (34, 197, 94)]):
            static_draw.ellipse((browser[0] + 48 + i * 42, browser[1] + 49, browser[0] + 72 + i * 42, browser[1] + 73), fill=c)
        draw_rounded_rect(static_draw, prompt_box, 24, (16, 24, 39), None, 1)
        cache["ai_prompt_static_overlay"] = overlay

    image = to_pil(canvas).convert("RGBA")
    image.alpha_composite(overlay)
    draw = ImageDraw.Draw(image, "RGBA")
    prompt = _scene_text(scene_config, "prompt", "caption_text", default="Compare coffee shop runs with brewing at home.")
    typed_len = int(len(prompt) * min(1.0, scene_progress / 0.48))
    typed = prompt[:typed_len]
    font = pil_font(42, bold=False)
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
    canvas[:] = to_cv_rgb(image)
    return {"template": "ai_prompt_mock", "text_boxes": [browser], "cropped": False, "motion_score": 0.88}


def comparison_split(frame_idx: int, scene_progress: float, canvas: np.ndarray, scene_config: dict[str, Any]) -> dict[str, Any]:
    h, w = canvas.shape[:2]
    animated_background(canvas, scene_progress, ((9, 16, 28), (20, 72, 61)))
    image = to_pil(canvas).convert("RGBA")
    draw = ImageDraw.Draw(image, "RGBA")
    area = safe_area(w, h)

    title = _scene_text(scene_config, "comparison_title", default="COFFEE SHOP vs HOME BREW")
    title_font = fit_font(draw, title, max(23, int(w * 0.060)), area.right - area.left, min_size=max(16, int(w * 0.040)), bold=True)
    tw, th = text_size(draw, title, title_font)
    draw.text(((w - tw) // 2, int(h * 0.105)), title, font=title_font, fill=(232, 246, 241))

    shop_label = _scene_text(scene_config, "shop_label", default="COFFEE SHOP")
    shop_value = _scene_text(scene_config, "shop_number", default="$100/mo")
    home_label = _scene_text(scene_config, "home_label", default="HOME BREW")
    home_value = _scene_text(scene_config, "home_number", default="$20/mo")
    save_text = _scene_text(scene_config, "savings_number", default="SAVE $80/mo")

    card_gap = int(h * 0.025)
    card_h = int(h * 0.145)
    top = int(h * 0.195)
    cards = [
        ((area.left + int(w * 0.02), top, area.right - int(w * 0.02), top + card_h), shop_label, shop_value, (184, 48, 44)),
        ((area.left + int(w * 0.02), top + card_h + card_gap, area.right - int(w * 0.02), top + card_h * 2 + card_gap), home_label, home_value, (8, 132, 94)),
    ]
    for idx, (card, label, value, color) in enumerate(cards):
        enter = ease_out(min(1.0, max(0.0, scene_progress - idx * 0.10) / 0.45))
        y_shift = int(h * 0.025 * (1.0 - enter))
        card = (card[0], card[1] + y_shift, card[2], card[3] + y_shift)
        draw_rounded_rect(draw, (card[0] + int(w * 0.012), card[1] + int(h * 0.010), card[2] + int(w * 0.012), card[3] + int(h * 0.010)), 26, (0, 0, 0, 58), None, 1)
        draw_rounded_rect(draw, card, 26, (248, 250, 252), (205, 216, 224), max(1, int(w * 0.004)))
        label_font = fit_font(draw, label, max(20, int(w * 0.052)), int((card[2] - card[0]) * 0.48), min_size=max(14, int(w * 0.036)), bold=True)
        draw.text((card[0] + int(w * 0.055), card[1] + int(h * 0.047)), label, font=label_font, fill=(58, 69, 83))
        value_font = fit_font(draw, value, max(35, int(w * 0.098)), int((card[2] - card[0]) * 0.40), min_size=max(24, int(w * 0.065)), bold=True)
        vw, vh = text_size(draw, value, value_font)
        draw.text((card[2] - vw - int(w * 0.055), card[1] + (card_h - vh) // 2), value, font=value_font, fill=color)

    save_reveal = ease_out(min(1.0, max(0.0, scene_progress - 0.22) / 0.50))
    badge_h = int(h * 0.135)
    badge = (area.left + int(w * 0.05), int(h * 0.555), area.right - int(w * 0.05), int(h * 0.555) + badge_h)
    badge = (badge[0], badge[1] + int(h * 0.035 * (1.0 - save_reveal)), badge[2], badge[3] + int(h * 0.035 * (1.0 - save_reveal)))
    draw_rounded_rect(draw, (badge[0] + int(w * 0.014), badge[1] + int(h * 0.012), badge[2] + int(w * 0.014), badge[3] + int(h * 0.012)), 30, (0, 0, 0, 70), None, 1)
    draw_rounded_rect(draw, badge, 30, (115, 231, 185), None, 1)
    save_font = fit_font(draw, save_text, max(42, int(w * 0.115)), badge[2] - badge[0] - int(w * 0.10), min_size=max(28, int(w * 0.076)), bold=True)
    sw, sh = text_size(draw, save_text, save_font)
    num_box = ((w - sw) // 2, badge[1] + (badge_h - sh) // 2, (w + sw) // 2, badge[1] + (badge_h + sh) // 2)
    draw.text((num_box[0], num_box[1]), save_text, font=save_font, fill=(6, 42, 34))

    sub = _scene_text(scene_config, "subline", default="same habit, cheaper route")
    sub_font = fit_font(draw, sub, max(16, int(w * 0.044)), area.right - area.left - int(w * 0.12), min_size=max(13, int(w * 0.034)), bold=True)
    sub_w, _ = text_size(draw, sub, sub_font)
    draw.text(((w - sub_w) // 2, badge[3] + int(h * 0.030)), sub, font=sub_font, fill=(206, 237, 226))

    canvas[:] = to_cv_rgb(image)
    return {
        "template": "comparison_split",
        "key_number_boxes": [num_box],
        "cropped": False,
        "motion_score": 0.9,
        "postability_signals": {
            "scene_treatment": "coffee_cost_comparison",
            "foreground_layers": 3,
        },
    }


def payoff_number_reveal(frame_idx: int, scene_progress: float, canvas: np.ndarray, scene_config: dict[str, Any]) -> dict[str, Any]:
    h, w = canvas.shape[:2]
    animated_background(canvas, scene_progress, ((8, 18, 30), (10, 92, 76)))
    reveal = ease_out(min(1.0, scene_progress / 0.58))
    settle = ease_in_out(min(1.0, max(0.0, (scene_progress - 0.40) / 0.60)))

    for i in range(44):
        ang = (i / 44.0) * math.tau + scene_progress * 1.8
        rad = (w * 0.34) + (w * 0.18) * math.sin(scene_progress * math.pi + i)
        cx = int(w / 2 + math.cos(ang) * rad)
        cy = int(h * 0.36 + math.sin(ang) * rad * 0.48)
        cv2.circle(canvas, (cx, cy), max(2, int(w * 0.012)), (130, 245, 210), -1, lineType=cv2.LINE_AA)
    for i in range(8):
        y = int(h * (0.11 + i * 0.095) + math.sin(scene_progress * math.tau + i) * h * 0.014)
        x = int(w * ((scene_progress * 0.22 + i * 0.15) % 1.1) - w * 0.10)
        cv2.line(canvas, (x, y), (x + int(w * 0.28), y - int(h * 0.025)), (64, 210, 170), max(1, int(w * 0.006)), lineType=cv2.LINE_AA)

    image = to_pil(canvas).convert("RGBA")
    draw = ImageDraw.Draw(image, "RGBA")
    count = int(1500 * ease_out(scene_progress))
    number = _scene_text(scene_config, "number", "payoff_number", default="$1,500+")
    if "{count}" in number:
        number = number.format(count=f"{count:,}")

    area = safe_area(w, h)
    phone_w = int(w * 0.66)
    phone_h = int(h * 0.48)
    phone_x = (w - phone_w) // 2
    phone_y = int(h * (0.18 + 0.03 * (1.0 - reveal)))
    phone = (phone_x, phone_y, phone_x + phone_w, phone_y + phone_h)
    draw.ellipse((phone_x - int(w * 0.04), phone[3] - int(h * 0.035), phone[2] + int(w * 0.04), phone[3] + int(h * 0.06)), fill=(0, 0, 0, 86))
    cache = scene_cache(scene_config)
    phone_patch = cache.get("payoff_phone_patch")
    if phone_patch is None:
        phone_patch = Image.new("RGBA", (phone_w, phone_h), (0, 0, 0, 0))
        phone_draw = ImageDraw.Draw(phone_patch, "RGBA")
        draw_rounded_rect(phone_draw, (0, 0, phone_w, phone_h), max(20, int(w * 0.065)), (12, 18, 28), (81, 100, 115), max(1, int(w * 0.008)))
        screen_patch = (int(w * 0.035), int(h * 0.040), phone_w - int(w * 0.035), phone_h - int(h * 0.040))
        draw_rounded_rect(phone_draw, screen_patch, max(16, int(w * 0.05)), (236, 253, 246), None, 1)
        badge_text = "SAVED"
        badge_font = pil_font(max(16, int(w * 0.062)), bold=True)
        bw, bh = text_size(phone_draw, badge_text, badge_font)
        badge = (screen_patch[0] + int(w * 0.045), screen_patch[1] + int(h * 0.040), screen_patch[0] + int(w * 0.045) + bw + int(w * 0.09), screen_patch[1] + int(h * 0.040) + bh + int(h * 0.034))
        draw_rounded_rect(phone_draw, badge, max(12, int(w * 0.04)), (8, 112, 84), None, 1)
        phone_draw.text((badge[0] + int(w * 0.045), badge[1] + int(h * 0.014)), badge_text, font=badge_font, fill=(255, 255, 255))
        cache["payoff_phone_patch"] = phone_patch
    paste_overlay_clipped(image, phone_patch, (phone_x, phone_y))
    screen = (phone_x + int(w * 0.035), phone_y + int(h * 0.040), phone[2] - int(w * 0.035), phone[3] - int(h * 0.040))

    font_size = max(44, int(w * (0.225 + 0.014 * math.sin(scene_progress * math.tau * 1.2))))
    font = fit_font(draw, number, font_size, screen[2] - screen[0] - int(w * 0.13), min_size=max(38, int(w * 0.14)), bold=True)
    nw, nh = text_size(draw, number, font)
    num_y = screen[1] + int(h * (0.18 - 0.020 * (1.0 - reveal)))
    num_box = ((w - nw) // 2, num_y, (w + nw) // 2, num_y + nh)
    draw.text((num_box[0] + 4, num_box[1] + 5), number, font=font, fill=(0, 0, 0, 95))
    draw.text((num_box[0], num_box[1]), number, font=font, fill=(6, 150, 110))

    sub = _scene_text(scene_config, "subline", default="a year from one small habit")
    sub_font = fit_font(draw, sub, max(18, int(w * 0.065)), screen[2] - screen[0] - int(w * 0.08), min_size=max(14, int(w * 0.040)), bold=True)
    sw, sh = text_size(draw, sub, sub_font)
    sub_x = max(screen[0] + int(w * 0.04), (w - sw) // 2)
    sub_y = min(num_box[3] + int(h * 0.035), screen[3] - int(h * 0.150))
    draw.text((sub_x + 2, sub_y + 2), sub, font=sub_font, fill=(0, 0, 0, 80))
    draw.text((sub_x, sub_y), sub, font=sub_font, fill=(22, 78, 62))

    action_y = screen[3] - int(h * 0.082)
    actions = ["SAVE", "SHARE", "COMMENT"]
    action_font = pil_font(max(12, int(w * 0.041)), bold=True)
    x = screen[0] + int(w * 0.045)
    for idx, action in enumerate(actions):
        aw, ah = text_size(draw, action, action_font)
        lift = int(math.sin(scene_progress * math.tau * 1.5 + idx) * h * 0.006)
        pill = (x, action_y + lift, x + aw + int(w * 0.055), action_y + lift + ah + int(h * 0.028))
        fill = (14, 22, 38) if idx != 2 else (8, 112, 84)
        draw_rounded_rect(draw, pill, max(9, int(w * 0.030)), fill, (115, 231, 185), max(1, int(w * 0.004)))
        draw.text((pill[0] + int(w * 0.027), pill[1] + int(h * 0.011)), action, font=action_font, fill=(255, 255, 255))
        x = pill[2] + int(w * 0.025)

    spark_count = 18
    for i in range(spark_count):
        p = (scene_progress + i / spark_count) % 1.0
        ang = i * 2.399 + settle * 0.8
        sx = int(w / 2 + math.cos(ang) * w * (0.18 + 0.18 * p))
        sy = int(h * 0.35 + math.sin(ang) * h * (0.10 + 0.12 * p))
        alpha = int(150 * (1.0 - p))
        draw.line((sx - 3, sy, sx + 3, sy), fill=(255, 255, 255, alpha), width=max(1, int(w * 0.006)))

    canvas[:] = to_cv_rgb(image)
    return {
        "template": "payoff_number_reveal",
        "key_number_boxes": [num_box],
        "cropped": False,
        "motion_score": 0.95,
        "number_reveal": True,
        "postability_signals": {
            "scene_treatment": "platform_payoff_phone_overlay",
            "foreground_layers": 3,
            "share_energy": True,
        },
    }


def cta_callback(frame_idx: int, scene_progress: float, canvas: np.ndarray, scene_config: dict[str, Any]) -> dict[str, Any]:
    h, w = canvas.shape[:2]
    animated_background(canvas, scene_progress, ((11, 18, 32), (38, 68, 62)))
    image = to_pil(canvas)
    draw = ImageDraw.Draw(image, "RGBA")
    area = safe_area(w, h)
    draw_rounded_rect(draw, (area.left, int(h * 0.22), area.right, int(h * 0.68)), 42, (10, 14, 22), (115, 231, 185), 4)
    eyebrow = _scene_text(scene_config, "eyebrow", default="WANT THE PROMPT?")
    draw.text((area.left + 52, int(h * 0.27)), eyebrow.upper(), font=pil_font(48, bold=True), fill=(148, 163, 184))
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
    "grocery_receipt_hook": grocery_receipt_hook,
    "grocery_reveal_scene": grocery_reveal_scene,
    "grocery_ai_comparison": grocery_ai_comparison,
    "grocery_savings_payoff": grocery_savings_payoff,
}


def get_template(name: str) -> Callable[[int, float, np.ndarray, dict[str, Any]], dict[str, Any]]:
    return TEMPLATES.get(name) or hook_footage_overlay
