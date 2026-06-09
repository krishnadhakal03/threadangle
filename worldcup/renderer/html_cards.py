"""
HTML + Playwright card renderer for World Cup 2026 videos.
Redesigned to FIFA UT layout with gold trim (Issue #221).

Public API
----------
render_team_cards(team, output_dir=None) -> list[Path]

Card segments (in pipeline order):
  hook.png       — team intro: solid team-colour bg, 220px flag, gold group badge
  history.png    — THE RECORD: giant bg title number, gold-border stat grid
  player_0.png   — FIFA UT card: full-bleed photo, OVR circle, gold stats panel
  player_1.png   — FIFA UT card
  player_2.png   — FIFA UT card
  group.png      — solid bg, circular 100px flags, gold highlight row
  cta.png        — high-contrast COMMENT, gold divider

YouTube Shorts safe zones (no text placed outside these boundaries):
  Horizontal: 120 px margin each side  →  content in x: 120–960
  Top:        250 px from top          →  text starts at y >= 250 (clears status bar)
  Bottom:     470 px from bottom       →  text ends at y <= 1450 (clears nav bar)
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
_SAFE_BOT = 1450   # bottom boundary — clears phone nav bar (stricter)
_SAFE_H   = 1200   # _SAFE_BOT - _SAFE_TOP

GOLD = "#D4A843"   # gold trim colour used across all cards


def _vcenter(content_h: int) -> int:
    """Y coordinate that vertically centres *content_h* px in the safe zone."""
    return _SAFE_TOP + max(0, (_SAFE_H - content_h) // 2)


def _stat_val_size(val: str) -> int:
    """240 px for 1-character values, 180 px for 2+ characters."""
    return 240 if len(str(val).strip()) <= 1 else 180


def _stat_box_h(val_size: int) -> int:
    """Total stat-box height for a given value font-size."""
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
    ext = path.suffix.lstrip(".").lower() or "jpeg"
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    return f"data:image/{ext};base64,{b64}"


def _fetch_background(query: str, outdir: Path, offset: int = 0) -> str:
    """
    Download a portrait Pexels photo for *query*.

    *offset* selects which photo from the 5-result page (0-4) so player
    cards can each display a distinct background image.

    Caches the JPEG to outdir/bg_{hash}.jpg then returns a base64 data URI.
    Returns "" if PEXELS_API_KEY is absent or the download fails.
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
        photo = photos[offset % len(photos)]
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


# ── Player photo -> base64 PNG data-URL ────────────────────────────────────────

def _player_photo_src(name: str, accent: tuple, size: int = 300) -> str:
    try:
        from worldcup.data.photos import get_player_photo
        img = get_player_photo(name, size=size, accent=accent)
        if img is None:           # no real photo — caller uses typographic fallback
            return ""
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
.card::before {{
  content: '';
  position: absolute; inset: 0; pointer-events: none; z-index: 1;
  background-image: repeating-linear-gradient(
    45deg,
    rgba(255,255,255,0.03) 0px, rgba(255,255,255,0.03) 1px,
    transparent 1px, transparent 8px
  );
}}
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
.top-bar {{
  position: absolute; top:0; left:0; right:0; height:10px; z-index:20;
  background: linear-gradient(90deg, {acc} 0%, {_rgba(theme["accent"],0.5)} 60%, transparent 100%);
}}
.bot-bar {{
  position: absolute; bottom:0; left:0; right:0; height:10px; z-index:20;
  background: linear-gradient(90deg, transparent 0%, {_rgba(theme["accent"],0.5)} 40%, {acc} 100%);
}}
.safe {{
  position: absolute;
  left: 120px; right: 120px;
  top: 250px; bottom: 470px;
  z-index: 5;
  display: flex; flex-direction: column;
}}
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
.stat-label {{
  font-family: 'Roboto', Arial, sans-serif;
  font-size: 36px; font-weight: 400; letter-spacing: 1.5px;
  color: rgba(170,175,195,0.75); margin-top: 14px; text-transform: uppercase;
}}
.divider {{
  width: 100%; height: 1px; margin: 36px 0;
  background: linear-gradient(90deg, transparent 0%, {acc_line} 30%, {acc_line} 70%, transparent 100%);
}}
.pill {{
  display: inline-block;
  padding: 10px 32px;
  background: {acc};
  border-radius: 999px;
  font-size: 28px; font-weight: 700; letter-spacing: 2px;
  color: #000; text-transform: uppercase;
}}
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


