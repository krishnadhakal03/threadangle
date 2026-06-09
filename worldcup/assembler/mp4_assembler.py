"""
Issue #124 — FFmpeg MP4 Assembler

assemble_mp4(team, footage_paths, card_pngs, narration_path=None) -> Path

Chains footage clips with PNG card overlays at 70% opacity, concatenates all
segments, optionally mixes narration at -3 dB, and writes:
  worldcup/output/final/{team}_wc2026_{timestamp}.mp4

Specs: 1080x1920 @ 30fps, H.264 + AAC, target < 50 MB for ~37s content.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Optional

from worldcup.config import OUTPUT_DIR, FPS

FINAL_DIR = OUTPUT_DIR / "final"
FFMPEG    = shutil.which("ffmpeg")   or shutil.which("ffmpeg.exe")   or "ffmpeg"
FFPROBE   = (shutil.which("ffprobe") or shutil.which("ffprobe.exe")
             or str(Path(FFMPEG).parent / "ffprobe"))


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


def _overlay_segment(footage: Path, card: Path, dest: Path,
                     w: int = 1080, h: int = 1920) -> bool:
    """
    Overlay *card* PNG at 70% opacity, centered on *footage*.
    Output resolution = *w*×*h*. Default: 1080×1920 portrait (Shorts).
    For 1920×1080 landscape, the portrait card is pillarboxed (centred strip).
    """
    filter_complex = (
        f"[1:v]scale={w}:{h}:force_original_aspect_ratio=decrease,"
        f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=black@0,"
        "format=rgba,colorchannelmixer=aa=0.7[card];"
        "[0:v][card]overlay=0:0:format=auto[vout]"
    )
    return _run([
        FFMPEG, "-y",
        "-i", str(footage),
        "-loop", "1", "-i", str(card),
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        "-map", "0:a:0",
        "-shortest",
        "-c:v", "libx264", "-preset", "fast", "-crf", "22", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-ac", "2", "-ar", "44100",
        "-r", str(FPS),
        str(dest),
    ], label=f"overlay:{dest.name}")


def _concat_segments(segment_paths: list[Path], dest: Path) -> bool:
    """Join all segments via ffmpeg concat demuxer (hard-cut, used as fallback)."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as f:
        list_path = Path(f.name)
        for p in segment_paths:
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


def _concat_with_xfade(segment_paths: list[Path], dest: Path,
                        xfade_duration: float = 0.5) -> bool:
    """
    Join segments with 0.5s crossfade (xfade) transitions between each pair.

    Each segment's effective contribution = (duration - xfade_duration) so the
    total runtime shrinks by xfade_duration * (n-1) vs a hard-cut concat.
    Audio is concatenated cleanly (no audio xfade — avoids phasing artefacts).
    """
    if len(segment_paths) == 1:
        shutil.copy2(str(segment_paths[0]), str(dest))
        return True

    # Probe every segment duration up front
    durations = [_probe_duration(p) for p in segment_paths]

    # Build -i list
    inputs: list[str] = []
    for p in segment_paths:
        inputs += ["-i", str(p)]

    # Build xfade video chain
    filter_parts: list[str] = []
    prev_label = "0:v"
    offset = 0.0
    for i in range(1, len(segment_paths)):
        offset += durations[i - 1] - xfade_duration
        curr_label = f"v{i}"
        filter_parts.append(
            f"[{prev_label}][{i}:v]xfade=transition=fade:"
            f"duration={xfade_duration:.3f}:offset={offset:.3f}[{curr_label}]"
        )
        prev_label = curr_label

    # Simple audio concat (no xfade on audio — avoids desync)
    audio_in = "".join(f"[{i}:a]" for i in range(len(segment_paths)))
    filter_parts.append(
        f"{audio_in}concat=n={len(segment_paths)}:v=0:a=1[aout]"
    )

    filter_complex = ";".join(filter_parts)

    return _run([
        FFMPEG, "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", f"[{prev_label}]",
        "-map", "[aout]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-ac", "2", "-ar", "44100",
        str(dest),
    ], label="xfade_concat")


def _probe_duration(p: Path) -> float:
    """Return video/audio duration in seconds via ffprobe. Falls back to 37.0."""
    try:
        r = subprocess.run(
            [FFPROBE, "-v", "quiet",
             "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1",
             str(p)],
            capture_output=True, text=True, timeout=15,
        )
        return float(r.stdout.strip())
    except Exception:
        return 37.0


def _add_bgm(input_mp4: Path, output_mp4: Path, has_narration: bool = False) -> bool:
    """
    Mix a looping background music track into *input_mp4*.

    BGM track is chosen by the BGM_TRACK env var:
      BGM_TRACK=hype (default) → worldcup/assets/bgm/football_hype.mp3
      BGM_TRACK=dramatic       → worldcup/assets/bgm/dramatic.mp3

    Volume: 0.12 under narration, 0.20 without (more presence when voice is off).
    Last 3 seconds fade out.
    If BGM file is missing the input is copied unchanged — never crashes.
    """
    track_map = {
        "hype":     "football_hype.mp3",
        "dramatic": "dramatic.mp3",
    }
    track_name   = os.getenv("BGM_TRACK", "hype").lower()
    bgm_filename = track_map.get(track_name, "football_hype.mp3")
    bgm_path     = Path(__file__).resolve().parent.parent / "assets" / "bgm" / bgm_filename

    if not bgm_path.exists():
        print(f"[assembler] BGM not found at {bgm_path} — skipping")
        shutil.copy2(str(input_mp4), str(output_mp4))
        return True

    bgm_vol    = "0.12" if has_narration else "0.20"
    total_dur  = _probe_duration(input_mp4)
    fade_start = max(0.0, total_dur - 3.0)

    print(f"[assembler] Adding BGM ({bgm_filename}, vol={bgm_vol}, fade@{fade_start:.1f}s)")
    return _run([
        FFMPEG, "-y",
        "-i", str(input_mp4),
        "-stream_loop", "-1",          # loop BGM to cover full video length
        "-i", str(bgm_path),
        "-filter_complex",
        (
            f"[1:a]volume={bgm_vol},"
            f"afade=t=out:st={fade_start:.3f}:d=3.0[bgm];"
            f"[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=0[aout]"
        ),
        "-map", "0:v",
        "-map", "[aout]",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        str(output_mp4),
    ], label="bgm_mix")


