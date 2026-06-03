"""
Pillow-based card renderer for World Cup 2026 videos.

Every card type used by the video pipeline is produced here.
Cards are pure PIL Images — callers compose them into video frames.
"""
from __future__ import annotations

import io
from pathlib import Path
from typing import Optional

import numpy as np
import requests
from PIL import Image, ImageDraw, ImageFont

from worldcup.config import FONTS, WC_THEME, WC_THEME_RGB


# ── Font loader ────────────────────────────────────────────────────────────────

def _load_font(variant: str = "regular", size: int = 32) -> ImageFont.FreeTypeFont:
    path = FONTS.get(variant, "")
    if path and Path(path).exists():
        return ImageFont.truetype(path, size)
    return ImageFont.load_default()


# ── Image helpers ──────────────────────────────────────────────────────────────

def _fetch_image(url: str, size: tuple[int, int] = (80, 80)) -> Optional[Image.Image]:
    """Download and resize an image URL; return None on failure."""
    if not url:
        return None
    try:
        resp = requests.get(url, timeout=8)
        resp.raise_for_status()
        img = Image.open(io.BytesIO(resp.content)).convert("RGBA")
        img.thumbnail(size, Image.LANCZOS)
        return img
    except Exception:
        return None


def _rounded_rect_mask(size: tuple[int, int], radius: int) -> Image.Image:
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([(0, 0), (size[0] - 1, size[1] - 1)], radius=radius, fill=255)
    return mask


def _gradient_bg(width: int, height: int,
                 top_color: tuple, bottom_color: tuple) -> Image.Image:
    """Fast vertical gradient using numpy instead of per-pixel Python loop."""
    t = np.linspace(0, 1, height, dtype=np.float32)[:, np.newaxis]  # (H, 1)
    top = np.array(top_color, dtype=np.float32)                       # (3,)
    bot = np.array(bottom_color, dtype=np.float32)                    # (3,)
    row = (top + t * (bot - top)).astype(np.uint8)                    # (H, 3)
    arr = np.broadcast_to(row[:, np.newaxis, :], (height, width, 3))  # (H, W, 3)
    return Image.fromarray(np.ascontiguousarray(arr), "RGB")


def _circle_crop(img: Image.Image, size: int) -> Image.Image:
    """Resize *img* to *size*×*size* and apply a circular mask."""
    img = img.convert("RGBA").resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size - 1, size - 1), fill=255)
    img.putalpha(mask)
    return img


# ── Watermark ─────────────────────────────────────────────────────────────────

def _add_watermark(img: Image.Image) -> Image.Image:
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    font = _load_font("bold", 20)
    text = "WORLD CUP 2026"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text((img.width - tw - 16, img.height - th - 12), text,
              font=font, fill=(255, 255, 255, 26))
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")


# ── Accent bar at top of card ──────────────────────────────────────────────────

def _draw_accent_bar(draw: ImageDraw.ImageDraw, width: int, color: tuple, height: int = 6):
    draw.rectangle([(0, 0), (width, height)], fill=color)


# ── InfoCard ───────────────────────────────────────────────────────────────────