# ── Card 1 — HOOK (solid team gradient — Issue #221) ──────────────────────────

def _hook_html(team: str, data: dict, theme: dict, bg_photo: str = "") -> str:
    group_id   = data["group_info"]["group"]
    flag_url   = data.get("flag_url") or ""
    gt         = _hex(theme["gradient_top"])
    gb         = _hex(theme["gradient_bottom"])
    acc        = _hex(theme["accent"])
    ar, ag, ab = theme["accent"]
    team_upper = team.upper()

    # Solid team-colour gradient — no photo overlay
    _card_bg = f"linear-gradient(160deg, {gt} 0%, {gb} 55%, #000508 100%)"
    extra = (
        f".card{{background:{_card_bg}!important;}}"
        f".card::before{{background-image:"
        f"radial-gradient(circle at 70% 30%, rgba(255,255,255,0.04) 0%, transparent 50%),"
        f"radial-gradient(circle at 30% 70%, rgba(255,255,255,0.03) 0%, transparent 40%)!important;}}"
    )

    # ── 1. Watermark — full-width div, text-align:center, rotated across card ──
    # left:0;right:0 makes the div span the full 1080px card width so the
    # transform-origin is the true card centre, bleeding equally off both sides.
    watermark = (
        f'<div style="position:absolute;top:50%;left:0;right:0;'
        f'transform:translateY(-50%) rotate(-15deg);'
        f'font-size:300px;font-weight:700;color:#fff;opacity:0.04;'
        f'z-index:0;text-align:center;pointer-events:none;'
        f'letter-spacing:-8px;font-family:Oswald,Impact,Arial,sans-serif;">'
        f'FIFA WORLD CUP 2026</div>'
    )

    # ── 2. Radial glow behind team name — centered on card ────────────────
    glow = (
        f'<div style="position:absolute;top:50%;left:50%;'
        f'transform:translate(-50%,-50%);'
        f'width:700px;height:500px;border-radius:50%;'
        f'background:radial-gradient(ellipse 600px 400px at center,'
        f'rgba({ar},{ag},{ab},0.15) 0%,transparent 70%);'
        f'z-index:1;pointer-events:none;"></div>'
    )

    # ── 3. Group badge — gold pill, top-right (stays in safe zone) ────────
    group_badge = (
        f'<div style="position:absolute;top:{_SAFE_TOP + 20}px;right:60px;'
        f'background:{GOLD};border-radius:12px;padding:14px 32px;z-index:6;">'
        f'<span style="font-size:24px;font-weight:700;letter-spacing:3px;color:#000;">'
        f'GROUP {group_id}</span></div>'
    )

    # ── 4. Content wrapper — flag at y=400, name at y≈640 ────────────────
    # top:400px + flag(200px) + gap(40px) = name starts at y=640
    flag_html = (
        f'<div style="display:flex;justify-content:center;margin-bottom:40px;">'
        f'<img src="{flag_url}" alt="{team}"'
        f' style="width:200px;height:200px;border-radius:50%;object-fit:cover;'
        f'box-shadow:0 8px 60px rgba(0,0,0,0.6),'
        f'0 0 0 4px rgba({ar},{ag},{ab},0.4);">'
        f'</div>'
    ) if flag_url else ""

    content = f"""
    <div style="position:absolute;left:60px;right:60px;
                top:400px;
                text-align:center;z-index:5;">

      {flag_html}

      <div style="font-size:160px;font-weight:700;letter-spacing:-6px;
                  color:#fff;line-height:1;
                  text-shadow:0 0 100px rgba({ar},{ag},{ab},0.7),
                              0 4px 40px rgba(0,0,0,0.9),
                              -1px -1px 0 rgba(0,0,0,0.7),
                               1px  1px 0 rgba(0,0,0,0.7);">
        {team_upper}
      </div>

      <div style="margin-top:30px;font-size:38px;font-weight:400;
                  letter-spacing:8px;color:{acc};
                  text-shadow:0 0 30px rgba({ar},{ag},{ab},0.5);">
        FIFA WORLD CUP 2026
      </div>

      <div style="width:200px;height:4px;margin:36px auto 0;
                  background:{GOLD};border-radius:2px;
                  box-shadow:0 0 20px rgba(212,168,67,0.6);"></div>

      <div style="margin-top:36px;font-family:'Roboto',Arial,sans-serif;
                  font-size:24px;font-weight:300;letter-spacing:5px;
                  color:rgba(200,205,215,0.6);">
        JUNE 11 - JULY 19, 2026
      </div>
    </div>"""

    css = _base_css(theme, extra=extra)
    return _html(css, watermark + glow + group_badge + content)


