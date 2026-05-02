"""Smooth multi-clip montage planning for HMR reports."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any


MONTAGE_TRANSITIONS = (
    "hard_cut",
    "whip_cut",
    "speed_ramp",
    "crossfade_short",
    "match_motion_cut",
    "zoom_blend",
)


@dataclass(frozen=True)
class MontageTransitionProfile:
    id: str
    transitions: tuple[str, ...]
    default_transition: str
    max_clip_duration: float
    min_clip_duration: float
    beat_aligned: bool
    voice_aligned: bool
    motion_continuity_target: str

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["transitions"] = list(self.transitions)
        return data


MONTAGE_PROFILES: dict[str, MontageTransitionProfile] = {
    "smooth_high_energy_shorts": MontageTransitionProfile(
        id="smooth_high_energy_shorts",
        transitions=MONTAGE_TRANSITIONS,
        default_transition="match_motion_cut",
        max_clip_duration=1.35,
        min_clip_duration=0.45,
        beat_aligned=True,
        voice_aligned=True,
        motion_continuity_target="direction_or_energy_match",
    ),
    "clean_proof_montage": MontageTransitionProfile(
        id="clean_proof_montage",
        transitions=("hard_cut", "crossfade_short", "match_motion_cut", "zoom_blend"),
        default_transition="crossfade_short",
        max_clip_duration=1.8,
        min_clip_duration=0.6,
        beat_aligned=False,
        voice_aligned=True,
        motion_continuity_target="readability_first",
    ),
}


def get_montage_profile(profile_id: str | None = None) -> MontageTransitionProfile:
    if not profile_id:
        return MONTAGE_PROFILES["smooth_high_energy_shorts"]
    try:
        return MONTAGE_PROFILES[profile_id]
    except KeyError as exc:
        raise ValueError(f"Unknown montage profile: {profile_id}") from exc


def _round_time(value: float) -> float:
    return round(max(0.0, float(value)), 3)


def _scene_id(row: dict[str, Any]) -> str:
    return str(row.get("scene_id") or row.get("id") or row.get("scene") or "")


def _asset_paths(row: dict[str, Any]) -> list[str]:
    paths = [str(path) for path in row.get("resolved_asset_paths", []) or [] if path]
    single = row.get("resolved_asset_path")
    if single:
        paths.insert(0, str(single))
    deduped = []
    for path in paths:
        if path not in deduped:
            deduped.append(path)
    return deduped


def _motion_hint(row: dict[str, Any], index: int) -> str:
    template = str(row.get("template") or "").lower()
    media = str(row.get("media_classification") or "").lower()
    if "payoff" in template or row.get("number_reveal"):
        return "push_in_to_number"
    if "comparison" in template or "split" in template:
        return "left_to_right_compare"
    if "hook" in template or index == 0:
        return "forward_hook_push"
    if "stock" in media:
        return "natural_motion_match"
    if "capture" in media:
        return "screen_motion_match"
    return "energy_match"


def _transition_for_clip(
    *,
    clip_index: int,
    scene_row: dict[str, Any],
    cue: str | None,
    profile: MontageTransitionProfile,
) -> str:
    template = str(scene_row.get("template") or "").lower()
    if clip_index == 0:
        return "hard_cut"
    if cue == "payoff_hit" or "payoff" in template or scene_row.get("number_reveal"):
        return "zoom_blend" if "zoom_blend" in profile.transitions else profile.default_transition
    if cue == "beat_accent":
        return "whip_cut" if "whip_cut" in profile.transitions else profile.default_transition
    if "comparison" in template:
        return "match_motion_cut"
    if clip_index % 4 == 0 and "speed_ramp" in profile.transitions:
        return "speed_ramp"
    return profile.default_transition


def _audio_marker_for_time(audio_timeline: dict[str, Any] | None, timestamp: float) -> str:
    events = (audio_timeline or {}).get("events", []) or []
    nearby = [
        event
        for event in events
        if abs(float(event.get("start", 0.0) or 0.0) - timestamp) <= 0.08
        and event.get("event_type") in {"voice_segment", "transition_hit", "payoff_hit", "sfx_cue"}
    ]
    if not nearby:
        return "estimated_visual_rhythm"
    priority = {"payoff_hit": 0, "transition_hit": 1, "sfx_cue": 2, "voice_segment": 3}
    return str(sorted(nearby, key=lambda event: priority.get(str(event.get("event_type")), 9))[0].get("event_type"))


def _shot_cuts_for_scene(editing_rhythm_plan: dict[str, Any] | None, scene_id: str, start: float, end: float) -> list[dict[str, Any]]:
    cuts = [
        cut
        for cut in (editing_rhythm_plan or {}).get("cut_schedule", []) or []
        if str(cut.get("scene_id")) == scene_id
    ]
    if cuts:
        return cuts
    return [{"scene_id": scene_id, "start": start, "end": end, "duration": end - start, "cue": "scene_hold"}]


def _continuity_score(previous_hint: str | None, current_hint: str, transition: str) -> float:
    if previous_hint is None:
        return 1.0
    prev_tokens = set(re.findall(r"[a-z]+", previous_hint))
    cur_tokens = set(re.findall(r"[a-z]+", current_hint))
    overlap = len(prev_tokens.intersection(cur_tokens))
    base = 0.72 + min(0.18, overlap * 0.06)
    if transition in {"match_motion_cut", "zoom_blend", "crossfade_short"}:
        base += 0.08
    return round(min(1.0, base), 3)


def build_montage_plan(
    *,
    scene_reports: list[dict[str, Any]],
    scene_timings: list[dict[str, Any]],
    editing_rhythm_plan: dict[str, Any] | None = None,
    audio_timeline: dict[str, Any] | None = None,
    profile_id: str | None = None,
) -> dict[str, Any]:
    profile = get_montage_profile(profile_id)
    timing_by_scene = {str(row.get("scene_id")): row for row in scene_timings}
    clips: list[dict[str, Any]] = []
    previous_hint: str | None = None

    for scene_index, row in enumerate(scene_reports):
        scene_id = _scene_id(row)
        timing = timing_by_scene.get(scene_id, {})
        start = float(timing.get("start", 0.0) or 0.0)
        end = float(timing.get("end", start + float(row.get("duration", 0.0) or 0.0)) or 0.0)
        if end <= start:
            end = start + float(row.get("duration", 0.0) or 0.0)
        paths = _asset_paths(row)
        if not paths:
            paths = [f"generated_motion_template:{row.get('template') or scene_id or scene_index + 1}"]
        cuts = _shot_cuts_for_scene(editing_rhythm_plan, scene_id, start, end)
        for cut_index, cut in enumerate(cuts):
            clip_start = float(cut.get("start", start) or start)
            clip_end = float(cut.get("end", end) or end)
            duration = max(profile.min_clip_duration, min(profile.max_clip_duration, clip_end - clip_start))
            asset_path = paths[cut_index % len(paths)]
            motion_hint = _motion_hint(row, scene_index)
            transition_in = _transition_for_clip(
                clip_index=len(clips),
                scene_row=row,
                cue=str(cut.get("cue") or ""),
                profile=profile,
            )
            speed_factor = 1.0
            if transition_in == "speed_ramp":
                speed_factor = 1.12
            elif transition_in == "whip_cut":
                speed_factor = 1.08
            clips.append(
                {
                    "clip_id": f"{scene_id or scene_index + 1}_{cut_index + 1:02d}",
                    "scene_id": scene_id,
                    "path": asset_path,
                    "timeline_start": _round_time(clip_start),
                    "timeline_end": _round_time(clip_start + duration),
                    "trim_start": 0.0,
                    "trim_end": _round_time(duration),
                    "transition_in": transition_in,
                    "transition_out": profile.default_transition,
                    "speed_factor": speed_factor,
                    "beat_voice_alignment_marker": _audio_marker_for_time(audio_timeline, clip_start),
                    "motion_continuity_hint": motion_hint,
                    "motion_continuity_score": _continuity_score(previous_hint, motion_hint, transition_in),
                    "source_status": row.get("asset_resolution_status") or "generated_template",
                }
            )
            previous_hint = motion_hint

    for idx, clip in enumerate(clips):
        clip["transition_out"] = clips[idx + 1]["transition_in"] if idx + 1 < len(clips) else "none"

    return {
        "schema_version": 1,
        "profile": profile.to_dict(),
        "transitions_supported": list(MONTAGE_TRANSITIONS),
        "clips": clips,
        "debug": {
            "scene_count": len(scene_reports),
            "clip_count": len(clips),
            "uses_resolved_assets": any(not str(clip["path"]).startswith("generated_motion_template:") for clip in clips),
            "beat_aligned": profile.beat_aligned,
            "voice_aligned": profile.voice_aligned,
            "render_required": False,
        },
    }


def attach_montage_plan_to_report(report: dict[str, Any], montage_plan: dict[str, Any]) -> dict[str, Any]:
    report["montage_plan"] = montage_plan
    clips_by_scene: dict[str, list[dict[str, Any]]] = {}
    for clip in montage_plan.get("clips", []) or []:
        clips_by_scene.setdefault(str(clip.get("scene_id")), []).append(clip)
    for row in report.get("scene_reports", []) or []:
        row["montage_clips"] = clips_by_scene.get(str(row.get("scene_id")), [])
        row["montage_clip_count"] = len(row["montage_clips"])
    return report