class InfoCard:
    """
    Pillow-based card builder for World Cup 2026 videos.

    Supported row types (added in order, rendered top-to-bottom):
        add_header(title, subtitle, flag_url)
        add_stat_row(label, value)
        add_bar(label, value, max_value, color)
        add_player_row(name, position, club, goals, image_url)
        add_group_row(group_id, teams)
        add_divider()
        add_footer(text)

    Usage::

        card = InfoCard(1080, 500, country="brazil")
        card.add_header("BRAZIL", subtitle="5× World Champions")
        card.add_stat_row("Appearances", "22")
        img = card.render()
        card.save("output/test_card.png")
    """

    PADDING    = 44
    LINE_GAP   = 10
    ACCENT_H   = 6      # top accent bar height

    def __init__(self, width: int, height: int,
                 theme: str = "worldcup",
                 country: Optional[str] = None):
        self.width  = width
        self.height = height
        self._rows: list[dict] = []

        if country:
            from worldcup.renderer.theme import get_country_theme
            ct = get_country_theme(country)
            self._bg_top    = ct["gradient_top"]
            self._bg_bottom = ct["gradient_bottom"]
            self._accent    = ct["accent"]
            self._text      = ct["text"]
            self._label     = ct["label"]
        else:
            self._bg_top    = WC_THEME_RGB["background"]
            self._bg_bottom = WC_THEME_RGB["background2"]
            self._accent    = WC_THEME_RGB["gold"]
            self._text      = (255, 255, 255)
            self._label     = (170, 170, 170)

    # ── Row adders ─────────────────────────────────────────────────────────────

    def add_header(self, title: str, subtitle: Optional[str] = None,
                   flag_url: Optional[str] = None):
        self._rows.append({"type": "header", "title": title,
                            "subtitle": subtitle, "flag_url": flag_url})

    def add_stat_row(self, label: str, value: str):
        self._rows.append({"type": "stat", "label": label, "value": value})

    def add_bar(self, label: str, value: float, max_value: float,
                color: Optional[tuple] = None):
        self._rows.append({"type": "bar", "label": label, "value": value,
                            "max_value": max_value, "color": color})

    def add_player_row(self, name: str, position: str, club: str,
                       goals: int = 0, image_url: Optional[str] = None):
        self._rows.append({"type": "player", "name": name, "position": position,
                            "club": club, "goals": goals, "image_url": image_url})

    def add_hero_header(self, title: str, country: str, subtitle: Optional[str] = None):
        """Header with flag auto-fetched from flagcdn.com for *country*."""
        from worldcup.data.wc2026_data import get_flag_url
        flag_url = get_flag_url(country)
        self._rows.append({"type": "header", "title": title,
                            "subtitle": subtitle, "flag_url": flag_url})

    def add_group_row(self, group_id: str, teams: list[str], highlight: str = ""):
        """Group block. Pass *highlight* (team name) to render that row in accent color."""
        self._rows.append({"type": "group", "group_id": group_id,
                            "teams": teams, "highlight": highlight})

    def add_divider(self):
        self._rows.append({"type": "divider"})

    def add_footer(self, text: str):
        self._rows.append({"type": "footer", "text": text})

    # ── Render ─────────────────────────────────────────────────────────────────

    def render(self) -> Image.Image:
        img = _gradient_bg(self.width, self.height, self._bg_top, self._bg_bottom)

        # Rounded corners
        radius = WC_THEME["card_radius"]
        mask = _rounded_rect_mask((self.width, self.height), radius)
        img.putalpha(mask)
        img = img.convert("RGB")

        draw = ImageDraw.Draw(img)

        # Accent bar at top
        _draw_accent_bar(draw, self.width, self._accent, self.ACCENT_H)

        y = self.PADDING + self.ACCENT_H

        for row in self._rows:
            y = self._draw_row(draw, img, row, y)
            y += self.LINE_GAP

        img = _add_watermark(img)
        return img

    def _draw_row(self, draw: ImageDraw.ImageDraw, img: Image.Image,
                  row: dict, y: int) -> int:
        p = self.PADDING
        w = self.width

        rtype = row["type"]

        # ── header ──────────────────────────────────────────────────────────
        if rtype == "header":
            flag_img = _fetch_image(row.get("flag_url") or "", (72, 54))
            tx = p
            if flag_img:
                paste_y = y + 4
                if flag_img.mode == "RGBA":
                    img.paste(flag_img, (tx, paste_y), flag_img.split()[3])
                else:
                    img.paste(flag_img, (tx, paste_y))
                tx += flag_img.width + 16

            font_title = _load_font("bold", 60)
            draw.text((tx, y), row["title"], font=font_title, fill=self._accent)
            y += 70

            if row.get("subtitle"):
                font_sub = _load_font("regular", 30)
                draw.text((p, y), row["subtitle"], font=font_sub, fill=self._label)
                y += 40

        # ── stat row ─────────────────────────────────────────────────────────
        elif rtype == "stat":
            font_lbl = _load_font("light", 28)
            font_val = _load_font("bold", 34)

            draw.text((p, y + 3), row["label"], font=font_lbl, fill=self._label)

            val_str = str(row["value"])
            bbox = draw.textbbox((0, 0), val_str, font=font_val)
            val_w = bbox[2] - bbox[0]
            draw.text((w - p - val_w, y), val_str, font=font_val, fill=self._text)
            y += 46

        # ── bar ──────────────────────────────────────────────────────────────
        elif rtype == "bar":
            font_lbl = _load_font("regular", 26)
            draw.text((p, y), row["label"], font=font_lbl, fill=self._label)
            y += 32

            bar_w  = w - 2 * p
            bar_h  = 20
            color  = row.get("color") or self._accent
            ratio  = min(1.0, row["value"] / max(float(row["max_value"]), 1))
            fill_w = int(bar_w * ratio)

            draw.rounded_rectangle([(p, y), (p + bar_w, y + bar_h)],
                                    radius=10, fill=(40, 40, 60))
            if fill_w > 0:
                draw.rounded_rectangle([(p, y), (p + fill_w, y + bar_h)],
                                        radius=10, fill=color)

            pct_str  = f"{int(ratio * 100)}%"
            font_pct = _load_font("light", 22)
            bbox = draw.textbbox((0, 0), pct_str, font=font_pct)
            draw.text((w - p - (bbox[2] - bbox[0]), y - 2), pct_str,
                      font=font_pct, fill=self._label)
            y += bar_h + 10

        # ── player row ───────────────────────────────────────────────────────
        elif rtype == "player":
            av_size = 52
            avatar  = _fetch_image(row.get("image_url") or "", (av_size, av_size))
            ax      = p

            if avatar:
                circ = _circle_crop(avatar, av_size)
                img.paste(circ, (ax, y), circ.split()[3])
                ax += av_size + 14

            font_name = _load_font("bold", 30)
            font_info = _load_font("light", 24)

            draw.text((ax, y + 2), row["name"], font=font_name, fill=self._text)

            # position + club
            info_str = f"{row['position']}  ·  {row['club']}"
            draw.text((ax, y + 36), info_str, font=font_info, fill=self._label)

            # goals right-aligned — plain ASCII to avoid cp1252 encoding errors
            goals = row.get("goals", 0)
            if goals:
                gstr  = f"Gls: {goals}"
                bbox  = draw.textbbox((0, 0), gstr, font=font_info)
                gw    = bbox[2] - bbox[0]
                draw.text((w - p - gw, y + 36), gstr, font=font_info,
                          fill=self._accent)

            y += av_size + 12

        # ── group row ────────────────────────────────────────────────────────
        elif rtype == "group":
            font_g      = _load_font("bold", 28)
            font_t      = _load_font("regular", 26)
            font_t_bold = _load_font("bold", 26)
            highlight   = row.get("highlight", "").lower()
            gid_str     = f"GROUP {row['group_id']}"
            draw.text((p, y), gid_str, font=font_g, fill=self._accent)
            y += 36
            for team in row.get("teams", []):
                is_hl  = team.lower() == highlight
                bullet = ">> " if is_hl else " - "   # ASCII-safe indicators
                color  = self._accent if is_hl else self._text
                font   = font_t_bold  if is_hl else font_t
                draw.text((p + 8, y), bullet + team, font=font, fill=color)
                y += 34
            y += 4

        # ── divider ──────────────────────────────────────────────────────────
        elif rtype == "divider":
            draw.line([(p, y + 8), (w - p, y + 8)],
                      fill=(self._accent[0], self._accent[1], self._accent[2], 80)
                      if len(self._accent) > 3 else (*self._accent[:3], 80),
                      width=1)
            y += 22

        # ── footer ───────────────────────────────────────────────────────────
        elif rtype == "footer":
            font_f = _load_font("light", 22)
            bbox   = draw.textbbox((0, 0), row["text"], font=font_f)
            fw     = bbox[2] - bbox[0]
            draw.text(((w - fw) // 2, y), row["text"], font=font_f, fill=self._label)
            y += 34

        return y

    # ── Save ───────────────────────────────────────────────────────────────────

    def save(self, path: str | Path):
        self.render().save(str(path))


# ══════════════════════════════════════════════════════════════════════════════
# Full-frame (1080×1920) segment builders for issue #120 video quality overhaul
# ══════════════════════════════════════════════════════════════════════════════

def _text_shadow(draw: ImageDraw.ImageDraw, pos: tuple, text: str,
                 font, fill: tuple, shadow: tuple = (0, 0, 0), offset: int = 3):
    """Draw text with a drop shadow."""
    draw.text((pos[0] + offset, pos[1] + offset), text, font=font, fill=shadow)
    draw.text(pos, text, font=font, fill=fill)


def _centered_x(draw: ImageDraw.ImageDraw, text: str, font, canvas_w: int) -> int:
    bb = draw.textbbox((0, 0), text, font=font)
    return (canvas_w - (bb[2] - bb[0])) // 2


def _pill(draw: ImageDraw.ImageDraw, text: str, font,
          cx: int, cy: int, fill: tuple, text_fill: tuple = (255, 255, 255),
          pad_x: int = 24, pad_y: int = 10):
    """Draw a rounded-pill badge centred at (cx, cy)."""
    bb  = draw.textbbox((0, 0), text, font=font)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    x0 = cx - tw // 2 - pad_x
    y0 = cy - th // 2 - pad_y
    x1 = cx + tw // 2 + pad_x
    y1 = cy + th // 2 + pad_y
    draw.rounded_rectangle([x0, y0, x1, y1], radius=(y1 - y0) // 2, fill=fill)
    draw.text((cx - tw // 2, cy - th // 2), text, font=font, fill=text_fill)


# ── Segment 1 — HOOK ──────────────────────────────────────────────────────────

def build_hook_segment(team: str, group_id: str, flag_url: str,
                        res: tuple = (1080, 1920)) -> Image.Image:
    """
    Full-bleed blurred flag background, team name centred, group badge.
    """
    from PIL import ImageFilter
    from worldcup.renderer.theme import get_country_theme

    W, H = res
    theme = get_country_theme(team)
    accent = theme["accent"]

    # Background: attempt flag blur, fall back to gradient
    bg = _gradient_bg(W, H, theme["gradient_top"], theme["gradient_bottom"])

    flag_full = _fetch_image(flag_url, (W, H))
    if flag_full:
        flag_full = flag_full.convert("RGB").resize((W, H), Image.LANCZOS)
        flag_blurred = flag_full.filter(ImageFilter.GaussianBlur(radius=28))
        # Dark overlay: blend flag 35% + dark gradient 65%
        bg_np  = np.array(bg, dtype=np.float32)
        flg_np = np.array(flag_blurred, dtype=np.float32)
        dark   = np.zeros_like(bg_np)
        mixed  = dark * 0.50 + flg_np * 0.35 + bg_np * 0.15
        bg = Image.fromarray(np.clip(mixed, 0, 255).astype(np.uint8))

    img  = bg.convert("RGBA")
    draw = ImageDraw.Draw(img)

    # Group badge — top-right pill
    font_badge = _load_font("bold", 32)
    badge_text = f"GROUP {group_id}"
    _pill(draw, badge_text, font_badge, W - 160, 90, accent, (0, 0, 0))

    # Team name centred at ~45% height
    font_team = _load_font("bold", 120)
    name_upper = team.upper()
    tx = _centered_x(draw, name_upper, font_team, W)
    ty = int(H * 0.42)
    _text_shadow(draw, (tx, ty), name_upper, font_team, (255, 255, 255), offset=4)

    # Subtitle
    font_sub = _load_font("bold", 40)
    sub = "FIFA WORLD CUP 2026"
    sx = _centered_x(draw, sub, font_sub, W)
    draw.text((sx, ty + 140), sub, font=font_sub, fill=accent)

    # Bottom watermark
    font_wm = _load_font("light", 22)
    wm = "WORLD CUP 2026"
    bb = draw.textbbox((0, 0), wm, font=font_wm)
    draw.text((W - (bb[2] - bb[0]) - 20, H - (bb[3] - bb[1]) - 20),
              wm, font=font_wm, fill=(255, 255, 255, 26))

    return img.convert("RGB")


# ── Segment 2 — HISTORY / THE RECORD ─────────────────────────────────────────

# Abbreviation map for long best-finish strings (Bug 2)
_BEST_FINISH_ABBREV = {
    "Champions":     "WINNER",
    "Runner-up":     "FINALIST",
    "3rd Place":     "3rd",
    "4th Place":     "4th",
    "Semi-final":    "SEMI",
    "Quarter-final": "QTR-F",
    "Round of 16":   "R16",
    "Group Stage":   "GRP",
    "First appear":  "DEBUT",
}

def _fit_cell_value(val: str, max_normal: int = 8) -> tuple[str, int]:
    """
    Return (display_text, font_size) for a history grid cell value.
    Abbreviates long strings and reduces font size if still long.
    """
    if len(val) <= max_normal:
        return val, 90
    for key, short in _BEST_FINISH_ABBREV.items():
        if key in val:
            return short, 80
    # Still long — use smaller font and truncate
    font_size = max(38, 90 - (len(val) - max_normal) * 5)
    return val[:14], font_size


def build_history_segment(team: str, titles: int, appearances: int,
                           best_finish: str, last_title: int,
                           res: tuple = (1080, 1920)) -> Image.Image:
    """
    2x2 stat grid + animated win-rate bar (rendered at full fill for static version).
    """
    from worldcup.renderer.theme import get_country_theme

    W, H = res
    theme = get_country_theme(team)
    accent  = theme["accent"]
    bg_top  = theme["gradient_top"]
    bg_bot  = theme["gradient_bottom"]

    img  = _gradient_bg(W, H, bg_top, bg_bot)
    draw = ImageDraw.Draw(img)

    # Title band
    band_h = 160
    draw.rectangle([(0, 0), (W, band_h)], fill=accent)
    font_band = _load_font("bold", 64)
    label = "THE RECORD"
    lx = _centered_x(draw, label, font_band, W)
    draw.text((lx, 40), label, font=font_band, fill=(0, 0, 0))

    # 2x2 stat grid
    pad    = 60
    cell_w = (W - pad * 3) // 2
    cell_h = 280
    grid_y = band_h + 80
    cells  = [
        ("WORLD CUP TITLES", str(titles),      str(last_title) if last_title else "N/A"),
        ("APPEARANCES",       str(appearances), "WC Finals"),
        ("BEST FINISH",       best_finish,      ""),
        ("TOTAL FINALS",      str(titles),      "Trophies Won"),
    ]

    for idx, (label_text, big_val, small_val) in enumerate(cells):
        col  = idx % 2
        row  = idx // 2
        cx   = pad + col * (cell_w + pad)
        cy   = grid_y + row * (cell_h + 40)

        # Cell background
        draw.rounded_rectangle([(cx, cy), (cx + cell_w, cy + cell_h)],
                                radius=16, fill=(255, 255, 255, 18))
        draw.rounded_rectangle([(cx, cy), (cx + cell_w, cy + cell_h)],
                                radius=16, outline=accent, width=2)

        # Big value — abbreviate and size-fit to prevent overflow (Bug 2)
        display_val, big_sz = _fit_cell_value(big_val)
        font_big = _load_font("bold", big_sz)
        bb  = draw.textbbox((0, 0), display_val, font=font_big)
        bvx = cx + (cell_w - (bb[2] - bb[0])) // 2
        draw.text((bvx, cy + 30), display_val, font=font_big, fill=accent)

        # Label
        font_lbl = _load_font("regular", 26)
        bb = draw.textbbox((0, 0), label_text, font=font_lbl)
        draw.text((cx + (cell_w - (bb[2] - bb[0])) // 2, cy + 145),
                  label_text, font=font_lbl, fill=(200, 200, 200))

        # Small sub-label
        if small_val:
            font_sm = _load_font("light", 22)
            bb = draw.textbbox((0, 0), small_val, font=font_sm)
            draw.text((cx + (cell_w - (bb[2] - bb[0])) // 2, cy + 185),
                      small_val, font=font_sm, fill=(150, 150, 170))

    # Win-rate bar (appearances / max 23)
    bar_y   = grid_y + 2 * (cell_h + 40) + 60
    bar_h_px = 28
    bar_x   = pad
    bar_w   = W - 2 * pad
    ratio   = min(1.0, appearances / 23)
    fill_w  = int(bar_w * ratio)

    font_bar_lbl = _load_font("regular", 28)
    draw.text((bar_x, bar_y - 38), "WC PARTICIPATION RATE", font=font_bar_lbl,
              fill=(180, 180, 180))
    draw.rounded_rectangle([(bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h_px)],
                            radius=14, fill=(40, 40, 60))
    if fill_w > 0:
        draw.rounded_rectangle([(bar_x, bar_y), (bar_x + fill_w, bar_y + bar_h_px)],
                                radius=14, fill=accent)
    pct_str = f"{int(ratio * 100)}%"
    font_pct = _load_font("bold", 28)
    bb = draw.textbbox((0, 0), pct_str, font=font_pct)
    draw.text((W - pad - (bb[2] - bb[0]), bar_y - 38), pct_str,
              font=font_pct, fill=accent)

    return img


# ── Segment 3 — KEY PLAYER ────────────────────────────────────────────────────

def build_player_segment(player: dict, photo: Image.Image, team: str,
                          res: tuple = (1080, 1920)) -> Image.Image:
    """
    'PLAYERS TO WATCH' header band + photo (top region) + name + position
    badge + club + 4-stat row (goals, caps, club goals, market value) + hype quote.
    """
    from worldcup.renderer.theme import get_country_theme

    W, H = res
    theme  = get_country_theme(team)
    accent = theme["accent"]

    img  = _gradient_bg(W, H, theme["gradient_top"], theme["gradient_bottom"])
    draw = ImageDraw.Draw(img)

    # ── "PLAYERS TO WATCH" header band ────────────────────────────────────────
    band_h = 120
    draw.rectangle([(0, 0), (W, band_h)], fill=accent)
    font_band = _load_font("bold", 52)
    band_lbl  = "PLAYERS TO WATCH"
    draw.text((_centered_x(draw, band_lbl, font_band, W), 28),
              band_lbl, font=font_band, fill=(0, 0, 0))

    # ── Photo — centred below band ─────────────────────────────────────────────
    photo_size = 280
    px = (W - photo_size) // 2
    py = band_h + 60

    photo_rgba = photo.convert("RGBA").resize((photo_size, photo_size), Image.LANCZOS)
    if photo_rgba.mode == "RGBA":
        img.paste(photo_rgba.convert("RGB"), (px, py), photo_rgba.split()[3])
    else:
        img.paste(photo_rgba, (px, py))

    # Re-draw after paste
    draw = ImageDraw.Draw(img)

    name  = player.get("name", "Player")
    pos   = player.get("position", "")
    club  = player.get("club", "")
    goals = player.get("country_goals") or player.get("goals", 0)
    caps  = player.get("caps", 0)
    club_goals = player.get("club_goals", 0)
    mval  = player.get("market_value", "")
    quote = player.get("hype_quote", "")

    # ── Name ──────────────────────────────────────────────────────────────────
    font_name = _load_font("bold", 68)
    ny = py + photo_size + 40
    _text_shadow(draw, (_centered_x(draw, name, font_name, W), ny),
                 name, font_name, (255, 255, 255))

    # ── Position badge ────────────────────────────────────────────────────────
    font_pos = _load_font("bold", 32)
    _pill(draw, pos, font_pos, W // 2, ny + 96, accent, (0, 0, 0))

    # ── Club ──────────────────────────────────────────────────────────────────
    font_club = _load_font("regular", 36)
    draw.text((_centered_x(draw, club, font_club, W), ny + 140),
              club, font=font_club, fill=(190, 190, 190))

    # ── 4-stat row ────────────────────────────────────────────────────────────
    stat_y  = ny + 210
    stat_items = [
        (str(goals), "INTL GOALS"),
        (str(caps),  "CAPS"),
        (str(club_goals), "CLUB GLS"),
        (mval or "N/A", "VALUE"),
    ]
    col_w = W // 4
    font_sv  = _load_font("bold", 44)
    font_sl  = _load_font("light", 22)
    for si, (sv, sl) in enumerate(stat_items):
        cx = si * col_w + col_w // 2
        draw.text((_centered_x(draw, sv, font_sv, col_w) + si * col_w, stat_y),
                  sv, font=font_sv, fill=accent)
        draw.text((_centered_x(draw, sl, font_sl, col_w) + si * col_w, stat_y + 52),
                  sl, font=font_sl, fill=(160, 160, 180))

    # ── Hype quote ────────────────────────────────────────────────────────────
    if quote:
        font_q = _load_font("light", 34)
        quote_display = f'"{quote}"'
        draw.text((_centered_x(draw, quote_display, font_q, W), stat_y + 130),
                  quote_display, font=font_q, fill=(200, 200, 200))

    # ── Bottom accent bar ──────────────────────────────────────────────────────
    draw.rectangle([(0, H - 12), (W, H)], fill=accent)

    return img


# ── Segment 4 — GROUP STAGE ───────────────────────────────────────────────────

def build_group_segment(team: str, group_id: str, group_teams: list[str],
                         res: tuple = (1080, 1920)) -> Image.Image:
    """
    GROUP C centred in large text; 4 team rows with flags below.
    """
    from worldcup.renderer.theme import get_country_theme
    from worldcup.data.wc2026_data import get_flag_url

    W, H = res
    theme  = get_country_theme(team)
    accent = theme["accent"]

    img  = _gradient_bg(W, H, (5, 5, 15), (15, 10, 35))
    draw = ImageDraw.Draw(img)

    # Accent top bar
    draw.rectangle([(0, 0), (W, 10)], fill=accent)

    # GROUP X — large centred header
    font_grp = _load_font("bold", 150)
    gtext    = f"GROUP {group_id}"
    gx       = _centered_x(draw, gtext, font_grp, W)
    draw.text((gx, 80), gtext, font=font_grp, fill=accent)

    font_sub = _load_font("regular", 36)
    sub = "FIFA WORLD CUP 2026"
    sx = _centered_x(draw, sub, font_sub, W)
    draw.text((sx, 280), sub, font=font_sub, fill=(180, 180, 180))

    # Team rows
    row_h    = 160
    row_start = 380
    pad       = 60
    font_team_hl = _load_font("bold", 46)
    font_team_nm = _load_font("regular", 40)

    for i, t_name in enumerate(group_teams[:4]):
        ry      = row_start + i * (row_h + 20)
        is_hl   = t_name.lower() == team.lower()
        row_clr = (255, 255, 255, 15) if is_hl else (255, 255, 255, 8)
        # row bg
        draw.rounded_rectangle([(pad, ry), (W - pad, ry + row_h)],
                                radius=12,
                                fill=(60, 55, 80) if is_hl else (30, 30, 50))
        if is_hl:
            draw.rounded_rectangle([(pad, ry), (W - pad, ry + row_h)],
                                    radius=12, outline=accent, width=2)

        # Flag
        flag_url = get_flag_url(t_name)
        flag_img = _fetch_image(flag_url, (90, 60))
        if flag_img:
            fy = ry + (row_h - 60) // 2
            if flag_img.mode == "RGBA":
                img.paste(flag_img.convert("RGB"), (pad + 20, fy),
                          flag_img.split()[3])
            else:
                img.paste(flag_img, (pad + 20, fy))

        # Team name — truncate long names and adjust font size (Bug 3)
        if len(t_name) > 14:
            display_t = t_name[:13] + "."
        else:
            display_t = t_name
        nm_size = 36 if len(t_name) <= 10 else 28
        fn    = _load_font("bold" if is_hl else "regular", nm_size)
        clr   = accent if is_hl else (220, 220, 220)
        ty_txt = ry + (row_h - nm_size) // 2
        draw.text((pad + 130, ty_txt), display_t, font=fn, fill=clr)

        # Featured badge
        if is_hl:
            font_feat = _load_font("bold", 26)
            _pill(draw, "YOUR TEAM", font_feat, W - pad - 90, ry + row_h // 2,
                  accent, (0, 0, 0))

    # Bottom bar
    draw.rectangle([(0, H - 10), (W, H)], fill=accent)
    return img


# ── Segment 5 — CTA ───────────────────────────────────────────────────────────

def build_cta_segment(team: str, group_id: str,
                       res: tuple = (1080, 1920)) -> Image.Image:
    """
    Prediction prompt + subscribe CTA.
    """
    from worldcup.renderer.theme import get_country_theme

    W, H = res
    theme  = get_country_theme(team)
    accent = theme["accent"]

    img  = _gradient_bg(W, H, (5, 5, 15), (20, 10, 40))
    draw = ImageDraw.Draw(img)

    # Top accent bar
    draw.rectangle([(0, 0), (W, 12)], fill=accent)

    # Prediction question
    font_q1 = _load_font("bold", 64)
    font_q2 = _load_font("bold", 72)
    font_cta = _load_font("bold", 80)
    font_sub = _load_font("regular", 36)

    q1 = "CAN"
    q2 = team.upper()
    q3 = "WIN THE WORLD CUP 2026?"

    y = int(H * 0.22)
    _text_shadow(draw, (_centered_x(draw, q1, font_q1, W), y),
                 q1, font_q1, (255, 255, 255))
    y += 90
    _text_shadow(draw, (_centered_x(draw, q2, font_q2, W), y),
                 q2, font_q2, accent)
    y += 100
    _text_shadow(draw, (_centered_x(draw, q3, font_q1, W), y),
                 q3, font_q1, (255, 255, 255))

    # Comment prompt
    y += 160
    cmt = "COMMENT BELOW"
    _text_shadow(draw, (_centered_x(draw, cmt, font_cta, W), y),
                 cmt, font_cta, accent)

    # Divider
    y += 120
    draw.line([(80, y), (W - 80, y)], fill=(*accent, 100), width=2)

    # Subscribe bar
    y += 50
    sub1 = "LIKE + FOLLOW for daily WC 2026 content"
    sub2 = "FIFA World Cup 2026 | USA - Canada - Mexico"
    draw.text((_centered_x(draw, sub1, font_sub, W), y),
              sub1, font=font_sub, fill=(200, 200, 200))
    y += 50
    draw.text((_centered_x(draw, sub2, font_sub, W), y),
              sub2, font=font_sub, fill=(140, 140, 160))

    # Bottom accent
    draw.rectangle([(0, H - 12), (W, H)], fill=accent)
    return img


# ── Module self-test ───────────────────────────────────────────────────────────
# Run:  python -m worldcup.renderer.card
# Produces 3 PNG files in worldcup/output/

if __name__ == "__main__":
    from worldcup.config import OUTPUT_DIR
    from worldcup.data.wc2026_data import get_full_team_data

    # ── Card 1: Team Intro — Brazil (flag via add_hero_header) ────────────────
    data = get_full_team_data("Brazil")

    c1 = InfoCard(1080, 480, country="brazil")
    c1.add_hero_header("BRAZIL", country="brazil", subtitle="5x World Champions · WC 2026")
    c1.add_divider()
    c1.add_stat_row("World Cup Titles",   str(data["titles"]))
    c1.add_stat_row("Appearances",        str(data["appearances"]))   # 23
    c1.add_stat_row("Best Finish",        data["best_finish"])
    c1.add_stat_row("WC 2026 Group",      data["group_info"]["group"])  # C
    c1.add_divider()
    c1.add_footer("Subscribe - Like - Share")
    out1 = OUTPUT_DIR / "test_team_intro.png"
    c1.save(out1)
    print(f"[test] Saved {out1}")

    # ── Card 2: Key Players — England (no Foden, goals as ASCII) ─────────────
    eng_data = get_full_team_data("England")
    players  = eng_data["key_players"]

    c2 = InfoCard(1080, 520, country="england")
    c2.add_hero_header("KEY PLAYERS", country="england",
                       subtitle="England · WC 2026 · Group L")
    c2.add_divider()
    for p in players[:4]:
        c2.add_player_row(
            name=p["name"], position=p["position"],
            club=p["club"],  goals=p.get("country_goals", 0),
        )
    c2.add_divider()
    c2.add_footer("FIFA World Cup 2026")
    out2 = OUTPUT_DIR / "test_key_players.png"
    c2.save(out2)
    print(f"[test] Saved {out2}")

    # ── Card 3: Group Stage — Germany Group E (highlight + all 4 teams) ───────
    ger_data = get_full_team_data("Germany")
    group    = ger_data["group_info"]   # group = "E"

    c3 = InfoCard(1080, 560, country="germany")
    c3.add_hero_header("GROUP STAGE", country="germany",
                       subtitle="Germany · FIFA World Cup 2026")
    c3.add_divider()
    c3.add_stat_row("Titles",      str(ger_data["titles"]))
    c3.add_stat_row("Appearances", str(ger_data["appearances"]))
    c3.add_stat_row("Best Finish", ger_data["best_finish"])
    c3.add_divider()
    c3.add_group_row(group["group"], group.get("teams", []), highlight="Germany")
    c3.add_footer("USA - Canada - Mexico 2026")
    out3 = OUTPUT_DIR / "test_group_stage.png"
    c3.save(out3)
    print(f"[test] Saved {out3}")

    print("\nAll 3 test cards created in", OUTPUT_DIR)
