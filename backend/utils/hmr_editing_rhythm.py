"""Quick-cut editing rhythm planning for Hybrid Motion Renderer reports."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class EditingRhythmProfile:
    id: str
    cut_frequency: str
    max_shot_duration: float
    phrase_sync_enabled: bool
    beat_sync_enabled: bool
    payoff_hit_timing: str
    visual_density_level: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


EDITING_RHYTHM_PROFILES: dict[str, EditingRhythmProfile] = {
    "quick_cut_shorts": EditingRhythmProfile(
        id="quick_cut_shorts",
        cut_frequency="fast",
        max_shot_duration=1.15,
        phrase_sync_enabled=True,
        beat_sync_enabled=True,
        payoff_hit_timing="land_on_number_or_payoff_word",
        visual_density_level="high_controlled",
    ),
    "balanced_clean": EditingRhythmProfile(
        id="balanced_clean",
        cut_frequency="moderate",
        max_shot_duration=1.8,
        phrase_sync_enabled=True,
        beat_sync_enabled=False,
        payoff_hit_timing="scene_midpoint",
        visual_density_level="medium",
    ),
    "slow_clarity": EditingRhythmProfile(
        id="slow_clarity",
        cut_frequency="low",
        max_shot_duration=2.6,
        phrase_sync_enabled=False,
        beat_sync_enabled=False,
        payoff_hit_timing="scene_end_hold",
        visual_density_level="low",
    ),
}

PAYOFF_RE = re.compile(r"(\$?\d[\d,.]*%?|save|saved|found|leak|payoff|result|before|after)", re.IGNORECASE)


def get_editing_rhythm_profile(profile_id: str | None = None) -> EditingRhythmProfile:
    if not profile_id:
        return EDITING_RHYTHM_PROFILES["quick_cut_shorts"]
    try:
        return EDITING_RHYTHM_PROFILES[profile_id]
    except KeyError as exc:
        raise ValueError(f"Unknown editing rhythm profile: {profile_id}") from exc


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


def _scene_text(scene: dict[str, Any]) -> str:
    fields = [
        scene.get("caption_text"),
        scene.get("narration_text"),
        scene.get("subtitle"),
        scene.get("headline"),
        scene.get("text"),
    ]
    return " ".join(str(field) for field in fields if field).strip()


def _fallback_phrase_events(script_text: str, duration: float) -> list[dict[str, Any]]:
    text = str(script_text or "").strip()
    if not text or duration <= 0:
        return []
    phrases = [part.strip() for part in re.split(r"(?<=[.!?])\s+|[,;:]\s+", text) if part.strip()]
    if not phrases:
        words = text.split()
        phrases = [" ".join(words[idx : idx + 4]) for idx in range(0, len(words), 4)]
    if not phrases:
        return []
    step = duration / len(phrases)
    return [
        {"start": _round_time(idx * step), "end": _round_time((idx + 1) * step), "text": phrase}
        for idx, phrase in enumerate(phrases)
    ]


def _timing_confidence(caption_events: list[dict[str, Any]], fallback_used: bool) -> str:
    if fallback_used:
        return "fallback_estimated"
    if not caption_events:
        return "scene_duration_only"
    if any(event.get("word_timings") or event.get("words") for event in caption_events):
        return "word_timing"
    return "caption_phrase_timing"


def _scene_for_time(scene_timings: list[dict[str, Any]], timestamp: float) -> dict[str, Any] | None:
    for scene in scene_timings:
        start = float(scene.get("start", 0.0) or 0.0)
        end = float(scene.get("end", start) or start)
        if start <= timestamp < end or abs(timestamp - end) < 0.001:
            return scene
    return None


def _nearest_payoff_time(
    *,
    scene_timings: list[dict[str, Any]],
    caption_events: list[dict[str, Any]],
    profile: EditingRhythmProfile,
) -> float | None:
    if profile.payoff_hit_timing == "scene_midpoint":
        payoff_scene = next(
            (scene for scene in scene_timings if PAYOFF_RE.search(str(scene.get("label") or scene.get("scene_id") or ""))),
            scene_timings[-1] if scene_timings else None,
        )
        if not payoff_scene:
            return None
        return _round_time((float(payoff_scene["start"]) + float(payoff_scene["end"])) / 2.0)
    if profile.payoff_hit_timing == "scene_end_hold":
        return _round_time(float(scene_timings[-1]["end"])) if scene_timings else None
    for event in caption_events:
        text = _caption_text(event)
        bounds = _event_bounds(event)
        if text and bounds and PAYOFF_RE.search(text):
            return _round_time(bounds[0])
    payoff_scene = next(
        (
            scene
            for scene in scene_timings
            if PAYOFF_RE.search(str(scene.get("label") or scene.get("scene_id") or scene.get("template") or ""))
        ),
        None,
    )
    if payoff_scene:
        return _round_time(float(payoff_scene.get("start", 0.0)))
    return None


def _build_scene_schedule(
    *,
    scene: dict[str, Any],
    caption_events: list[dict[str, Any]],
    profile: EditingRhythmProfile,
    payoff_time: float | None,
) -> list[dict[str, Any]]:
    scene_id = str(scene.get("scene_id") or scene.get("id") or "")
    start = float(scene.get("start", 0.0) or 0.0)
    end = float(scene.get("end", start) or start)
    duration = max(0.0, end - start)
    if duration <= 0:
        return []

    cut_times = {start}
    for event in caption_events:
        bounds = _event_bounds(event)
        if not bounds:
            continue
        event_start, event_end = bounds
        if start < event_start < end:
            cut_times.add(event_start)
        if profile.phrase_sync_enabled and start < event_end < end:
            cut_times.add(event_end)

    cursor = start
    while cursor + profile.max_shot_duration < end:
        cursor += profile.max_shot_duration
        cut_times.add(cursor)

    if payoff_time is not None and start <= payoff_time <= end:
        cut_times.add(payoff_time)

    ordered = sorted(_round_time(item) for item in cut_times if start <= item < end)
    if not ordered or ordered[0] != _round_time(start):
        ordered.insert(0, _round_time(start))
    shots: list[dict[str, Any]] = []
    for idx, cut_start in enumerate(ordered):
        cut_end = _round_time(ordered[idx + 1] if idx + 1 < len(ordered) else end)
        if cut_end <= cut_start:
            continue
        cue = "phrase_cut" if idx else "scene_start"
        if payoff_time is not None and abs(cut_start - payoff_time) < 0.02:
            cue = "payoff_hit"
        elif profile.beat_sync_enabled and idx > 0:
            cue = "beat_accent"
        shots.append(
            {
                "scene_id": scene_id,
                "shot_index": idx + 1,
                "start": cut_start,
                "end": cut_end,
                "duration": _round_time(cut_end - cut_start),
                "cue": cue,
                "transition": "hard_cut" if profile.cut_frequency == "fast" else "clean_cut",
                "motion_preset": "quick_zoom_snap" if cue in {"payoff_hit", "beat_accent"} else "micro_reframe",
            }
        )
    return shots


def build_quick_cut_schedule(
    *,
    script_text: str,
    scene_timings: list[dict[str, Any]],
    caption_events: list[dict[str, Any]] | None = None,
    profile_id: str | None = None,
) -> dict[str, Any]:
    profile = get_editing_rhythm_profile(profile_id)
    normalized_scenes = []
    for scene in scene_timings:
        try:
            start = float(scene.get("start", 0.0))
            end = float(scene.get("end", start + float(scene.get("duration", 0.0) or 0.0)))
        except (TypeError, ValueError):
            continue
        if end <= start:
            continue
        normalized = dict(scene)
        normalized["start"] = _round_time(start)
        normalized["end"] = _round_time(end)
        normalized.setdefault("label", _scene_text(scene))
        normalized_scenes.append(normalized)

    total_duration = max((float(scene["end"]) for scene in normalized_scenes), default=0.0)
    usable_caption_events = [event for event in (caption_events or []) if _event_bounds(event)]
    fallback_used = False
    if not usable_caption_events:
        usable_caption_events = _fallback_phrase_events(script_text, total_duration)
        fallback_used = bool(usable_caption_events)

    payoff_time = _nearest_payoff_time(
        scene_timings=normalized_scenes,
        caption_events=usable_caption_events,
        profile=profile,
    )
    scene_schedules = []
    flat_cuts = []
    for scene in normalized_scenes:
        cuts = _build_scene_schedule(
            scene=scene,
            caption_events=usable_caption_events,
            profile=profile,
            payoff_time=payoff_time,
        )
        scene_schedules.append(
            {
                "scene_id": str(scene.get("scene_id") or scene.get("id") or ""),
                "start": scene["start"],
                "end": scene["end"],
                "planned_shot_count": len(cuts),
                "cuts": cuts,
            }
        )
        flat_cuts.extend(cuts)

    max_duration = max((cut["duration"] for cut in flat_cuts), default=0.0)
    density_warning = len(flat_cuts) / max(1.0, total_duration) > 1.6
    return {
        "schema_version": 1,
        "profile": profile.to_dict(),
        "timing_confidence": _timing_confidence(usable_caption_events, fallback_used),
        "fallback_timing_used": fallback_used,
        "payoff_hit_time": payoff_time,
        "scene_schedules": scene_schedules,
        "cut_schedule": flat_cuts,
        "debug": {
            "scene_count": len(normalized_scenes),
            "caption_event_count": len(usable_caption_events),
            "planned_cut_count": len(flat_cuts),
            "max_planned_shot_duration": _round_time(max_duration),
            "visual_density_warning": density_warning,
            "render_required": False,
        },
    }


def attach_quick_cut_schedule_to_report(
    report: dict[str, Any],
    *,
    schedule: dict[str, Any],
) -> dict[str, Any]:
    report["editing_rhythm_plan"] = schedule
    cuts_by_scene: dict[str, list[dict[str, Any]]] = {}
    for cut in schedule.get("cut_schedule", []):
        cuts_by_scene.setdefault(str(cut.get("scene_id")), []).append(cut)
    for row in report.get("scene_reports", []) or []:
        scene_id = str(row.get("scene_id"))
        row["planned_quick_cuts"] = cuts_by_scene.get(scene_id, [])
        row["planned_quick_cut_count"] = len(row["planned_quick_cuts"])
    return report