# ── Card 2 — HISTORY (giant bg number, gold borders — Issue #221) ─────────────

def _history_html(team: str, data: dict, theme: dict, bg_photo: str = "") -> str:
    titles      = data["titles"]
    appearances = data["appearances"]
    best        = data["best_finish"]
    years       = data.get("titles_years", [])
    last_yr     = years[-1] if years else "N/A"
    recent      = data.get("recent_wc", [])
    acc         = _hex(theme["accent"])
    acc_glow    = _rgba(theme["accent"], 0.55)

    ratio  = min(1.0, appearances / 23)
    pct    = int(ratio * 100)
    fill_w = int(840 * ratio)

    abbrev = {
        "Champions": "WINNER", "Runner-up": "FINALIST",
        "3rd Place": "3RD", "4th Place": "4TH",
        "Semi-final": "SEMI", "Quarter-final": "QF",
        "Round of 16": "R16", "Group Stage": "GRP",
    }
    best_short = next((v for k, v in abbrev.items() if k in best), best[:8].upper())

    _result_colors = {
        "WIN":   "#FFD700", "FINAL": "#FFA040", "3RD": "#B0B0B0",
        "4TH":   "#909090", "SF":    "#7878A0", "QF":  "#5a5a8a",
        "R16":   "#464678", "GRP":   "#383860", "DNQ": "#282840",
    }

    _titles_sz = _stat_val_size(str(titles))
    _appear_sz = _stat_val_size(str(appearances))
    _lastyr_sz = _stat_val_size(str(last_yr) if last_yr else "0")
    _best_box  = 24 + 54 + 14 + 36 + 20

    _row1_h = max(_stat_box_h(_titles_sz), _stat_box_h(_appear_sz))
    _row2_h = max(_best_box, _stat_box_h(_lastyr_sz))
    _stat_grid_h = _row1_h + 18 + _row2_h

    _bar_h      = 110
    _timeline_h = 220 if recent else 0
    _hist_content_h = _stat_grid_h + _bar_h + _timeline_h
    _header_bot = _SAFE_TOP + 100          # 100px header below notch
    _hist_top = max(_header_bot + 20, _vcenter(_hist_content_h))  # min 370px

    recent_boxes = ""
    if recent:
        n     = len(recent)
        box_w = (840 - 20 * (n - 1)) // n
        for i, entry in enumerate(recent):
            yr  = entry.get("year", "")
            res = str(entry.get("result", "")).upper()
            clr = _result_colors.get(res, "#505070")
            left_offset = i * (box_w + 20)
            is_win = res == "WIN"
            recent_boxes += (
                f'<div style="position:absolute;left:{left_offset}px;width:{box_w}px;'
                f'top:0;height:120px;background:rgba(0,0,0,0.45);'
                f'border:2px solid {clr};border-radius:14px;'
                f'display:flex;flex-direction:column;align-items:center;justify-content:center;'
                f'box-shadow:{("0 0 20px " + clr + "50") if is_win else "none"};">'
                f'<div style="font-family:Roboto,Arial,sans-serif;font-size:22px;'
                f'font-weight:300;letter-spacing:2px;color:rgba(180,185,200,0.7);">{yr}</div>'
                f'<div style="font-size:38px;font-weight:700;letter-spacing:1px;'
                f'color:{clr};margin-top:6px;'
                f'text-shadow:{("0 0 20px " + clr) if is_win else "none"};">{res}</div>'
                f'</div>'
            )

    # Giant decorative title count behind stat grid (opacity 0.06, z-index:1)
    titles_giant = (
        f'<div style="position:absolute;left:20px;top:{_SAFE_TOP}px;'
        f'font-size:520px;font-weight:700;line-height:1;'
        f'color:{acc};opacity:0.06;z-index:1;letter-spacing:-20px;'
        f'pointer-events:none">{titles}</div>'
    )

    body = f"""
    {titles_giant}

    <!-- Header band: team-colour to gold gradient, below notch -->
    <div style="position:absolute;top:{_SAFE_TOP}px;left:0;right:0;height:100px;
                background:linear-gradient(90deg,{acc} 0%,{GOLD} 100%);
                z-index:6;display:flex;align-items:center;justify-content:center;">
      <div style="font-size:44px;font-weight:700;letter-spacing:8px;
                  color:#000;text-shadow:none;">
        THE RECORD
      </div>
    </div>

    <!-- Stat grid — gold borders, TITLES in gold, others in accent -->
    <div style="position:absolute;left:120px;right:120px;top:{_hist_top}px;z-index:5;">

      <div style="display:grid;grid-template-columns:1fr 1fr;gap:18px;">

        <div class="stat-box">
          <div style="font-size:{_titles_sz}px;font-weight:700;color:{GOLD};
                      line-height:1;letter-spacing:-2px;
                      text-shadow:0 0 60px rgba(212,168,67,0.6);">{titles}</div>
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
          <div style="font-size:32px;font-weight:700;color:{GOLD};
                      text-shadow:0 0 20px rgba(212,168,67,0.5);">{pct}%</div>
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

    # Pure solid dark bg — no bg_photo, no semi-transparent rgba bleeding onto white
    extra = (
        f".stat-box{{background:rgba(0,0,0,0.80)!important;"
        f"border:1.5px solid {GOLD}!important;}}"
        f".card{{background:linear-gradient(170deg,#1a1a2e 0%,#16213e 40%,#0a0a14 100%)!important;}}"
    )
    css = _base_css(theme, extra=extra)   # bg_photo intentionally not passed
    return _html(css, body)


# ── Card 3 — PLAYER (FIFA UT layout — Issue #221) ────────────────────────────

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

    # OVR proxy: goals scaled to 70-99
    ovr = min(99, max(70, 70 + int(goals * 0.6)))

    country_code = team.upper()[:3]
    pos_labels   = {"FW": "FWD", "MF": "MID", "DF": "DEF", "GK": "GK"}
    pos_short    = pos_labels.get(pos.upper(), pos.upper()[:3] if pos else "FWD")
    display_name = name.split()[-1].upper() if len(name) > 14 else name.upper()

    # Photo at 600px for full-bleed quality
    photo_src = _player_photo_src(name, theme["accent"], size=600)

    # ── Photo zone: top 67% of card ───────────────────────────────────────
    if photo_src:
        photo_zone = (
            f'<div style="position:absolute;top:0;left:0;right:0;height:1280px;overflow:hidden;">'
            f'<img src="{photo_src}" alt="{name}"'
            f' style="width:100%;height:100%;object-fit:cover;object-position:center top;">'
            f'<div style="position:absolute;inset:0;'
            f'background:linear-gradient(180deg,'
            f'transparent 50%,rgba(0,0,0,0.6) 75%,rgba(0,0,0,0.95) 100%);"></div>'
            f'</div>'
        )
    elif bg_photo:
        photo_zone = (
            f'<div style="position:absolute;top:0;left:0;right:0;height:1280px;overflow:hidden;">'
            f'<div style="position:absolute;inset:0;'
            f'background:url(\'{bg_photo}\') center top/cover no-repeat;"></div>'
            f'<div style="position:absolute;inset:0;'
            f'background:linear-gradient(180deg,'
            f'rgba(0,0,0,0.15) 0%,transparent 40%,rgba(0,0,0,0.95) 100%);"></div>'
            f'</div>'
        )
    else:
        # Typographic poster — no photo available.
        # Player's last name rendered large, like a print poster.
        last_name = name.split()[-1].upper()
        # Scale font to fit 960px content width (Oswald 700 ~1.6× width ratio)
        poster_fs = min(280, max(120, int(1100 // max(len(last_name), 4))))
        photo_zone = (
            f'<div style="position:absolute;top:0;left:0;right:0;height:1280px;'
            f'background:#000;display:flex;flex-direction:column;'
            f'align-items:center;justify-content:center;overflow:hidden;">'
            # Team-colour radial glow behind the name
            f'<div style="position:absolute;inset:0;'
            f'background:radial-gradient(ellipse at 50% 55%,'
            f'{_rgba(theme["accent"], 0.28)} 0%,transparent 65%);'
            f'pointer-events:none;"></div>'
            # Diagonal stripe texture
            f'<div style="position:absolute;inset:0;'
            f'background:repeating-linear-gradient('
            f'135deg,transparent,transparent 40px,'
            f'rgba(255,255,255,0.018) 40px,rgba(255,255,255,0.018) 41px);'
            f'pointer-events:none;"></div>'
            # Player last name — poster typographic treatment
            f'<div style="position:relative;z-index:2;width:960px;'
            f'font-family:Oswald,Impact,Arial Black,Arial,sans-serif;'
            f'font-size:{poster_fs}px;font-weight:700;color:#ffffff;'
            f'line-height:1;letter-spacing:-4px;text-align:center;'
            f'text-shadow:0 0 80px {_rgba(theme["accent"], 0.7)},'
            f'0 0 200px {_rgba(theme["accent"], 0.4)},'
            f'0 4px 40px rgba(0,0,0,0.9);">'
            f'{last_name}</div>'
            # Position pill below name
            f'<div style="position:relative;z-index:2;margin-top:48px;'
            f'background:#E63946;color:#fff;'
            f'font-family:Oswald,Impact,Arial Black,Arial,sans-serif;'
            f'font-size:32px;font-weight:700;letter-spacing:4px;'
            f'padding:14px 48px;border-radius:6px;">{pos_short}</div>'
            f'</div>'
        )

    # ── OVR circle — top-left ─────────────────────────────────────────────
    ovr_circle = (
        f'<div style="position:absolute;top:270px;left:60px;width:110px;height:110px;'
        f'border-radius:50%;background:rgba(0,0,0,0.75);border:2.5px solid {GOLD};'
        f'display:flex;flex-direction:column;align-items:center;'
        f'justify-content:center;z-index:20;">'
        f'<div style="font-size:48px;font-weight:700;color:{GOLD};line-height:1">{ovr}</div>'
        f'<div style="font-size:14px;color:rgba(212,168,67,0.8);letter-spacing:2px">OVR</div>'
        f'</div>'
    )

    # ── Country badge — top-right ─────────────────────────────────────────
    flag_url  = get_flag_url(team)
    flag_img  = f'<img src="{flag_url}" style="height:48px;border-radius:6px;">' if flag_url else ""
    country_badge = (
        f'<div style="position:absolute;top:270px;right:60px;background:rgba(0,0,0,0.75);'
        f'border:1.5px solid {GOLD};border-radius:12px;padding:8px 16px;'
        f'z-index:20;display:flex;align-items:center;gap:10px;">'
        f'{flag_img}'
        f'<div style="font-size:18px;font-weight:700;color:{GOLD};letter-spacing:3px">{country_code}</div>'
        f'</div>'
    )

    # ── Gold corner accents ───────────────────────────────────────────────
    gold_corners = (
        f'<div style="position:absolute;top:190px;left:0;width:40px;height:40px;'
        f'border-top:2px solid {GOLD};border-right:2px solid {GOLD};'
        f'border-radius:0 12px 0 0;opacity:0.6;z-index:10;"></div>'
        f'<div style="position:absolute;top:190px;right:0;width:40px;height:40px;'
        f'border-top:2px solid {GOLD};border-left:2px solid {GOLD};'
        f'border-radius:12px 0 0 0;opacity:0.6;z-index:10;"></div>'
    )

    # ── Quote ─────────────────────────────────────────────────────────────
    quote_html = (
        f'<div style="font-size:22px;color:rgba(255,255,255,0.4);'
        f'font-family:Roboto,sans-serif;line-height:1.4;'
        f'padding:0 20px;max-width:400px;">{quote}</div>'
    ) if quote else ""

    # ── Stats panel: bottom 640px ─────────────────────────────────────────
    stats_panel = f"""
    <div style="position:absolute;bottom:0;left:0;right:0;height:640px;
                background:rgba(0,0,0,0.88);border-top:1.5px solid {GOLD};">

      <div style="padding:24px 60px 12px;display:flex;align-items:baseline;
                  justify-content:space-between;
                  border-bottom:0.5px solid rgba(212,168,67,0.3);">
        <div style="font-size:100px;font-weight:700;color:#fff;
                    line-height:1;letter-spacing:-2px">{display_name}</div>
        <div style="background:#E63946;color:#fff;font-size:22px;font-weight:700;
                    padding:8px 24px;border-radius:6px;letter-spacing:2px;
                    white-space:nowrap;align-self:center">{pos_short}</div>
      </div>

      <div style="padding:10px 60px 0;font-family:Roboto,sans-serif;
                  font-size:24px;color:rgba(212,168,67,0.8);letter-spacing:3px;">
        {club.upper()} - WC 2026
      </div>

      <div style="height:1px;background:linear-gradient(90deg,transparent,{GOLD},transparent);
                  margin:16px 60px 20px;"></div>

      <div style="display:grid;grid-template-columns:1fr 1fr 1fr;padding:0 60px;">
        <div style="text-align:center;border-right:0.5px solid rgba(212,168,67,0.2);">
          <div style="font-size:96px;font-weight:700;color:{GOLD};
                      line-height:1;letter-spacing:-2px">{goals}</div>
          <div style="font-size:22px;color:rgba(255,255,255,0.6);
                      letter-spacing:2px;margin-top:8px">GOALS</div>
        </div>
        <div style="text-align:center;border-right:0.5px solid rgba(212,168,67,0.2);">
          <div style="font-size:72px;font-weight:700;color:#E63946;
                      line-height:1;letter-spacing:-2px">{caps}</div>
          <div style="font-size:22px;color:rgba(255,255,255,0.6);
                      letter-spacing:2px;margin-top:8px">CAPS</div>
        </div>
        <div style="text-align:center;">
          <div style="font-size:72px;font-weight:700;color:#E63946;
                      line-height:1;letter-spacing:-2px">{club_goals}</div>
          <div style="font-size:22px;color:rgba(255,255,255,0.6);
                      letter-spacing:2px;margin-top:8px">CLUB GLS</div>
        </div>
      </div>

      <div style="display:flex;align-items:center;justify-content:space-between;
                  padding:16px 60px 0;margin-top:12px;
                  border-top:0.5px solid rgba(212,168,67,0.2);">
        <div>
          <div style="font-size:36px;font-weight:700;color:{GOLD}">{mval}</div>
          <div style="font-size:20px;color:rgba(255,255,255,0.5);
                      letter-spacing:2px;margin-top:4px">MARKET VALUE</div>
        </div>
        {quote_html}
      </div>
    </div>"""

    top_bar = (
        f'<div style="position:absolute;top:0;left:0;right:0;height:4px;z-index:30;'
        f'background:linear-gradient(90deg,#E63946,{GOLD},#E63946);"></div>'
    )

    body = photo_zone + top_bar + ovr_circle + country_badge + gold_corners + stats_panel

    # Player card manages its own complete styling — no _base_css()
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Oswald:wght@400;600;700&family=Roboto:wght@300;400&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:1080px;height:1920px;overflow:hidden;
           font-family:'Oswald',Impact,'Arial Black',Arial,sans-serif;
           -webkit-font-smoothing:antialiased;background:#0D0D14}}
.card{{position:relative;width:1080px;height:1920px;overflow:hidden;background:#0D0D14}}
</style>
</head>
<body><div class="card">{body}</div></body>
</html>"""


