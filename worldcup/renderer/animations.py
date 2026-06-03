"""
Frame-level animation utilities for World Cup videos.

Every function returns a MoviePy clip (ImageClip or VideoClip).
Callers concatenate clips to build the final timeline.

Memory strategy: animated transitions are short (0.3-0.5 s = 9-15 frames).
Static holds are MoviePy ImageClips (one frame stored, repeated lazily).
"""
from __future__ import annotations

from typing import Optional
import numpy as np
from PIL import Image


# ── helpers ───────────────────────────────────────────────────────────────────

def _to_rgb(img: Image.Image, w: int, h: int) -> np.ndarray:
    img = img.convert("RGB")
    if img.size != (w, h):
        img = img.resize((w, h), Image.LANCZOS)
    return np.asarray(img, dtype=np.uint8)


def _frames_to_clip(frames: list, fps: int):
    """Wrap a list of numpy frames as a MoviePy VideoClip."""
    from moviepy.editor import VideoClip
    n = len(frames)
    _f = frames            # capture reference

    def make_frame(t, _frames=_f, _fps=fps, _n=n):
        return _frames[min(int(t * _fps), _n - 1)]

    return VideoClip(make_frame, duration=n / fps)


# ── public clip builders ───────────────────────────────────────────────────────

def hold(img: Image.Image, fps: int, duration: float):
    """Static ImageClip — most memory-efficient hold."""
    from moviepy.editor import ImageClip
    frame = _to_rgb(img, img.width, img.height)
    return ImageClip(frame, duration=duration)


def slide_in_from_right(img: Image.Image, fps: int, duration: float = 0.4,
                         bg: tuple = (5, 5, 15)):
    """Card slides in from the right edge with ease-out cubic."""
    w, h  = img.size
    src   = _to_rgb(img, w, h)
    bg_np = np.full((h, w, 3), bg, dtype=np.uint8)
    n     = max(1, round(fps * duration))

    frames = []
    for i in range(n):
        t      = (i + 1) / n
        ease   = 1.0 - (1.0 - t) ** 3
        offset = int(w * (1.0 - ease))
        canvas = bg_np.copy()
        if offset < w:
            canvas[:, : w - offset] = src[:, offset:]
        frames.append(canvas)

    return _frames_to_clip(frames, fps)


def fade_up(img: Image.Image, fps: int, duration: float = 0.3,
             bg: tuple = (5, 5, 15), shift_px: int = 50):
    """Card fades in while rising *shift_px* pixels."""
    w, h  = img.size
    src   = _to_rgb(img, w, h).astype(np.float32)
    bg_np = np.full((h, w, 3), bg, dtype=np.float32)
    n     = max(1, round(fps * duration))

    frames = []
    for i in range(n):
        t     = (i + 1) / n
        alpha = t
        dy    = int(shift_px * (1.0 - t))
        canvas = bg_np.copy()
        visible_h = h - dy
        if visible_h > 0:
            canvas[dy:] = bg_np[dy:] * (1 - alpha) + src[:visible_h] * alpha
        frames.append(np.clip(canvas, 0, 255).astype(np.uint8))

    return _frames_to_clip(frames, fps)


def zoom_in(img: Image.Image, fps: int, duration: float = 0.5,
             scale_start: float = 1.06):
    """Subtle Ken-Burns zoom: starts slightly oversized, eases to 1:1."""
    w, h  = img.size
    src   = _to_rgb(img, w, h)
    n     = max(1, round(fps * duration))

    frames = []
    for i in range(n):
        t     = (i + 1) / n
        scale = scale_start + (1.0 - scale_start) * t  # scale_start → 1.0
        nw    = max(1, int(w / scale))
        nh    = max(1, int(h / scale))
        x0    = (w - nw) // 2
        y0    = (h - nh) // 2
        crop  = Image.fromarray(src).crop((x0, y0, x0 + nw, y0 + nh))
        frames.append(_to_rgb(crop.resize((w, h), Image.BILINEAR), w, h))

    return _frames_to_clip(frames, fps)


def crossfade(img_a: Image.Image, img_b: Image.Image,
              fps: int, duration: float = 0.3):
    """Dissolve from img_a to img_b."""
    w, h = img_a.size
    a    = _to_rgb(img_a, w, h).astype(np.float32)
    b    = _to_rgb(img_b, w, h).astype(np.float32)
    n    = max(1, round(fps * duration))

    frames = []
    for i in range(n):
        t = (i + 1) / n
        frames.append(np.clip(a * (1 - t) + b * t, 0, 255).astype(np.uint8))

    return _frames_to_clip(frames, fps)
