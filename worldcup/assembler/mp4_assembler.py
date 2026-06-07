"""
Issue #124 — FFmpeg MP4 Assembler

assemble_mp4(team, footage_paths, card_pngs, narration_path=None) -> Path

Chains footage clips with PNG card overlays at 70% opacity, concatenates all
segments, optionally mixes narration at -3 dB, and writes:
  worldcup/output/final/{team}_wc2026_{timestamp}.mp4

Specs: 1080x1920 @ 30fps, H.264 + AAC, target < 50 MB for ~37s content.
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Optional

from worldcup.config import OUTPUT_DIR, FPS

FINAL_DIR = OUTPUT_DIR / "final"
FFMPEG = shutil.which("ffmpeg") or shutil.which("ffmpeg.exe") or "ffmpeg"


def _run(args: list[str], label: str = "") -> bool:
    try:
        r = subprocess.run(
            args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            timeout=300,
        )
        if r.returncode != 0:
            tail = r.stderr.decode(errors="replace")[-600:]
            print(f"[assembler] ffmpeg {label} failed:\n{tail}")
        return r.returncode == 0
    except Exception as exc:
        print(f"[assembler] {label} error: {exc}")
        return False


def _overlay_segment(footage: Path, card: Path, dest: Path) -> bool:
    """
    Overlay *card* PNG at 70% opacity, centered on *footage*.
    Output duration = footage duration (-shortest stops at footage EOF).
    Always produces 1 video + 1 stereo AAC audio stream.
    """
    filter_complex = (
        # Scale card to fit 1080x1920, pad transparent, apply 70% opacity
        "[1:v]scale=1080:1920:force_original_aspect_ratio=decrease,"
        "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black@0,"
        "format=rgba,colorchannelmixer=aa=0.7[card];"
        # Blend card over footage video
        "[0:v][card]overlay=0:0:format=auto[vout]"
    )
    return _run([
        FFMPEG, "-y",
        "-i", str(footage),
        "-loop", "1", "-i", str(card),  # loop still image to match footage duration
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        "-map", "0:a:0",               # audio from footage (null or real)
        "-shortest",                    # stop when footage stream ends
        "-c:v", "libx264", "-preset", "fast", "-crf", "22", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-ac", "2", "-ar", "44100",
        "-r", str(FPS),
        str(dest),
    ], label=f"overlay:{dest.name}")


def _concat_segments(segment_paths: list[Path], dest: Path) -> bool:
    """Join all segments via ffmpeg concat demuxer with re-encode for compatibility."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as f:
        list_path = Path(f.name)
        for p in segment_paths:
            # Use forward slashes — ffmpeg concat demuxer requires them on Windows too
            f.write(f"file '{p.as_posix()}'\n")

    ok = _run([
        FFMPEG, "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(list_path),
        "-c:v", "libx264", "-preset", "fast", "-crf", "22", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-ac", "2", "-ar", "44100",
        str(dest),
    ], label="concat")
    list_path.unlink(missing_ok=True)
    return ok


def _mix_narration(video: Path, narration: Path, dest: Path) -> bool:
    """Mix narration at -3 dB over video; soften existing footage audio to -6 dB."""
    return _run([
        FFMPEG, "-y",
        "-i", str(video),
        "-i", str(narration),
        "-filter_complex",
        (
            "[0:a]volume=-6dB[va];"
            "[1:a]volume=-3dB[na];"
            "[va][na]amix=inputs=2:duration=first[aout]"
        ),
        "-map", "0:v",
        "-map", "[aout]",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "128k", "-ac", "2", "-ar", "44100",
        str(dest),
    ], label="mix_narration")


def assemble_mp4(
    team: str,
    footage_paths: list[Path],
    card_pngs: list[Path],
    narration_path: Optional[Path] = None,
) -> Path:
    """
    Assemble a 1080x1920 World Cup Short MP4.

    Parameters
    ----------
    team:           Team name, used in the output filename.
    footage_paths:  One Path per segment, already trimmed to segment duration
                    by fetch_footage().
    card_pngs:      One PNG per segment, overlaid at 70% opacity centered on
                    the footage. Must have the same length as footage_paths.
    narration_path: Optional WAV/MP3 voiceover mixed at -3 dB. When absent
                    (or file missing), the video is silent — safe for dev mode.

    Returns
    -------
    Path to worldcup/output/final/{team}_wc2026_{timestamp}.mp4

    Raises
    ------
    ValueError      if footage_paths and card_pngs differ in length.
    RuntimeError    if the concatenation step fails entirely.
    """
    if len(footage_paths) != len(card_pngs):
        raise ValueError(
            f"footage_paths ({len(footage_paths)}) and card_pngs ({len(card_pngs)}) "
            "must have equal length — one card per footage segment"
        )

    FINAL_DIR.mkdir(parents=True, exist_ok=True)
    slug = team.lower().replace(" ", "_")
    ts = int(time.time())
    out_path = FINAL_DIR / f"{slug}_wc2026_{ts}.mp4"

    with tempfile.TemporaryDirectory(prefix="wc_asm_") as tmp_dir:
        tmp = Path(tmp_dir)

        # ── Step 1: overlay card on each footage segment ───────────────────────
        seg_paths: list[Path] = []
        n = len(footage_paths)
        for i, (footage, card) in enumerate(zip(footage_paths, card_pngs)):
            dest = tmp / f"seg_{i:02d}.mp4"
            print(f"[assembler] [{i+1}/{n}] {card.stem} overlay → {dest.name}")
            ok = _overlay_segment(footage, card, dest)
            if not ok or not dest.exists() or dest.stat().st_size < 1_000:
                print(f"[assembler]   overlay failed — using raw footage for segment {i+1}")
                shutil.copy(str(footage), str(dest))
            seg_paths.append(dest)

        # ── Step 2: concatenate ────────────────────────────────────────────────
        concat_path = tmp / "concat.mp4"
        print(f"[assembler] Concatenating {len(seg_paths)} segments...")
        if not _concat_segments(seg_paths, concat_path):
            raise RuntimeError("[assembler] Concat failed — check ffmpeg stderr above")

        # ── Step 3: mix narration (optional) ──────────────────────────────────
        narration = Path(narration_path) if narration_path else None
        if narration and narration.exists():
            print(f"[assembler] Mixing narration at -3 dB...")
            mixed = tmp / "mixed.mp4"
            if _mix_narration(concat_path, narration, mixed):
                shutil.copy(str(mixed), str(out_path))
            else:
                print("[assembler] Narration mix failed — keeping silent video")
                shutil.copy(str(concat_path), str(out_path))
        else:
            shutil.copy(str(concat_path), str(out_path))

    size_mb = out_path.stat().st_size / (1024 * 1024)
    print(f"[assembler] Done → {out_path} ({size_mb:.1f} MB)")
    return out_path
