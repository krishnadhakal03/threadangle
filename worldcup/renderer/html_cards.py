"""
HTML + Playwright card renderer for World Cup 2026 videos (Issue #123, step 16A).

Public API
----------
render_team_cards(team, output_dir=None) -> list[Path]

Takes team name, pulls data from wc2026_data.py, renders each card segment as a
self-contained HTML page, screenshots at 1080×1920 via Playwright (headless
Chromium), and saves PNGs to worldcup/output/cards/{team}/.

Card segments (in pipeline order):
  hook.png       — team intro: flag + name + group badge
  history.png    — THE RECORD: 2×2 stat grid + bar + recent WC timeline
  player_0.png   — key player 1 spotlight
  player_1.png   — key player 2 spotlight
  player_2.png   — key player 3 spotlight
  group.png      — group draw: 4 team rows with flag images
  cta.png        — prediction prompt + subscribe CTA

YouTube Shorts safe zones (no text placed outside these boundaries):
  Horizontal: 120 px margin each side  →  content in x: 120–960
  Top:        250 px from top          →  text starts at y ≥ 250 (clears status bar)
  Bottom:     520 px from bottom       →  text ends at y ≤ 1400 (clears nav bar)
Decorative bars, borders, and images may extend outside these zones.
"""
from __future__ import annotations

import asyncio
import base64
import io
from pathlib import Path
from typing import Optional

from worldcup.config import OUTPUT_DIR
from worldcup.data.wc2026_data import get_full_team_data, get_flag_url
from worldcup.renderer.theme import get_country_theme

# ── Safe-zone constants ────────────────────────────────────────────────────────
_SAFE_TOP = 250    # top boundary — clears phone status bar (fix #133)
_SAFE_BOT = 1400   # bottom boundary — clears phone nav bar (fix #133)
_SAFE_H   = 1150   # _SAFE_BOT - _SAFE_TOP


def _vcenter(content_h: int) -> int:
    """Y coordinate that vertically centres *content_h* px in the safe zone."""
    return _SAFE_TOP + max(0, (_SAFE_H - content_h) // 2)


def _stat_val_size(val: str) -> int:
    """240 px for 1-character values, 180 px for 2+ characters."""
    return 240 if len(str(val).strip()) <= 1 else 180


def _stat_box_h(val_size: int) -> int:
    """Total stat-box height for a given value font-size (uses reduced padding)."""
    # padding-top(24) + value(val_size) + label-margin(14) + label(36) + padding-bottom(20)
    return 24 + val_size + 14 + 36 + 20


# ── Colour helpers ─────────────────────────────────────────────────────────────

def _rgb(t: tuple) -> str:
    return f"rgb({t[0]},{t[1]},{t[2]})"

def _rgba(t: tuple, a: float) -> str:
    return f"rgba({t[0]},{t[1]},{t[2]},{a:.2f})"

def _hex(t: tuple) -> str:
    return f"#{t[0]:02x}{t[1]:02x}{t[2]:02x}"


# ── Pexels background fetch ───────────────────────────────────────────────────

def _file_to_data_uri(path: Path) -> str:
    """Encode a local image file as a base64 data URI for inline CSS embedding."""
    ext = path.suffix.lstrip(".").lower() or "jpeg"
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    return f"data:image/{ext};base64,{b64}"


def _fetch_background(query: str, outdir: Path, offset: int = 0) -> str:
    """
    Download a portrait Pexels photo for *query*.

    *offset* selects which photo from the 5-result page (0–4), so each player
    card can display a distinct background image while sharing one API call's
    worth of results.

    Caches the JPEG to outdir/bg_{hash}.jpg then returns a base64 data URI.
    Returns "" if PEXELS_API_KEY is absent or the download fails — the card
    silently falls back to the team-colour gradient.
    """
    import hashlib
    import os
    import httpx
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent.parent.parent / "backend" / ".env")
    api_key = os.getenv("PEXELS_API_KEY", "").strip()
    if not api_key:
        return ""

    qhash  = hashlib.md5(f"{query}:{offset}".lower().encode()).hexdigest()[:12]
    cached = (outdir / f"bg_{qhash}.jpg").resolve()
    if cached.exists() and cached.stat().st_size > 1_000:
        return _file_to_data_uri(cached)

    try:
        r = httpx.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": api_key},
            params={"query": query, "orientation": "portrait", "per_page": 5},
            timeout=15.0,
        )
        r.raise_for_status()
        photos = r.json().get("photos", [])
        if not photos:
            return ""
        photo = photos[offset % len(photos)]   # pick by offset for diversity
        src = photo.get("src", {})
        url = src.get("large2x") or src.get("large") or src.get("original", "")
        if not url:
            return ""
        img_r = httpx.get(url, timeout=40.0)
        img_r.raise_for_status()
        cached.parent.mkdir(parents=True, exist_ok=True)
        cached.write_bytes(img_r.content)
        print(f"[html_cards] BG cached -> {cached.name}")
        return _file_to_data_uri(cached)
    except Exception as exc:
        print(f"[html_cards] Pexels fetch failed for '{query}': {exc}")
        return ""


