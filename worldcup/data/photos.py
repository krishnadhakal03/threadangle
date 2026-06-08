"""
Player photo fetching for World Cup 2026 video cards.

Resolution order:
  1. Disk cache (PNG saved from a previous successful fetch)
  2. Wikipedia REST API thumbnail — exact player name
  3. Wikipedia REST API thumbnail — "{name} (footballer)"
  4. Wikipedia search API — first hit for "{name} footballer"
  5. TheSportsDB API — strCutout / strThumb field
  6. Returns None — caller renders typographic fallback

All photos cached to worldcup/data/cache/photos/ as PNG files.
A sentinel file (.miss) is written when no photo exists to avoid
redundant network calls on re-runs.
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

_UA = {"User-Agent": "ThreadangleWCBot/1.0 (worldcup video factory)"}

# Known Wikipedia page-title corrections for footballer names that differ
# from the display name stored in wc2026_data.py.
_WIKI_TITLE_MAP: dict[str, str] = {
    "vinicius jr":       "Vinicius Junior",
    "kylian mbappe":     "Kylian Mbappe",
    "erling haaland":    "Erling Haaland",
    "harry kane":        "Harry Kane",
    "lionel messi":      "Lionel Messi",
    "cristiano ronaldo": "Cristiano Ronaldo",
    "jude bellingham":   "Jude Bellingham",
    "lamine yamal":      "Lamine Yamal",
    "jamal musiala":     "Jamal Musiala",
    "florian wirtz":     "Florian Wirtz",
    "endrick":           "Endrick (footballer)",
}


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


# ── Wikipedia helpers ──────────────────────────────────────────────────────────

def _wiki_summary_thumb(page_title: str) -> Optional[str]:
    """Return thumbnail URL for a Wikipedia page title, or None."""
    try:
        safe = page_title.replace(" ", "_")
        r = requests.get(
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{safe}",
            headers=_UA, timeout=6,
        )
        r.raise_for_status()
        return r.json().get("thumbnail", {}).get("source", "") or None
    except Exception:
        return None


def _wiki_search_title(query: str) -> Optional[str]:
    """Use Wikipedia search API; return the top hit title or None."""
    try:
        r = requests.get(
            "https://en.wikipedia.org/w/api.php",
            params={"action": "query", "list": "search",
                    "srsearch": query, "format": "json", "srlimit": 3},
            headers=_UA, timeout=6,
        )
        r.raise_for_status()
        hits = r.json().get("query", {}).get("search", [])
        return hits[0]["title"] if hits else None
    except Exception:
        return None


def _download_image(url: str) -> Optional[Image.Image]:
    try:
        r = requests.get(url, headers=_UA, timeout=8)
        r.raise_for_status()
        img = Image.open(io.BytesIO(r.content)).convert("RGBA")
        w, h = img.size
        m    = min(w, h)
        img  = img.crop(((w - m) // 2, (h - m) // 2,
                         (w - m) // 2 + m, (h - m) // 2 + m))
        return img
    except Exception:
        return None


def _wiki_photo(player_name: str) -> Optional[Image.Image]:
    """
    Multi-step Wikipedia photo fetch with disk cache.

    Steps:
      1. Disk cache hit (PNG or .miss sentinel)
      2. Exact name lookup
      3. Known title correction map
      4. "{name} (footballer)" suffix
      5. Wikipedia search API "footballer" query
    """
    key     = hashlib.md5(player_name.lower().encode()).hexdigest()[:14]
    cached  = PHOTO_CACHE / f"wiki_{key}.png"
    sentinel = PHOTO_CACHE / f"wiki_{key}.miss"

    # Cache hit
    if cached.exists():
        try:
            return Image.open(cached).convert("RGBA")
        except Exception:
            pass

    # Confirmed no photo
    if sentinel.exists():
        return None

    thumb_url: Optional[str] = None
    lower = player_name.lower()

    # Step 2 — exact name / known alias
    canonical = _WIKI_TITLE_MAP.get(lower, player_name)
    thumb_url = _wiki_summary_thumb(canonical)

    # Step 3 — "{name} (footballer)"
    if not thumb_url:
        thumb_url = _wiki_summary_thumb(f"{canonical} (footballer)")

    # Step 4 — search API "footballer"
    if not thumb_url:
        found = _wiki_search_title(f"{player_name} footballer")
        if found:
            thumb_url = _wiki_summary_thumb(found)

    # Step 5 — search API plain name
    if not thumb_url:
        found = _wiki_search_title(player_name)
        if found:
            thumb_url = _wiki_summary_thumb(found)

    if not thumb_url:
        sentinel.touch()   # write miss sentinel to skip future network calls
        return None

    img = _download_image(thumb_url)
    if img:
        img.save(cached)
        return img

    sentinel.touch()
    return None


# ── TheSportsDB fallback ────────────────────────────────────────────────────────

def _sportsdb_photo(player_name: str) -> Optional[Image.Image]:
    """
    Try TheSportsDB free API for a player photo.
    Uses strCutout (transparent PNG) if available, then strThumb.
    Returns a square-cropped RGBA Image or None.
    """
    try:
        r = requests.get(
            "https://www.thesportsdb.com/api/v1/json/3/searchplayers.php",
            params={"p": player_name},
            headers=_UA,
            timeout=8,
        )
        r.raise_for_status()
        players = r.json().get("player") or []
        if not players:
            return None
        p = players[0]
        url = p.get("strCutout") or p.get("strThumb") or ""
        if not url:
            return None
        return _download_image(url)
    except Exception:
        return None


# ── Public API ─────────────────────────────────────────────────────────────────

def get_player_photo(player_name: str, size: int = 240,
                      accent: tuple = (255, 215, 0)) -> Optional[Image.Image]:
    """
    Return a circular RGBA photo at *size*×*size*, or None if no real photo found.

    Resolution order:
      1. Disk cache
      2. Wikipedia (multi-step)
      3. TheSportsDB API (strCutout / strThumb)

    When None is returned the caller is expected to render a typographic fallback.
    Border: 6px solid #E63946 (red), independent of team accent colour.
    """
    raw = _wiki_photo(player_name)
    if not raw:
        raw = _sportsdb_photo(player_name)

    if not raw:
        return None

    raw = raw.resize((size, size), Image.LANCZOS)
    out  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size - 1, size - 1), fill=255)
    out.paste(raw, (0, 0), mask)
    # 6px #E63946 border regardless of team accent
    ImageDraw.Draw(out).ellipse((3, 3, size - 4, size - 4),
                                outline=(230, 57, 70), width=6)
    return out