def _ffmpeg_vf_path(p: Path) -> str:
    """
    Escape an absolute path for use inside an ffmpeg -vf filter value.
    On Windows the drive-letter colon must be escaped: C:/ → C\\:/
    """
    s = str(p.resolve()).replace("\\", "/")
    if len(s) >= 2 and s[1] == ":":
        s = s[0] + "\\:" + s[2:]
    return s


def _burn_captions(video: Path, srt: Path, dest: Path) -> bool:
    """
    Hard-burn SRT captions into video using ffmpeg subtitles filter.
    Style: white text, black outline, bottom-centre, MarginV=120 (above TikTok chrome).
    """
    force_style = (
        "FontName=Arial,"
        "FontSize=18,"
        "Bold=1,"
        "PrimaryColour=&H00FFFFFF,"   # white
        "OutlineColour=&H00000000,"   # black outline
        "BorderStyle=1,"
        "Outline=2,"
        "Shadow=0,"
        "Alignment=2,"                # bottom-centre
        "MarginV=120"                 # 120px above bottom edge
    )
    srt_escaped = _ffmpeg_vf_path(srt)
    return _run([
        FFMPEG, "-y",
        "-i", str(video),
        "-vf", f"subtitles='{srt_escaped}':force_style='{force_style}'",
        "-c:a", "copy",
        str(dest),
    ], label="burn_captions")


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
    srt_path: Optional[Path] = None,
    fmt: str = "short",
) -> Path:
    """
    Assemble a World Cup MP4.

    Parameters
    ----------
    team:           Team name, used in the output filename.
    footage_paths:  One Path per segment, already trimmed to segment duration.
    card_pngs:      One PNG per segment, overlaid at 70% opacity centered.
                    Must have the same length as footage_paths.
    narration_path: Optional WAV/MP3 voiceover mixed at -3 dB.
    srt_path:       Optional SRT file; captions are hard-burned into the video.
    fmt:            "short" (default, 1080×1920) | "long" (1920×1080 landscape).

    Returns
    -------
    Path to worldcup/output/final/{team}_wc2026_{short|long}_{timestamp}.mp4

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
    slug     = team.lower().replace(" ", "_")
    ts       = int(time.time())
    w, h     = (1920, 1080) if fmt == "long" else (1080, 1920)
    out_path = FINAL_DIR / f"{slug}_wc2026_{fmt}_{ts}.mp4"

    with tempfile.TemporaryDirectory(prefix="wc_asm_") as tmp_dir:
        tmp = Path(tmp_dir)

        # ── Step 1: overlay card on each footage segment ───────────────────────
        seg_paths: list[Path] = []
        n = len(footage_paths)
        for i, (footage, card) in enumerate(zip(footage_paths, card_pngs)):
            dest = tmp / f"seg_{i:02d}.mp4"
            print(f"[assembler] [{i+1}/{n}] {card.stem} overlay → {dest.name}")
            ok = _overlay_segment(footage, card, dest, w=w, h=h)
            if not ok or not dest.exists() or dest.stat().st_size < 1_000:
                print(f"[assembler]   overlay failed — using raw footage for segment {i+1}")
                shutil.copy(str(footage), str(dest))
            seg_paths.append(dest)

        # ── Step 2: concatenate with crossfade transitions ────────────────────
        concat_path = tmp / "concat.mp4"
        print(f"[assembler] Concatenating {len(seg_paths)} segments (xfade 0.5s)...")
        if not _concat_with_xfade(seg_paths, concat_path):
            print("[assembler] xfade failed — falling back to hard-cut concat")
            if not _concat_segments(seg_paths, concat_path):
                raise RuntimeError("[assembler] Concat failed — check ffmpeg stderr above")

        # ── Step 3: mix narration (optional) ──────────────────────────────────
        current = concat_path
        narration = Path(narration_path) if narration_path else None
        if narration and narration.exists():
            print(f"[assembler] Mixing narration at -3 dB...")
            mixed = tmp / "mixed.mp4"
            if _mix_narration(current, narration, mixed):
                current = mixed
            else:
                print("[assembler] Narration mix failed — continuing without")

        # ── Step 4: burn captions (optional) ──────────────────────────────────
        srt = Path(srt_path) if srt_path else None
        if srt and srt.exists():
            print(f"[assembler] Burning captions...")
            captioned = tmp / "captioned.mp4"
            if _burn_captions(current, srt, captioned):
                current = captioned
            else:
                print("[assembler] Caption burn failed — outputting without captions")

        # ── Step 5: add BGM ────────────────────────────────────────────────────
        bgm_out = tmp / "bgm_mixed.mp4"
        _add_bgm(current, bgm_out, has_narration=(narration is not None and narration.exists()))
        if bgm_out.exists() and bgm_out.stat().st_size > 1_000:
            current = bgm_out

        shutil.copy(str(current), str(out_path))

    size_mb = out_path.stat().st_size / (1024 * 1024)
    print(f"[assembler] Done → {out_path} ({size_mb:.1f} MB)")
    return out_path
