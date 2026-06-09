"""
Footage fetcher for World Cup 2026 video pipeline (Issue #123, step 16B).

Public API
----------
fetch_footage(team, segment, duration) -> Path

Searches Pexels (primary) then Pixabay (fallback) for a portrait MP4 clip,
downloads it to a temp file, trims/resizes to 1080×1920 at *duration* seconds
via ffmpeg, and caches the result to worldcup/output/footage/{team}/{segment}.mp4.

Returns a silent black fallback clip if both APIs fail — never raises.

Search queries per segment type:
  hook    → "{team} football fans celebration"
  history → "world cup trophy celebration stadium"
  player  → "football player dribbling action"
  group   → "football stadium crowd night"
  cta     → "football crowd celebration goal"
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from dotenv import load_dotenv

from worldcup.config import OUTPUT_DIR

# ── Setup ──────────────────────────────────────────────────────────────────────

load_dotenv(Path(__file__).resolve().parent.parent.parent / "backend" / ".env")

FOOTAGE_DIR = OUTPUT_DIR / "footage"
FFMPEG      = shutil.which("ffmpeg") or shutil.which("ffmpeg.exe") or "ffmpeg"

_QUERIES: dict[str, str] = {
    "hook":     "{team} football fans celebration",
    "history":  "world cup trophy celebration stadium",
    "player_0": "football forward attacking sprint",
    "player_1": "football midfielder passing technique",
    "player_2": "football winger dribbling skill",
    "player":   "football player dribbling action",   # fallback for unknown index
    "group":    "football stadium crowd night",
    "cta":      "football crowd celebration goal",
}


# ── ffmpeg helpers ─────────────────────────────────────────────────────────────

def _run(args: list[str], label: str = "") -> bool:
    try:
        r = subprocess.run(
            args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            timeout=180,
        )
        if r.returncode != 0 and label:
            tail = r.stderr.decode(errors="replace")[-400:]
            print(f"[footage] ffmpeg {label} failed: {tail}")
        return r.returncode == 0
    except Exception as exc:
        print(f"[footage] ffmpeg {label} error: {exc}")
        return False


def _make_fallback(dest: Path, duration: float) -> Path:
    """Silent black 1080×1920 h264/aac clip — always works."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    _run([
        FFMPEG, "-y",
        "-f", "lavfi", "-i",
        f"color=black:size=1080x1920:rate=30:duration={duration:.3f}",
        "-f", "lavfi", "-i",
        "anullsrc=channel_layout=stereo:sample_rate=44100",
        "-t", f"{duration:.3f}",
        "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "64k", "-shortest",
        str(dest),
    ], label="fallback")
    if not dest.exists():
        dest.touch()   # absolute last resort so callers never crash
    return dest