# ── Player photo → base64 PNG data-URL ────────────────────────────────────────

def _player_photo_src(name: str, accent: tuple, size: int = 300) -> str:
    """Return a base64 data-URL for the player photo (uses existing disk cache)."""
    try:
        from worldcup.data.photos import get_player_photo
        img = get_player_photo(name, size=size, accent=accent)
        buf = io.BytesIO()
        img.convert("RGBA").save(buf, format="PNG")
        enc = base64.b64encode(buf.getvalue()).decode()
        return f"data:image/png;base64,{enc}"
    except Exception:
        return ""


# ── Shared CSS base ────────────────────────────────────────────────────────────

_GF = "https://fonts.googleapis.com/css2?family=Oswald:wght@400;600;700&family=Roboto:wght@300;400;700&display=swap"

def _base_css(theme: dict, bg_photo: str = "", extra: str = "") -> str:
    acc      = _hex(theme["accent"])
    gt       = _hex(theme["gradient_top"])
    gb       = _hex(theme["gradient_bottom"])
    acc_dim  = _rgba(theme["accent"], 0.18)
    acc_glow = _rgba(theme["accent"], 0.55)
    acc_line = _rgba(theme["accent"], 0.40)

    # Background: photo + 58% dark overlay when available, else team gradient
    if bg_photo:
        card_bg = (
            f"background:\n"
            f"    linear-gradient(rgba(0,0,0,0.52),rgba(0,0,0,0.52)),\n"
            f"    url('{bg_photo}') center/cover no-repeat;"
        )
    else:
        card_bg = f"background: linear-gradient(170deg, {gt} 0%, {gb} 60%, #000508 100%);"

    return f"""
@import url('{_GF}');
*, *::before, *::after {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{
  width: 1080px; height: 1920px; overflow: hidden;
  font-family: 'Oswald', Impact, 'Arial Black', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
}}
.card {{
  position: relative; width: 1080px; height: 1920px; overflow: hidden;
  {card_bg}
}}
/* Step 4: Diagonal line texture at 3% opacity — always on */
.card::before {{
  content: '';
  position: absolute; inset: 0; pointer-events: none; z-index: 1;
  background-image: repeating-linear-gradient(
    45deg,
    rgba(255,255,255,0.03) 0px, rgba(255,255,255,0.03) 1px,
    transparent 1px, transparent 8px
  );
}}
/* Team colour accent sweep */
.card::after {{
  content: '';
  position: absolute; inset: 0; pointer-events: none; z-index: 1;
  background: linear-gradient(
    135deg,
    transparent 30%,
    {_rgba(theme["accent"], 0.06)} 50%,
    transparent 70%
  );
}}
/* Accent bars */
.top-bar {{
  position: absolute; top:0; left:0; right:0; height:10px; z-index:20;
  background: linear-gradient(90deg, {acc} 0%, {_rgba(theme["accent"],0.5)} 60%, transparent 100%);
}}
.bot-bar {{
  position: absolute; bottom:0; left:0; right:0; height:10px; z-index:20;
  background: linear-gradient(90deg, transparent 0%, {_rgba(theme["accent"],0.5)} 40%, {acc} 100%);
}}
/* Safe-zone content container: x 120–960, y 250–1400 */
.safe {{
  position: absolute;
  left: 120px; right: 120px;
  top: 250px; bottom: 520px;
  z-index: 5;
  display: flex; flex-direction: column;
}}
/* Typography */
.team-name {{
  font-size: 128px; font-weight: 700; letter-spacing: -3px;
  color: #fff; line-height: 1;
  text-shadow: 0 0 60px {acc_glow}, 0 4px 30px rgba(0,0,0,0.8);
}}
.section-title {{
  font-size: 38px; font-weight: 700; letter-spacing: 6px;
  color: {acc}; text-transform: uppercase;
  text-shadow: 0 0 30px {acc_glow};
}}
.label {{
  font-family: 'Roboto', Arial, sans-serif;
  font-size: 20px; font-weight: 400; letter-spacing: 3px;
  color: rgba(180,185,200,0.8); text-transform: uppercase;
}}
/* Stat boxes — reduced padding to accommodate hero-size numbers */
.stat-grid {{
  display: grid; grid-template-columns: 1fr 1fr; gap: 18px;
}}
.stat-box {{
  background: rgba(0,0,0,0.52);
  border: 1.5px solid {acc_line};
  border-radius: 18px;
  padding: 24px 20px 20px;
  text-align: center;
  box-shadow: 0 0 40px {acc_dim}, inset 0 1px 0 {_rgba(theme["accent"],0.12)};
}}
.stat-value {{
  font-size: 80px; font-weight: 700; color: {acc}; line-height: 1;
  letter-spacing: -2px;
  text-shadow: 0 0 50px {acc_glow};
}}
/* Step 3: Labels at 36px */
.stat-label {{
  font-family: 'Roboto', Arial, sans-serif;
  font-size: 36px; font-weight: 400; letter-spacing: 1.5px;
  color: rgba(170,175,195,0.75); margin-top: 14px; text-transform: uppercase;
}}
/* Divider */
.divider {{
  width: 100%; height: 1px; margin: 36px 0;
  background: linear-gradient(90deg, transparent 0%, {acc_line} 30%, {acc_line} 70%, transparent 100%);
}}
/* Pill badge */
.pill {{
  display: inline-block;
  padding: 10px 32px;
  background: {acc};
  border-radius: 999px;
  font-size: 28px; font-weight: 700; letter-spacing: 2px;
  color: #000; text-transform: uppercase;
}}
/* Progress bar */
.bar-track {{
  width: 100%; height: 22px;
  background: rgba(255,255,255,0.08);
  border-radius: 11px; overflow: hidden;
}}
.bar-fill {{
  height: 100%; border-radius: 11px;
  background: linear-gradient(90deg, {acc}, {_rgba(theme["accent"],0.6)});
  box-shadow: 0 0 20px {acc_glow};
}}
{extra}
"""