# ── Card 4 — GROUP (solid bg, circular flags — Issue #221) ────────────────────

def _group_html(team: str, data: dict, theme: dict, bg_photo: str = "") -> str:
    group_id    = data["group_info"]["group"]
    group_teams = data["group_info"].get("teams", [])
    acc         = _hex(theme["accent"])
    r, g, b     = theme["accent"]

    rows_html = ""
    for t_name in group_teams[:4]:
        is_hl    = t_name.lower() == team.lower()
        flag_url = get_flag_url(t_name, width=200)

        # Explicit width+height attrs + border-radius on <img> directly.
        # A wrapper div with overflow:hidden is intentionally avoided — flex/grid
        # containers collapse it. The img itself carries all circular styling.
        if flag_url:
            flag_cell = (
                f'<img src="{flag_url}" alt="{t_name}"'
                f' width="100" height="100"'
                f' style="width:100px;height:100px;object-fit:cover;'
                f'border-radius:50%;display:block;flex-shrink:0;">'
            )
        else:
            flag_cell = (
                f'<div style="width:100px;height:100px;border-radius:50%;'
                f'background:rgba(255,255,255,0.12);display:block;flex-shrink:0;"></div>'
            )

        if is_hl:
            row_style = (
                f"background:rgba({r},{g},{b},0.25);"
                f"border:2px solid {GOLD};"
                f"box-shadow:0 0 40px rgba({r},{g},{b},0.3);"
            )
            name_color  = "#fff"
            name_weight = "700"
            badge = (
                f'<span style="background:{GOLD};color:#000;font-size:18px;'
                f'font-weight:700;letter-spacing:2px;padding:8px 20px;'
                f'border-radius:999px;white-space:nowrap;">YOUR TEAM</span>'
            )
        else:
            row_style   = "background:rgba(15,15,30,0.85);border:1.5px solid rgba(255,255,255,0.08);"
            name_color  = "#d0d4e8"
            name_weight = "400"
            badge       = ""

        name_size = "52px" if len(t_name) <= 12 else "40px"

        # Grid layout: fixed 110px flag col | flexible name col | auto badge col.
        # display:grid prevents flex from collapsing the flag cell.
        rows_html += (
            f'<div style="display:grid;grid-template-columns:110px 1fr auto;'
            f'align-items:center;gap:16px;'
            f'{row_style}border-radius:20px;padding:20px 28px;min-height:160px;">'
            f'{flag_cell}'
            f'<div style="font-size:{name_size};font-weight:{name_weight};'
            f'color:{name_color};letter-spacing:0;line-height:1.1;">'
            f'{t_name}</div>'
            f'{badge}'
            f'</div>'
        )

    # Decorative left accent bar — font-load-independent replacement for
    # the group letter (which rendered as a thin rectangle before fonts loaded).
    accent_bar = (
        f'<div style="position:absolute;left:60px;top:{_SAFE_TOP}px;'
        f'width:8px;height:200px;border-radius:4px;'
        f'background:{acc};z-index:2;'
        f'box-shadow:0 0 24px {_rgba(theme["accent"],0.55)};"></div>'
    )

    body = f"""
    {accent_bar}

    <!-- Subtitle pinned at safe-zone top, indented past the accent bar -->
    <div style="position:absolute;left:88px;right:60px;top:{_SAFE_TOP + 20}px;z-index:5;">
      <div style="font-size:28px;font-weight:400;letter-spacing:4px;
                  color:rgba(255,255,255,0.85);">
        GROUP {group_id} &mdash; FIFA WORLD CUP 2026
      </div>
    </div>

    <!-- Team rows — first row starts at y=400 -->
    <div style="position:absolute;left:60px;right:60px;top:400px;z-index:5;">
      <div style="display:flex;flex-direction:column;gap:16px;">
        {rows_html}
      </div>
    </div>"""

    # Solid team-colour flat bg — no photo
    gt    = _hex(theme["gradient_top"])
    extra = f".card{{background:linear-gradient(160deg,{gt} 0%,#060810 60%)!important;}}"
    css   = _base_css(theme, extra=extra)
    return _html(css, body)


