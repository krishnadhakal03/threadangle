"""Voice, music, and SFX binding timeline planning for HMR."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any


DEFAULT_MIX_RULES = {
    "voice_priority": True,
    "voice_volume": 1.0,
    "music_bed_volume": 0.16,
    "music_ducking_under_voice_db": -12,
    "max_sfx_volume": 0.28,
    "transition_hit_volume": 0.14,
    "payoff_hit_volume": 0.2,
    "limiter": "0.95",
}

PAYOFF_RE = re.compile(r"(\$?\d[\d,.]*%?|save|saved|found|leak|payoff|result|before|after)", re.IGNORECASE)


def _round_time(value: float) -> float:
    return round(max(0.0, float(value)), 3)


def _caption_text(event: dict[str, Any]) -> str:
    return str(event.get("text") or event.get("caption") or "").strip()


def _event_bounds(event: dict[str, Any]) -> tuple[float, float] | None:
    try:
        start = float(event.get("start", 0.0))
        end = float(event.get("end", start))
    except (TypeError, ValueError):
        return None
    if end <= start:
        return None
    return start, end


def _fallback_voice_segments(script_text: str, total_duration: float) -> list[dict[str, Any]]:
    text = str(script_text or "").strip()
    if not text or total_duration <= 0:
        return []
    phrases = [part.strip() for part in re.split(r"(?<=[.!?])\s+|[,;:]\s+", text) if part.strip()]
    if not phrases:
        words = text.split()
        phrases = [" ".join(words[idx : idx + 5]) for idx in range(0, len(words), 5)]
    if not phrases:
        return []
    step = total_duration / len(phrases)
    return [
        {
            "event_type": "voice_segment",
            "id": f"voice_{idx + 1:02d}",
            "start": _round_time(idx * step),
            "end": _round_time((idx + 1) * step),
            "text": phrase,
            "source": "fallback_script_phrase",
            "priority": "primary",
        }
        for idx, phrase in enumerate(phrases)
    ]


def _voice_segments(
    *,
    script_text: str,
    caption_events: list[dict[str, Any]] | None,
    total_duration: float,
) -> tuple[list[dict[str, Any]], str]:
    usable = [event for event in (caption_events or []) if _event_bounds(event)]
    if usable:
        source = "word_timing" if any(event.get("word_timings") or event.get("words") for event in usable) else "caption_phrase_timing"
        return (
            [
                {
                    "event_type": "voice_segment",
                    "id": f"voice_{idx + 1:02d}",
                    "start": _round_time(_event_bounds(event)[0]),  # type: ignore[index]
                    "end": _round_time(_event_bounds(event)[1]),  # type: ignore[index]
                    "text": _caption_text(event),
                    "source": source,
                    "priority": "primary",
                }
                for idx, event in enumerate(usable)
            ],
            source,
        )
    fallback = _fallback_voice_segments(script_text, total_duration)
    return fallback, "fallback_estimated" if fallback else "scene_duration_only"


def _nearest_voice_segment(voice_segments: list[dict[str, Any]], timestamp: float) -> dict[str, Any] | None:
    if not voice_segments:
        return None
    containing = [
        segment
        for segment in voice_segments
        if float(segment["start"]) <= timestamp <= float(segment["end"])
    ]
    if containing:
        return containing[0]
    return min(voice_segments, key=lambda segment: abs(float(segment["start"]) - timestamp))


def _bind_sfx_cues(
    *,
    sfx_plan: dict[str, Any] | None,
    voice_segments: list[dict[str, Any]],
    max_sfx_volume: float,
) -> list[dict[str, Any]]:
    events = []
    for idx, cue in enumerate((sfx_plan or {}).get("cues", []) or []):
        cue_time = float(cue.get("timeline_time", 0.0) or 0.0)
        segment = _nearest_voice_segment(voice_segments, cue_time)
        bound_time = cue_time
        binding = "scene_timing"
        bound_text = ""
        if segment:
            bound_text = str(segment.get("text") or "")
            if cue.get("reason") in {"warning_language", "payoff_resolution", "payoff_rise"} or cue.get("role") in {
                "warning_beep",
                "payoff_chime",
                "riser",
            }:
                bound_time = float(segment["start"])
                binding = str(segment.get("source") or "voice_segment")
        events.append(
            {
                "event_type": "sfx_cue",
                "id": f"sfx_{idx + 1:02d}",
                "scene_id": str(cue.get("scene_id") or ""),
                "role": cue.get("role"),
                "start": _round_time(bound_time),
                "end": _round_time(bound_time + float(cue.get("duration", 0.35) or 0.35)),
                "volume": round(min(max_sfx_volume, max(0.01, float(cue.get("volume", 0.16) or 0.16))), 3),
                "asset_status": cue.get("status"),
                "path": cue.get("path"),
                "reason": cue.get("reason"),
                "binding": binding,
                "bound_voice_text": bound_text,
            }
        )
    return events


def _transition_events(editing_rhythm_plan: dict[str, Any] | None) -> list[dict[str, Any]]:
    events = []
    cuts = (editing_rhythm_plan or {}).get("cut_schedule", []) or []
    for idx, cut in enumerate(cuts):
        if cut.get("cue") not in {"beat_accent", "payoff_hit"}:
            continue
        start = float(cut.get("start", 0.0) or 0.0)
        event_type = "payoff_hit" if cut.get("cue") == "payoff_hit" else "transition_hit"
        events.append(
            {
                "event_type": event_type,
                "id": f"{event_type}_{idx + 1:02d}",
                "scene_id": str(cut.get("scene_id") or ""),
                "start": _round_time(start),
                "end": _round_time(start + 0.18),
                "volume": DEFAULT_MIX_RULES["payoff_hit_volume"]
                if event_type == "payoff_hit"
                else DEFAULT_MIX_RULES["transition_hit_volume"],
                "binding": "editing_rhythm_cut",
                "motion_preset": cut.get("motion_preset"),
            }
        )
    return events


def build_audio_binding_timeline(
    *,
    script_text: str,
    scene_timings: list[dict[str, Any]],
    caption_events: list[dict[str, Any]] | None = None,
    sfx_plan: dict[str, Any] | None = None,
    editing_rhythm_plan: dict[str, Any] | None = None,
    voice_audio_path: str | Path | None = None,
    music_bed_path: str | Path | None = None,
    music_enabled: bool = False,
    mix_rules: dict[str, Any] | None = None,
) -> dict[str, Any]:
    rules = {**DEFAULT_MIX_RULES, **(mix_rules or {})}
    total_duration = max(
        [
            float(scene.get("end", 0.0) or 0.0)
            for scene in scene_timings
            if isinstance(scene, dict)
        ]
        or [0.0]
    )
    voice_segments, timing_confidence = _voice_segments(
        script_text=script_text,
        caption_events=caption_events,
        total_duration=total_duration,
    )
    events: list[dict[str, Any]] = [*voice_segments]

    if music_enabled or music_bed_path:
        events.append(
            {
                "event_type": "music_bed",
                "id": "music_bed_01",
                "start": 0.0,
                "end": _round_time(total_duration),
                "volume": rules["music_bed_volume"],
                "path": str(music_bed_path) if music_bed_path else None,
                "status": "planned_local" if music_bed_path else "missing_optional",
                "ducking_under_voice_db": rules["music_ducking_under_voice_db"],
                "binding": "full_timeline_under_voice",
            }
        )

    events.extend(
        _bind_sfx_cues(
            sfx_plan=sfx_plan,
            voice_segments=voice_segments,
            max_sfx_volume=float(rules["max_sfx_volume"]),
        )
    )
    events.extend(_transition_events(editing_rhythm_plan))
    events = sorted(events, key=lambda event: (float(event.get("start", 0.0) or 0.0), str(event.get("event_type"))))

    return {
        "schema_version": 1,
        "timing_source": "voiceover_primary",
        "timing_confidence": timing_confidence,
        "voice_audio_path": str(voice_audio_path) if voice_audio_path else None,
        "music_bed_path": str(music_bed_path) if music_bed_path else None,
        "mix_rules": rules,
        "event_types": ["voice_segment", "sfx_cue", "music_bed", "transition_hit", "payoff_hit"],
        "events": events,
        "debug": {
            "voice_segment_count": len(voice_segments),
            "sfx_event_count": len([event for event in events if event.get("event_type") == "sfx_cue"]),
            "transition_event_count": len([event for event in events if event.get("event_type") == "transition_hit"]),
            "payoff_event_count": len([event for event in events if event.get("event_type") == "payoff_hit"]),
            "music_bed_planned": any(event.get("event_type") == "music_bed" for event in events),
            "render_required": False,
            "paid_providers_used": {
                "elevenlabs": False,
                "paid_music": False,
                "paid_sfx": False,
            },
        },
    }


def attach_audio_timeline_to_report(report: dict[str, Any], audio_timeline: dict[str, Any]) -> dict[str, Any]:
    report["audio_binding_timeline"] = audio_timeline
    sfx_by_scene: dict[str, list[dict[str, Any]]] = {}
    for event in audio_timeline.get("events", []):
        if event.get("event_type") == "sfx_cue":
            sfx_by_scene.setdefault(str(event.get("scene_id")), []).append(event)
    for row in report.get("scene_reports", []) or []:
        row["audio_bound_sfx_cues"] = sfx_by_scene.get(str(row.get("scene_id")), [])
    return report


def build_audio_mix_plan(
    *,
    voice_audio_path: str | Path,
    output_audio_path: str | Path,
    audio_timeline: dict[str, Any],
    audio_bitrate: str = "160k",
) -> dict[str, Any]:
    """Build an ffmpeg command plan without running it."""
    events = audio_timeline.get("events", []) or []
    mix_rules = audio_timeline.get("mix_rules", DEFAULT_MIX_RULES)
    cmd = ["ffmpeg", "-y", "-i", str(voice_audio_path)]
    input_events = []
    for event in events:
        if event.get("event_type") not in {"sfx_cue", "music_bed", "transition_hit", "payoff_hit"}:
            continue
        path = event.get("path")
        if not path:
            continue
        input_events.append(event)
        cmd.extend(["-i", str(path)])
    if not input_events:
        return {
            "render_required": False,
            "command": [*cmd, "-c:a", "aac", "-b:a", audio_bitrate, str(output_audio_path)],
            "input_event_count": 0,
        }

    filters = [f"[0:a]volume={float(mix_rules.get('voice_volume', 1.0)):.3f}[voice]"]
    mix_inputs = ["[voice]"]
    for idx, event in enumerate(input_events, start=1):
        delay_ms = max(0, int(round(float(event.get("start", 0.0) or 0.0) * 1000)))
        volume = float(event.get("volume", 0.16) or 0.16)
        label = f"aud{idx}"
        if event.get("event_type") == "music_bed":
            filters.append(
                f"[{idx}:a]asetpts=PTS-STARTPTS,volume={volume:.3f},"
                f"sidechaincompress=threshold=0.08:ratio=6:attack=20:release=250[{label}]"
            )
        else:
            volume = min(float(mix_rules.get("max_sfx_volume", 0.28)), volume)
            filters.append(f"[{idx}:a]asetpts=PTS-STARTPTS,volume={volume:.3f},adelay={delay_ms}|{delay_ms}[{label}]")
        mix_inputs.append(f"[{label}]")
    filters.append(
        f"{''.join(mix_inputs)}amix=inputs={len(mix_inputs)}:duration=first:dropout_transition=0,"
        f"alimiter=limit={mix_rules.get('limiter', '0.95')}[mixed]"
    )
    return {
        "render_required": False,
        "command": [
            *cmd,
            "-filter_complex",
            ";".join(filters),
            "-map",
            "[mixed]",
            "-c:a",
            "aac",
            "-b:a",
            audio_bitrate,
            str(output_audio_path),
        ],
        "input_event_count": len(input_events),
    }


def _is_local_existing_file(path: Any) -> bool:
    if not path:
        return False
    text = str(path)
    if text.startswith(("http://", "https://", "s3://", "gs://")):
        return False
    candidate = Path(text).expanduser()
    return candidate.exists() and candidate.is_file()


def _executable_mix_command(
    *,
    voice_audio_path: str | Path,
    output_audio_path: str | Path,
    events: list[dict[str, Any]],
    mix_rules: dict[str, Any],
    audio_bitrate: str,
) -> list[str]:
    cmd = ["ffmpeg", "-y", "-i", str(voice_audio_path)]
    for event in events:
        cmd.extend(["-i", str(event["path"])])
    filters = [f"[0:a]volume={float(mix_rules.get('voice_volume', 1.0)):.3f}[voice]"]
    mix_inputs = ["[voice]"]
    for idx, event in enumerate(events, start=1):
        start_ms = max(0, int(round(float(event.get("start", 0.0) or 0.0) * 1000)))
        label = f"aud{idx}"
        volume = float(event.get("volume", mix_rules.get("music_bed_volume", 0.16)) or 0.16)
        if event.get("event_type") != "music_bed":
            volume = min(float(mix_rules.get("max_sfx_volume", 0.28)), volume)
        filters.append(f"[{idx}:a]asetpts=PTS-STARTPTS,volume={volume:.3f},adelay={start_ms}|{start_ms}[{label}]")
        mix_inputs.append(f"[{label}]")
    filters.append(
        f"{''.join(mix_inputs)}amix=inputs={len(mix_inputs)}:duration=first:dropout_transition=0,"
        f"alimiter=limit={mix_rules.get('limiter', '0.95')}[mixed]"
    )
    return [
        *cmd,
        "-filter_complex",
        ";".join(filters),
        "-map",
        "[mixed]",
        "-c:a",
        "aac",
        "-b:a",
        audio_bitrate,
        str(output_audio_path),
    ]


def execute_audio_mix_plan(
    *,
    voice_audio_path: str | Path | None,
    output_audio_path: str | Path,
    audio_timeline: dict[str, Any],
    enabled: bool = False,
    audio_bitrate: str = "160k",
    timeout: int = 90,
) -> dict[str, Any]:
    """Execute a local-only audio mix plan when explicitly enabled."""
    base = {
        "audio_mix_execution_status": "not_requested" if not enabled else "skipped",
        "mixed": False,
        "mixed_audio_path": None,
        "mixed_event_count": 0,
        "skipped_event_count": 0,
        "local_assets_only": True,
        "skipped_missing_assets": [],
        "skipped_non_local_assets": [],
        "command": None,
    }
    if not enabled:
        return base
    if not voice_audio_path or not _is_local_existing_file(voice_audio_path):
        base["audio_mix_execution_status"] = "skipped_missing_voice"
        base["skipped_missing_assets"].append(str(voice_audio_path) if voice_audio_path else "voice_audio_path")
        return base

    mix_rules = audio_timeline.get("mix_rules", DEFAULT_MIX_RULES)
    mixable_types = {"sfx_cue", "music_bed", "transition_hit", "payoff_hit"}
    events = []
    skipped_missing = []
    skipped_non_local = []
    for event in audio_timeline.get("events", []) or []:
        if event.get("event_type") not in mixable_types:
            continue
        path = event.get("path")
        if path and str(path).startswith(("http://", "https://", "s3://", "gs://")):
            skipped_non_local.append({"event_id": event.get("id"), "path": str(path)})
            continue
        if not _is_local_existing_file(path):
            skipped_missing.append({"event_id": event.get("id"), "path": str(path) if path else None})
            continue
        events.append(event)

    base["skipped_missing_assets"] = skipped_missing
    base["skipped_non_local_assets"] = skipped_non_local
    base["skipped_event_count"] = len(skipped_missing) + len(skipped_non_local)
    if not events:
        base["audio_mix_execution_status"] = "skipped_missing_assets"
        return base

    output = Path(output_audio_path).expanduser()
    output.parent.mkdir(parents=True, exist_ok=True)
    cmd = _executable_mix_command(
        voice_audio_path=voice_audio_path,
        output_audio_path=output,
        events=events,
        mix_rules=mix_rules,
        audio_bitrate=audio_bitrate,
    )
    base["command"] = cmd
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=timeout)
    except Exception as exc:
        base["audio_mix_execution_status"] = "failed"
        base["error"] = str(exc)[:160]
        return base

    base.update(
        {
            "audio_mix_execution_status": "mixed",
            "mixed": True,
            "mixed_audio_path": str(output),
            "mixed_event_count": len(events),
        }
    )
    if base["skipped_event_count"]:
        base["audio_mix_execution_status"] = "mixed_with_skips"
    return base