def _trim_resize(src: Path, dest: Path, duration: float) -> bool:
    """
    Resize to 1080×1920 (scale-to-fill + crop, no letterboxing), trim to
    *duration* seconds, add a silent stereo audio track for mux compatibility.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    return _run([
        FFMPEG, "-y",
        "-i", str(src),
        # Silent audio source — overridden if source has audio via -map below
        "-f", "lavfi", "-i",
        "anullsrc=channel_layout=stereo:sample_rate=44100",
        # Video: scale up to fill 1080×1920 then centre-crop (no black bars)
        "-vf", (
            "scale=1080:1920:force_original_aspect_ratio=increase,"
            "crop=1080:1920,"
            "setsar=1"
        ),
        "-map", "0:v:0",          # video from source
        "-map", "0:a:0?",         # source audio if present (? = optional)
        "-map", "1:a:0",          # lavfi silent audio (used when source has none)
        "-t", f"{duration:.3f}",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-ac", "2",
        "-shortest",
        str(dest),
    ], label="trim_resize")


# ── Download helper ────────────────────────────────────────────────────────────

def _download(url: str, dest: Path) -> bool:
    try:
        import httpx
        dest.parent.mkdir(parents=True, exist_ok=True)
        with httpx.stream("GET", url, timeout=60.0, follow_redirects=True) as r:
            r.raise_for_status()
            with dest.open("wb") as f:
                for chunk in r.iter_bytes(chunk_size=65_536):
                    f.write(chunk)
        return dest.exists() and dest.stat().st_size > 10_000
    except Exception as exc:
        print(f"[footage] Download error: {exc}")
        return False


# ── API search functions ───────────────────────────────────────────────────────

def _best_pexels_file(video_files: list[dict]) -> str:
    """
    Return the URL of the highest-resolution portrait .mp4 in a Pexels
    video_files list. Falls back to the largest file of any orientation
    if no portrait file exists.
    """
    mp4s = [f for f in video_files if "mp4" in f.get("file_type", "")]
    if not mp4s:
        return ""

    portrait = [
        f for f in mp4s
        if f.get("height", 0) >= f.get("width", 1)
    ]
    pool = portrait if portrait else mp4s
    best = max(pool, key=lambda f: f.get("width", 0) * f.get("height", 0))
    return best.get("link", "")


def _search_pexels(query: str) -> str:
    """Return the best portrait video URL from Pexels, or ""."""
    api_key = os.getenv("PEXELS_API_KEY", "").strip()
    if not api_key:
        return ""
    try:
        import httpx
        r = httpx.get(
            "https://api.pexels.com/videos/search",
            headers={"Authorization": api_key},
            params={
                "query":       query,
                "orientation": "portrait",
                "size":        "medium",
                "per_page":    5,
            },
            timeout=20.0,
        )
        r.raise_for_status()
        for video in r.json().get("videos", []):
            url = _best_pexels_file(video.get("video_files", []))
            if url:
                return url
    except Exception as exc:
        print(f"[footage] Pexels error: {exc}")
    return ""


def _search_pixabay(query: str) -> str:
    """Return the best video URL from Pixabay, or ""."""
    api_key = os.getenv("PIXABAY_API_KEY", "").strip()
    if not api_key:
        return ""
    try:
        import httpx
        r = httpx.get(
            "https://pixabay.com/api/videos/",
            params={
                "key":         api_key,
                "q":           query,
                "orientation": "vertical",
                "per_page":    5,
            },
            timeout=20.0,
        )
        r.raise_for_status()
        for hit in r.json().get("hits", []):
            videos = hit.get("videos", {})
            for quality in ("large", "medium", "small", "tiny"):
                url = videos.get(quality, {}).get("url", "")
                if url:
                    return url
    except Exception as exc:
        print(f"[footage] Pixabay error: {exc}")
    return ""


# ── Public API ─────────────────────────────────────────────────────────────────

def fetch_footage(team: str, segment: str, duration: float) -> Path:
    """
    Fetch, process, and cache a 1080×1920 portrait MP4 for one video segment.

    Parameters
    ----------
    team:     Team name matching wc2026_data.py key (e.g. "Brazil").
    segment:  Segment key: "hook" | "history" | "player" | "group" | "cta".
    duration: Target clip length in seconds.

    Returns
    -------
    Path to worldcup/output/footage/{team}/{segment}.mp4.
    Always returns a valid Path — uses a silent black fallback on any failure.
    """
    slug    = team.lower().replace(" ", "_")
    out_dir = FOOTAGE_DIR / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    dest    = out_dir / f"{segment}.mp4"

    if dest.exists() and dest.stat().st_size > 10_000:
        print(f"[footage] Cache hit: {slug}/{segment}.mp4")
        return dest

    raw_query = _QUERIES.get(segment, "{team} football")
    query     = raw_query.replace("{team}", team.title())
    print(f"[footage] {team}/{segment} — searching '{query}' ({duration:.1f}s)")

    url = _search_pexels(query) or _search_pixabay(query)

    if not url:
        print(f"[footage] No results for '{query}' — using fallback")
        return _make_fallback(dest, duration)

    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        print(f"[footage] Downloading {url[:72]}...")
        if not _download(url, tmp_path):
            print(f"[footage] Download failed — using fallback")
            return _make_fallback(dest, duration)

        print(f"[footage] Trimming/resizing to 1080x1920 @ {duration:.1f}s...")
        if not _trim_resize(tmp_path, dest, duration):
            print(f"[footage] Resize failed — using fallback")
            return _make_fallback(dest, duration)
    finally:
        tmp_path.unlink(missing_ok=True)

    size_kb = dest.stat().st_size // 1024
    print(f"[footage] Saved {slug}/{segment}.mp4 ({size_kb} KB)")
    return dest