# ── Card 5 — CTA (high-contrast, gold divider — Issue #221) ──────────────────

def _cta_html(team: str, data: dict, theme: dict, bg_photo: str = "") -> str:
    acc      = _hex(theme["accent"])
    acc_glow = _rgba(theme["accent"], 0.5)
    group_id = data["group_info"]["group"]
    r, g, b  = theme["accent"]

    # ── 1. Content block — true vertical center of full 1920px card ───────
    # top:50% + translateY(-50%) centres on card height, not safe zone.
    content = f"""
    <div style="position:absolute;left:60px;right:60px;
                top:50%;transform:translateY(-50%);
                text-align:center;z-index:5;">

      <!-- CAN / TEAM / WIN IT ALL -->
      <div style="font-size:80px;font-weight:700;color:#fff;line-height:1;">CAN</div>
      <div style="font-size:120px;font-weight:700;color:{acc};line-height:1;
                  text-shadow:0 0 60px rgba({r},{g},{b},0.6);">{team.upper()}</div>
      <div style="font-size:80px;font-weight:700;color:#fff;line-height:1;">WIN IT ALL?</div>

      <!-- ── 3. Gold divider — 840px wide, 3px, glowing ── -->
      <div style="width:840px;max-width:100%;height:3px;margin:48px auto;
                  background:{GOLD};border-radius:2px;
                  box-shadow:0 0 12px {GOLD};"></div>

      <!-- COMMENT — white, large, with accent glow -->
      <div style="font-size:96px;font-weight:700;letter-spacing:-1px;
                  color:#FFFFFF;
                  text-shadow:0 0 40px {acc_glow},2px 2px 0 rgba(0,0,0,0.8);">
        COMMENT
      </div>
      <div style="font-size:52px;font-weight:700;letter-spacing:2px;
                  color:rgba(255,255,255,0.9);margin-top:12px;">
        YOUR PREDICTION
      </div>

      <div style="margin-top:16px;font-family:'Roboto',Arial,sans-serif;
                  font-size:32px;font-weight:300;
                  color:rgba(180,185,200,0.6);">
        Group {group_id} - FIFA World Cup 2026
      </div>

    </div>"""

    # ── 2. Swipe indicator — 5 circles at y=1350, middle filled with accent ──
    dot_outline = (
        f'<div style="width:10px;height:10px;border-radius:50%;'
        f'border:2px solid rgba(255,255,255,0.35);"></div>'
    )
    dot_filled = (
        f'<div style="width:10px;height:10px;border-radius:50%;'
        f'background:{acc};box-shadow:0 0 8px {acc_glow};"></div>'
    )
    swipe_indicator = (
        f'<div style="position:absolute;top:1350px;left:50%;'
        f'transform:translateX(-50%);'
        f'display:flex;align-items:center;gap:16px;z-index:5;">'
        f'{dot_outline}{dot_outline}{dot_filled}{dot_outline}{dot_outline}'
        f'</div>'
    )

    # Gold bottom accent bar
    bottom_bar = (
        f'<div style="position:absolute;bottom:10px;left:0;right:0;height:4px;z-index:20;'
        f'background:linear-gradient(90deg,transparent,{GOLD},transparent);"></div>'
    )

    css = _base_css(theme)
    return _html(css, content + swipe_indicator + bottom_bar)


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
    players:    Number of player cards to render (1-5, default 3)
    """
    data   = get_full_team_data(team)
    theme  = get_country_theme(team)
    slug   = team.lower().replace(" ", "_")
    outdir = output_dir or (OUTPUT_DIR / "cards" / slug)
    outdir.mkdir(parents=True, exist_ok=True)

    key_players = data.get("key_players", [])[:players]

    # Only player cards use photo backgrounds; hook/history/group/cta use solid gradients
    print(f"[html_cards] Fetching player backgrounds for {team}...")
    _PLAYER_QUERY = "football player action stadium crowd"
    player_bgs = [
        _fetch_background(_PLAYER_QUERY, outdir, offset=i)
        for i in range(len(key_players))
    ]

    # Build (html, path) list in pipeline order
    cards: list[tuple[str, Path]] = [
        (_hook_html(team, data, theme),    outdir / "hook.png"),
        (_history_html(team, data, theme), outdir / "history.png"),
        *[
            (
                _player_html(p, team, theme,
                             bg_photo=player_bgs[i] if i < len(player_bgs) else ""),
                outdir / f"player_{i}.png",
            )
            for i, p in enumerate(key_players)
        ],
        (_group_html(team, data, theme),   outdir / "group.png"),
        (_cta_html(team, data, theme),     outdir / "cta.png"),
    ]

    print(f"[html_cards] Rendering {len(cards)} cards for {team}...")
    return asyncio.run(_screenshot_all(cards))