def _html(css: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><style>{css}</style></head>
<body><div class="card">
  <div class="top-bar"></div>
  <div class="bot-bar"></div>
  {body}
</div></body>
</html>"""


# ── Card 1 — HOOK ──────────────────────────────────────────────────────────────

def _hook_html(team: str, data: dict, theme: dict, bg_photo: str = "") -> str:
    group_id   = data["group_info"]["group"]
    flag_url   = data["flag_url"] or ""
    acc        = _hex(theme["accent"])
    acc_rgba   = _rgba(theme["accent"], 0.12)
    acc_border = _rgba(theme["accent"], 0.45)
    team_upper = team.upper()
    subtitle   = "FIFA WORLD CUP 2026"

    # Flag in the no-text top zone: centred at y≈80, inside card but above safe zone
    flag_block = f"""
      <div style="position:absolute;top:32px;left:0;right:0;
                  display:flex;justify-content:center;z-index:6;">
        <img src="{flag_url}" alt="{team}"
             style="height:180px;width:auto;object-fit:contain;
                    border-radius:8px;box-shadow:0 4px 40px rgba(0,0,0,0.7);">
      </div>""" if flag_url else ""

    # Group badge — top right, inside safe zone (below status bar)
    group_badge = f"""
      <div style="position:absolute;top:{_SAFE_TOP + 20}px;right:120px;
                  background:{acc};border-radius:12px;
                  padding:12px 28px;z-index:6;">
        <span style="font-size:22px;font-weight:700;letter-spacing:3px;color:#000;">
          GROUP {group_id}
        </span>
      </div>"""

    # Content block height: name(132) + subtitle(28+38) + divider(40+3) + date(50+24) = 315px
    # Centred in safe zone (1320px): top = 200 + (1320-315)//2 = 702
    _hook_content_h = 132 + 66 + 43 + 74   # = 315
    _hook_top = _vcenter(_hook_content_h)   # = 702

    body_inner = f"""
      <div style="position:absolute;left:120px;right:120px;
                  top:{_hook_top}px;text-align:center;z-index:5;">
        <div style="font-size:132px;font-weight:700;letter-spacing:-4px;
                    color:#fff;line-height:1;
                    text-shadow:0 0 80px {_rgba(theme['accent'],0.7)},0 4px 30px rgba(0,0,0,0.9),-1px -1px 0 rgba(0,0,0,0.8),1px -1px 0 rgba(0,0,0,0.8),-1px 1px 0 rgba(0,0,0,0.8),1px 1px 0 rgba(0,0,0,0.8);">
          {team_upper}
        </div>
        <div style="margin-top:28px;font-size:38px;font-weight:400;
                    letter-spacing:8px;color:{acc};
                    text-shadow:0 0 30px {_rgba(theme['accent'],0.5)};">
          {subtitle}
        </div>

        <!-- Decorative line -->
        <div style="width:160px;height:3px;margin:40px auto 0;
                    background:{acc};
                    box-shadow:0 0 20px {_rgba(theme['accent'],0.8)};
                    border-radius:2px;"></div>

        <!-- Tournament dates -->
        <div style="margin-top:50px;font-family:'Roboto',Arial,sans-serif;
                    font-size:24px;font-weight:300;letter-spacing:5px;
                    color:rgba(200,205,215,0.6);">
          JUNE 11 – JULY 19, 2026
        </div>
      </div>

      <!-- Hosts line pinned to bottom of safe zone -->
      <div style="position:absolute;bottom:{1920 - _SAFE_BOT + 20}px;left:120px;right:120px;
                  text-align:center;z-index:5;">
        <div style="font-family:'Roboto',Arial,sans-serif;
                    font-size:22px;font-weight:300;letter-spacing:4px;
                    color:rgba(180,185,200,0.5);">
          USA · CANADA · MEXICO
        </div>
      </div>

"""

    css = _base_css(theme, bg_photo=bg_photo)
    return _html(css, flag_block + group_badge + body_inner)


# ── Card 2 — HISTORY ──────────────────────────────────────────────────────────

def _history_html(team: str, data: dict, theme: dict, bg_photo: str = "") -> str:
    titles      = data["titles"]
    appearances = data["appearances"]
    best        = data["best_finish"]
    years       = data.get("titles_years", [])
    last_yr     = years[-1] if years else "N/A"
    recent      = data.get("recent_wc", [])
    acc         = _hex(theme["accent"])
    acc_glow    = _rgba(theme["accent"], 0.55)

    ratio   = min(1.0, appearances / 23)
    pct     = int(ratio * 100)
    fill_w  = int(840 * ratio)   # 840 = 960 - 120 safe width

    # Abbreviate long best_finish strings
    abbrev = {
        "Champions": "WINNER", "Runner-up": "FINALIST",
        "3rd Place": "3RD", "4th Place": "4TH",
        "Semi-final": "SEMI", "Quarter-final": "QF",
        "Round of 16": "R16", "Group Stage": "GRP",
    }
    best_short = next((v for k, v in abbrev.items() if k in best), best[:8].upper())

    # Recent WC result colours
    _result_colors = {
        "WIN":   "#FFD700", "FINAL": "#FFA040", "3RD": "#B0B0B0",
        "4TH":   "#909090", "SF":    "#7878A0", "QF":  "#5a5a8a",
        "R16":   "#464678", "GRP":   "#383860", "DNQ": "#282840",
    }

    # Step 3: hero number font sizes (1 digit→240px, 2+digits→180px)
    _titles_sz = _stat_val_size(str(titles))
    _appear_sz = _stat_val_size(str(appearances))
    _lastyr_sz = _stat_val_size(str(last_yr) if last_yr else "0")
    _best_box  = 24 + 54 + 14 + 36 + 20   # fixed 54px for text abbreviation

    # Grid height = max(row1) + 18 + max(row2)
    _row1_h = max(_stat_box_h(_titles_sz), _stat_box_h(_appear_sz))
    _row2_h = max(_best_box, _stat_box_h(_lastyr_sz))
    _stat_grid_h = _row1_h + 18 + _row2_h

    _bar_h      = 110
    _timeline_h = 220 if recent else 0
    _hist_content_h = _stat_grid_h + _bar_h + _timeline_h
    _header_bot = _SAFE_TOP + 80          # 80px header sits just below notch
    _hist_top = max(_header_bot + 20, _vcenter(_hist_content_h))

    recent_boxes = ""
    if recent:
        n     = len(recent)
        box_w = (840 - 20 * (n - 1)) // n
        for i, entry in enumerate(recent):
            yr  = entry.get("year", "")
            res = str(entry.get("result", "")).upper()
            clr = _result_colors.get(res, "#505070")
            # left_offset is relative to the parent div (which is already left:120px)
            left_offset = i * (box_w + 20)
            is_win = res == "WIN"
            recent_boxes += f"""
        <div style="position:absolute;left:{left_offset}px;width:{box_w}px;
                    top:0;height:120px;
                    background:rgba(0,0,0,0.45);
                    border:2px solid {clr};border-radius:14px;
                    display:flex;flex-direction:column;
                    align-items:center;justify-content:center;
                    box-shadow:{'0 0 20px ' + clr + '50' if is_win else 'none'};">
          <div style="font-family:'Roboto',Arial,sans-serif;font-size:22px;
                      font-weight:300;letter-spacing:2px;color:rgba(180,185,200,0.7);">
            {yr}
          </div>
          <div style="font-size:38px;font-weight:700;letter-spacing:1px;
                      color:{clr};margin-top:6px;
                      text-shadow:{'0 0 20px ' + clr if is_win else 'none'};">
            {res}
          </div>
        </div>"""

    body = f"""
      <!-- Header band: repositioned below notch area (fix #133) -->
      <div style="position:absolute;top:{_SAFE_TOP}px;left:0;right:0;height:80px;
                  background:linear-gradient(90deg,{acc} 0%,{_rgba(theme['accent'],0.7)} 100%);
                  z-index:6;display:flex;align-items:center;justify-content:center;">
        <div style="font-size:44px;font-weight:700;letter-spacing:8px;
                    color:#000;text-shadow:none;">
          THE RECORD
        </div>
      </div>

      <!-- SAFE ZONE content — vertically centred -->
      <div style="position:absolute;left:120px;right:120px;top:{_hist_top}px;z-index:5;">

        <!-- 2×2 stat grid — hero numbers -->
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:18px;">

          <div class="stat-box">
            <div style="font-size:{_titles_sz}px;font-weight:700;color:{acc};
                        line-height:1;letter-spacing:-2px;
                        text-shadow:0 0 60px {acc_glow};">{titles}</div>
            <div class="stat-label">WC Titles</div>
          </div>

          <div class="stat-box">
            <div style="font-size:{_appear_sz}px;font-weight:700;color:{acc};
                        line-height:1;letter-spacing:-2px;
                        text-shadow:0 0 60px {acc_glow};">{appearances}</div>
            <div class="stat-label">Appearances</div>
          </div>

          <div class="stat-box">
            <div style="font-size:54px;font-weight:700;color:{acc};line-height:1;
                        text-shadow:0 0 30px {acc_glow};">{best_short}</div>
            <div class="stat-label">Best Finish</div>
          </div>

          <div class="stat-box">
            <div style="font-size:{_lastyr_sz}px;font-weight:700;color:{acc};
                        line-height:1;letter-spacing:-2px;
                        text-shadow:0 0 60px {acc_glow};">{last_yr}</div>
            <div class="stat-label">Last Title</div>
          </div>

        </div>

        <!-- Participation bar -->
        <div style="margin-top:52px;">
          <div style="display:flex;justify-content:space-between;
                      align-items:baseline;margin-bottom:16px;">
            <div class="label">WC Participation Rate</div>
            <div style="font-size:32px;font-weight:700;color:{acc};
                        text-shadow:0 0 20px {acc_glow};">{pct}%</div>
          </div>
          <div class="bar-track">
            <div class="bar-fill" style="width:{fill_w}px;"></div>
          </div>
        </div>

        <!-- Recent WC mini-timeline -->
        {"" if not recent else f'''
        <div style="margin-top:52px;">
          <div class="label" style="margin-bottom:18px;letter-spacing:3px;">Recent WC Results</div>
          <div style="position:relative;height:130px;">
            {recent_boxes}
          </div>
        </div>
        '''}

      </div>"""

    css = _base_css(theme, bg_photo=bg_photo,
                    extra=".stat-box{background:rgba(0,0,0,0.75)!important;}")
    return _html(css, body)


# ── Card 3 — PLAYER ───────────────────────────────────────────────────────────

def _player_html(player: dict, team: str, theme: dict, bg_photo: str = "") -> str:
    name       = player.get("name", "Player")
    pos        = player.get("position", "")
    club       = player.get("club", "")
    goals      = player.get("country_goals") or player.get("goals", 0)
    caps       = player.get("caps", 0)
    club_goals = player.get("club_goals", 0)
    mval       = player.get("market_value", "N/A") or "N/A"
    quote      = player.get("hype_quote", "")
    acc        = _hex(theme["accent"])
    acc_glow   = _rgba(theme["accent"], 0.55)

    _photo_size = 240   # defined early; recalculated below with layout context
    photo_src  = _player_photo_src(name, theme["accent"], size=_photo_size)
    photo_html = f"""
      <img src="{photo_src}" alt="{name}"
           style="width:{_photo_size}px;height:{_photo_size}px;object-fit:cover;
                  border-radius:50%;
                  border:4px solid {acc};
                  box-shadow:0 0 60px {_rgba(theme['accent'],0.5)};
                  display:block;margin:0 auto;">
    """ if photo_src else f"""
      <div style="width:{_photo_size}px;height:{_photo_size}px;border-radius:50%;
                  background:rgba(0,0,0,0.4);border:4px solid {acc};
                  display:flex;align-items:center;justify-content:center;
                  margin:0 auto;overflow:hidden;">
        <svg viewBox="0 0 80 110" width="{int(_photo_size*0.72)}" height="{int(_photo_size*0.72)}"
             xmlns="http://www.w3.org/2000/svg">
          <circle cx="40" cy="14" r="12" fill="{acc}" opacity="0.85"/>
          <path d="M32 30 Q40 26 48 30 L54 65 L44 65 L42 78 L38 78 L36 65 L26 65 Z"
                fill="{acc}" opacity="0.85"/>
          <path d="M28 35 Q14 48 12 62 L20 64 Q24 52 30 42 Z"
                fill="{acc}" opacity="0.85"/>
          <path d="M52 35 Q65 45 68 58 L60 60 Q58 50 50 42 Z"
                fill="{acc}" opacity="0.85"/>
          <path d="M30 65 L22 95 L30 95 L36 72 Z" fill="{acc}" opacity="0.85"/>
          <path d="M50 65 L58 95 L50 95 L44 72 Z" fill="{acc}" opacity="0.85"/>
          <circle cx="62" cy="100" r="9" fill="{acc}" opacity="0.6"/>
        </svg>
      </div>"""

    pos_labels = {
        "FW": "FORWARD", "MF": "MIDFIELDER",
        "DF": "DEFENDER", "GK": "GOALKEEPER",
    }
    pos_full = pos_labels.get(pos.upper(), pos.upper())

    quote_html = f"""
      <div style="margin-top:36px;text-align:center;
                  font-family:'Roboto',Arial,sans-serif;
                  font-size:28px;font-weight:300;font-style:italic;
                  color:rgba(200,205,215,0.75);
                  line-height:1.45;padding:0 20px;">
        &ldquo;{quote}&rdquo;
      </div>""" if quote else ""

    # Step 3: hero number sizing per stat value
    _goals_sz = _stat_val_size(str(goals))
    _caps_sz  = _stat_val_size(str(caps))
    _cgl_sz   = _stat_val_size(str(club_goals))
    _mval_box = 24 + 40 + 14 + 36 + 20   # fixed 40px for mval text ("180M EUR")

    _row1_h = max(_stat_box_h(_goals_sz), _stat_box_h(_caps_sz))
    _row2_h = max(_stat_box_h(_cgl_sz), _mval_box)
    _play_stat_h = _row1_h + 16 + _row2_h

    # Text block heights: name(82)+pill(72)+club(52)+stats(38+grid)+quote
    _quote_h  = 117 if quote else 0
    _text_h   = 82 + 72 + 52 + 38 + _play_stat_h + _quote_h
    _text_top = _vcenter(_text_h)
    # Photo hangs 30px above text block; may extend above safe zone (image, not text)
    _photo_top   = max(130, _text_top - 30 - _photo_size)

    body = f"""
      <!-- Header band -->
      <div style="position:absolute;top:0;left:0;right:0;height:130px;
                  background:linear-gradient(90deg,{acc} 0%,{_rgba(theme['accent'],0.7)} 100%);
                  z-index:6;display:flex;align-items:center;justify-content:center;">
        <div style="font-size:44px;font-weight:700;letter-spacing:6px;color:#000;">
          PLAYERS TO WATCH
        </div>
      </div>

      <!-- Photo — image may overlap safe zone top boundary (images exempt from text rule) -->
      <div style="position:absolute;top:{_photo_top}px;left:0;right:0;z-index:5;">
        {photo_html}
      </div>

      <!-- Text block — vertically centred in safe zone -->
      <div style="position:absolute;left:120px;right:120px;top:{_text_top}px;z-index:5;
                  text-align:center;">

        <!-- Player name -->
        <div style="font-size:82px;font-weight:700;letter-spacing:-2px;
                    color:#fff;line-height:1;
                    text-shadow:0 0 60px {acc_glow};">
          {name}
        </div>

        <!-- Position pill -->
        <div style="margin-top:24px;">
          <span class="pill">{pos_full}</span>
        </div>

        <!-- Club -->
        <div style="margin-top:22px;font-family:'Roboto',Arial,sans-serif;
                    font-size:30px;font-weight:400;letter-spacing:2px;
                    color:rgba(180,185,200,0.75);">
          {club}
        </div>

        <!-- 2×2 stat grid — hero numbers -->
        <div style="margin-top:38px;
                    display:grid;grid-template-columns:1fr 1fr;gap:16px;">
          <div class="stat-box">
            <div style="font-size:{_goals_sz}px;font-weight:700;color:{acc};
                        line-height:1;letter-spacing:-2px;
                        text-shadow:0 0 60px {acc_glow};">{goals}</div>
            <div class="stat-label">Intl Goals</div>
          </div>
          <div class="stat-box">
            <div style="font-size:{_caps_sz}px;font-weight:700;color:{acc};
                        line-height:1;letter-spacing:-2px;
                        text-shadow:0 0 60px {acc_glow};">{caps}</div>
            <div class="stat-label">Caps</div>
          </div>
          <div class="stat-box">
            <div style="font-size:{_cgl_sz}px;font-weight:700;color:{acc};
                        line-height:1;letter-spacing:-2px;
                        text-shadow:0 0 60px {acc_glow};">{club_goals}</div>
            <div class="stat-label">Club Gls</div>
          </div>
          <div class="stat-box">
            <div style="font-size:40px;font-weight:700;color:{acc};line-height:1;
                        text-shadow:0 0 30px {acc_glow};">{mval}</div>
            <div class="stat-label">Value</div>
          </div>
        </div>

        {quote_html}

      </div>"""

    css = _base_css(theme, bg_photo=bg_photo)
    return _html(css, body)


# ── Card 4 — GROUP ────────────────────────────────────────────────────────────

def _group_html(team: str, data: dict, theme: dict, bg_photo: str = "") -> str:
    group_id    = data["group_info"]["group"]
    group_teams = data["group_info"].get("teams", [])
    acc         = _hex(theme["accent"])
    acc_rgba    = _rgba(theme["accent"], 0.35)
    acc_glow    = _rgba(theme["accent"], 0.6)

    rows_html = ""
    for i, t_name in enumerate(group_teams[:4]):
        is_hl       = t_name.lower() == team.lower()
        flag_url    = get_flag_url(t_name, width=160)
        flag_img    = f'<img src="{flag_url}" alt="{t_name}" style="height:72px;width:auto;object-fit:contain;border-radius:6px;">' if flag_url else ""
        row_bg      = f"rgba(60,55,80,0.80)" if is_hl else "rgba(30,30,50,0.70)"
        row_border  = f"border:2px solid {acc};" if is_hl else "border:1.5px solid rgba(255,255,255,0.08);"
        name_color  = acc if is_hl else "#e0e4ee"
        name_size   = "40px" if len(t_name) <= 12 else "32px"
        badge       = f'<span style="background:{acc};color:#000;font-size:18px;font-weight:700;letter-spacing:2px;padding:6px 18px;border-radius:999px;margin-left:auto;white-space:nowrap;">YOUR TEAM</span>' if is_hl else ""
        glow        = f"box-shadow:0 0 30px {acc_rgba};" if is_hl else ""

        rows_html += f"""
        <div style="display:flex;align-items:center;gap:24px;
                    background:{row_bg};{row_border}border-radius:16px;
                    padding:22px 28px;{glow}">
          {flag_img}
          <div style="font-size:{name_size};font-weight:{'700' if is_hl else '400'};
                      color:{name_color};letter-spacing:1px;flex:1;">
            {t_name}
          </div>
          {badge}
        </div>"""

    # Content block heights (px):
    #   letter: 180  subtitle: −10 margin+30 font = 20 effective
    #   gap: 48  each row: 22+72+22=116  row gaps: (n−1)×18
    _n_teams      = len(group_teams[:4])
    _row_h        = 116
    _rows_total   = _n_teams * _row_h + max(0, _n_teams - 1) * 18
    _grp_content_h = 180 + 20 + 48 + _rows_total   # = 766 for 4 teams
    _grp_top = _vcenter(_grp_content_h)              # = 477 for 4 teams

    body = f"""
      <!-- Content block — vertically centred in safe zone -->
      <div style="position:absolute;left:120px;right:120px;top:{_grp_top}px;
                  text-align:center;z-index:5;">

        <!-- GROUP letter — massive -->
        <div style="font-size:180px;font-weight:700;letter-spacing:-8px;
                    color:{acc};line-height:1;
                    text-shadow:0 0 100px {acc_glow},0 0 40px {acc_glow};">
          {group_id}
        </div>
        <div style="font-size:30px;font-weight:400;letter-spacing:5px;
                    color:rgba(255,255,255,0.85);margin-top:-10px;">
          GROUP STAGE · FIFA WORLD CUP 2026
        </div>

        <!-- Team rows -->
        <div style="margin-top:48px;display:flex;flex-direction:column;gap:18px;
                    text-align:left;">
          {rows_html}
        </div>

      </div>"""

    css = _base_css(theme, bg_photo=bg_photo)
    return _html(css, body)


# ── Card 5 — CTA ──────────────────────────────────────────────────────────────

def _cta_html(team: str, data: dict, theme: dict, bg_photo: str = "") -> str:
    acc      = _hex(theme["accent"])
    acc_glow = _rgba(theme["accent"], 0.6)
    t_name   = team.title()
    group_id = data["group_info"]["group"]

    # Content block heights (px):
    #   label: 22  CAN-block: 40+76+101+76=293  divider: 52+4+52=108
    #   COMMENT: 74  YOUR PREDICTION: 8+44=52  date: 16+32=48  → total: 597
    _cta_content_h = 22 + 293 + 108 + 74 + 52 + 48   # = 597
    _cta_top = _vcenter(_cta_content_h)                # = 561

    body = f"""
      <!-- Main block — vertically centred in safe zone -->
      <div style="position:absolute;left:120px;right:120px;top:{_cta_top}px;
                  text-align:center;z-index:5;">

        <div class="label" style="letter-spacing:5px;font-size:22px;">
          YOUR PREDICTION
        </div>

        <div style="margin-top:40px;font-size:72px;font-weight:700;
                    letter-spacing:-2px;color:#fff;line-height:1.05;
                    text-shadow:0 0 50px rgba(255,255,255,0.25);">
          CAN
          <span style="color:{acc};display:block;font-size:96px;
                       text-shadow:0 0 80px {acc_glow};">
            {team.upper()}
          </span>
          WIN IT ALL?
        </div>

        <!-- Accent divider -->
        <div style="width:200px;height:4px;margin:52px auto;
                    background:{acc};border-radius:2px;
                    box-shadow:0 0 30px {acc_glow};"></div>

        <!-- Comment prompt -->
        <div style="font-size:74px;font-weight:700;letter-spacing:-1px;
                    color:#ffffff;
                    text-shadow:0 0 50px {acc_glow};">
          COMMENT
        </div>
        <div style="font-size:44px;font-weight:700;letter-spacing:2px;
                    color:rgba(255,255,255,0.85);margin-top:8px;">
          YOUR PREDICTION
        </div>
        <div style="margin-top:16px;font-family:'Roboto',Arial,sans-serif;
                    font-size:32px;font-weight:300;
                    color:rgba(180,185,200,0.65);">
          Group {group_id} · FIFA World Cup 2026
        </div>

      </div>

      <!-- Subscribe line — 200px above previous position, safely inside safe zone -->
      <div style="position:absolute;left:120px;right:120px;bottom:630px;
                  text-align:center;z-index:5;">
        <div style="font-family:'Roboto',Arial,sans-serif;
                    font-size:24px;font-weight:300;letter-spacing:3px;
                    color:rgba(160,165,180,0.55);">
          LIKE · FOLLOW · SUBSCRIBE FOR DAILY WC 2026
        </div>
      </div>

"""

    css = _base_css(theme, bg_photo=bg_photo)
    return _html(css, body)


# ── Playwright screenshot engine ───────────────────────────────────────────────

async def _screenshot_all(
    cards: list[tuple[str, Path]],
    timeout_ms: int = 15_000,
) -> list[Path]:
    """Launch one browser, screenshot every (html_str, path) pair, return paths."""
    from playwright.async_api import async_playwright

    saved: list[Path] = []
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-gpu"],
        )
        page = await browser.new_page(
            viewport={"width": 1080, "height": 1920},
            device_scale_factor=1,
        )
        for html_str, out_path in cards:
            abs_path = out_path.resolve()
            abs_path.parent.mkdir(parents=True, exist_ok=True)
            await page.set_content(html_str, wait_until="networkidle",
                                   timeout=timeout_ms)
            await page.screenshot(path=str(abs_path), clip={
                "x": 0, "y": 0, "width": 1080, "height": 1920,
            })
            saved.append(out_path)
            print(f"[html_cards] Saved {out_path.name}")
        await browser.close()
    return saved


# ── Public API ─────────────────────────────────────────────────────────────────

def render_team_cards(
    team: str,
    output_dir: Optional[Path] = None,
    players: int = 3,
) -> list[Path]:
    """
    Render all card segments for *team* and return list of saved PNG paths.

    Parameters
    ----------
    team:       Team name matching wc2026_data.py key (e.g. "Brazil")
    output_dir: Override save directory (default: worldcup/output/cards/{team}/)
    players:    Number of player cards to render (1–5, default 3)
    """
    data   = get_full_team_data(team)
    theme  = get_country_theme(team)
    slug   = team.lower().replace(" ", "_")
    outdir = output_dir or (OUTPUT_DIR / "cards" / slug)
    outdir.mkdir(parents=True, exist_ok=True)

    key_players = data.get("key_players", [])[:players]

    # Step 1: fetch Pexels backgrounds (cached; silently skipped if no API key)
    print(f"[html_cards] Fetching backgrounds for {team}...")
    _PLAYER_QUERY = "football player action stadium crowd"
    _bg = {
        "hook":    _fetch_background(f"{team} football fans stadium",           outdir),
        "history": _fetch_background("football world cup trophy close up gold", outdir),
        "player":  [                                   # distinct photo per player card
            _fetch_background(_PLAYER_QUERY, outdir, offset=i)
            for i in range(len(key_players))
        ],
        "group":   _fetch_background("football stadium crowd night lights",     outdir),
        "cta":     _fetch_background("football stadium night lights crowd",     outdir),
    }

    # Build (html, path) list in pipeline order
    cards: list[tuple[str, Path]] = [
        (_hook_html(team, data, theme,    bg_photo=_bg["hook"]),    outdir / "hook.png"),
        (_history_html(team, data, theme, bg_photo=_bg["history"]), outdir / "history.png"),
        *[
            (
                _player_html(p, team, theme,
                             bg_photo=_bg["player"][i] if i < len(_bg["player"]) else ""),
                outdir / f"player_{i}.png",
            )
            for i, p in enumerate(key_players)
        ],
        (_group_html(team, data, theme,   bg_photo=_bg["group"]),   outdir / "group.png"),
        (_cta_html(team, data, theme,     bg_photo=_bg["cta"]),     outdir / "cta.png"),
    ]

    print(f"[html_cards] Rendering {len(cards)} cards for {team}...")
    return asyncio.run(_screenshot_all(cards))
