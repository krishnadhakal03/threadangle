"""
worldcup/assembler/captions.py

SRT caption generation for World Cup Short segments.

Public API
----------
build_segment_captions(team, seg_names, seg_durations, team_data) -> list[dict]
generate_srt(team, segments) -> Path
"""
from __future__ import annotations

from pathlib import Path

from worldcup.config import OUTPUT_DIR

CAPTIONS_DIR = OUTPUT_DIR / "captions"

_POS_LABELS = {
    "FW": "FORWARD", "MF": "MIDFIELDER",
    "DF": "DEFENDER", "GK": "GOALKEEPER",
}


def _fmt_time(seconds: float) -> str:
    """Format seconds as SRT timestamp  HH:MM:SS,mmm."""
    total_ms = int(round(seconds * 1000))
    ms = total_ms % 1000
    s  = (total_ms // 1000) % 60
    m  = (total_ms // 60_000) % 60
    h  = total_ms // 3_600_000
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def build_segment_captions(
    team: str,
    seg_names: list[str],
    seg_durations: list[float],
    team_data: dict,
) -> list[dict]:
    """
    Build caption text for every segment.

    Returns list of dicts: {key, duration_seconds, caption_text}
    """
    key_players = team_data.get("key_players", [])
    group_info  = team_data.get("group_info", {})
    group_id    = group_info.get("group", "?")
    team_upper  = team.upper()

    def _player_caption(idx: int) -> str:
        if idx < len(key_players):
            p   = key_players[idx]
            pos = _POS_LABELS.get(p.get("position", "").upper(), "PLAYER")
            return f"{p['name'].upper()} · {pos}"
        return f"PLAYER {idx + 1}"

    caption_map: dict[str, str] = {
        "hook":     f"{team_upper} · FIFA WORLD CUP 2026",
        "history":  "THE RECORD",
        "player_0": _player_caption(0),
        "player_1": _player_caption(1),
        "player_2": _player_caption(2),
        "group":    f"GROUP {group_id} · FIFA WORLD CUP 2026",
        "cta":      f"CAN {team_upper} WIN IT ALL?",
    }

    segments = []
    for key, dur in zip(seg_names, seg_durations):
        text = caption_map.get(key, key.upper().replace("_", " "))
        segments.append({"key": key, "duration_seconds": dur, "caption_text": text})
    return segments


XFADE_DUR = 0.5   # must match mp4_assembler._concat_with_xfade xfade_duration


def generate_srt(team: str, segments: list[dict],
                 xfade: float = XFADE_DUR) -> Path:
    """
    Write an SRT file from a segment list, accounting for xfade overlap.

    Each xfade transition removes *xfade* seconds from the total timeline, so
    segment N starts at:
        sum(durations 0..N-1) - N * xfade

    Each dict requires: key, duration_seconds, caption_text.
    Returns path to worldcup/output/captions/{team}.srt
    """
    CAPTIONS_DIR.mkdir(parents=True, exist_ok=True)
    slug     = team.lower().replace(" ", "_")
    srt_path = CAPTIONS_DIR / f"{slug}.srt"

    _SKIP_KEYS = {"player_0", "player_1", "player_2"}

    lines: list[str] = []
    entry_num = 1
    t = 0.0
    for i, seg in enumerate(segments):
        dur = float(seg["duration_seconds"])
        key = seg.get("key", "")

        if key not in _SKIP_KEYS:
            text    = str(seg["caption_text"]).strip()
            t_start = t
            t_end   = t + dur - (xfade if i < len(segments) - 1 else 0)
            lines.append(str(entry_num))
            lines.append(f"{_fmt_time(t_start)} --> {_fmt_time(t_end)}")
            lines.append(text)
            lines.append("")
            entry_num += 1

        t += dur - xfade   # timeline advances for all segments, skipped or not

    srt_path.write_text("\n".join(lines), encoding="utf-8")
    n_written = entry_num - 1
    print(f"[captions] SRT written -> {srt_path} ({n_written} entries)")
    return srt_path
