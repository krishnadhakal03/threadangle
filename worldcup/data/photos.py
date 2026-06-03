"""
Player photo fetching for World Cup 2026 video cards.

Resolution order:
  1. Wikipedia REST API thumbnail (cached to disk)
  2. Styled initials circle with gold border (always works)

All photos cached to worldcup/data/cache/photos/ as PNG files.
"""
from __future__ import annotations

import hashlib
import io
from pathlib import Path
from typing import Optional

import requests
from PIL import Image, ImageDraw, ImageFont

from worldcup.config import CACHE_DIR, FONTS

PHOTO_CACHE = CACHE_DIR / "photos"
PHOTO_CACHE.mkdir(parents=True, exist_ok=True)


# ── Initials fallback ──────────────────────────────────────────────────────────

def _initials_circle(name: str, size: int = 240,
                      bg: tuple = (15, 15, 40),
                      border: tuple = (255, 215, 0)) -> Image.Image:
    """Gold-bordered circle containing the player's initials."""
    img  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    draw.ellipse((0, 0, size - 1, size - 1), fill=bg)

    bw = max(4, size // 22)
    draw.ellipse((bw // 2, bw // 2, size - bw // 2 - 1, size - bw // 2 - 1),
                 outline=border, width=bw)

    parts    = name.split()
    initials = (parts[0][0] + parts[-1][0]).upper() if len(parts) > 1 else name[:2].upper()

    font_path = FONTS.get("bold", "")
    font_size = size // 3
    try:
        font = (ImageFont.truetype(font_path, font_size)
                if font_path and Path(font_path).exists()
                else ImageFont.load_default())
    except Exception:
        font = ImageFont.load_default()

    bb = draw.textbbox((0, 0), initials, font=font)
    draw.text(((size - (bb[2] - bb[0])) // 2, (size - (bb[3] - bb[1])) // 2 - 4),
              initials, font=font, fill=border)
    return img


# ── Wikipedia fetch ────────────────────────────────────────────────────────────

def _wiki_photo(player_name: str) -> Optional[Image.Image]:
    key   = hashlib.md5(player_name.lower().encode()).hexdigest()[:14]
    cache = PHOTO_CACHE / f"wiki_{key}.png"

    if cache.exists():
        try:
            return Image.open(cache).convert("RGBA")
        except Exception:
            pass

    try:
        title = player_name.replace(" ", "_")
        api   = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
        resp  = requests.get(api, timeout=6,
                             headers={"User-Agent": "ThreadangleWCBot/1.0"})
        resp.raise_for_status()
        thumb_url = resp.json().get("thumbnail", {}).get("source", "")
        if not thumb_url:
            return None

        ir = requests.get(thumb_url, timeout=6)
        ir.raise_for_status()
        img = Image.open(io.BytesIO(ir.content)).convert("RGBA")

        # Square-crop from centre
        w, h = img.size
        m    = min(w, h)
        img  = img.crop(((w - m) // 2, (h - m) // 2,
                         (w - m) // 2 + m, (h - m) // 2 + m))
        img.save(cache)
        return img
    except Exception:
        return None


# ── Public API ─────────────────────────────────────────────────────────────────

def get_player_photo(player_name: str, size: int = 240,
                      accent: tuple = (255, 215, 0)) -> Image.Image:
    """
    Return a circular RGBA photo at *size*×*size*.

    Falls back to a styled initials circle if Wikipedia has no image.
    Always returns a valid Image — never None.
    """
    raw = _wiki_photo(player_name)

    if raw:
        raw = raw.resize((size, size), Image.LANCZOS)
        # Circular mask
        out  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, size - 1, size - 1), fill=255)
        out.paste(raw, (0, 0), mask)
        # Accent border
        bw = max(3, size // 28)
        ImageDraw.Draw(out).ellipse((bw // 2, bw // 2,
                                     size - bw // 2 - 1, size - bw // 2 - 1),
                                    outline=accent, width=bw)
        return out

    return _initials_circle(player_name, size=size, border=accent)
