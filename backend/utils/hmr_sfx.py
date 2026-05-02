"""Local sound-design planning for Hybrid Motion Renderer outputs."""

from __future__ import annotations

from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
SFX_ROOT = REPO_ROOT / "assets" / "sfx"
SFX_ROLES = (
    "whoosh",
    "tick",
    "soft_hit",
    "warning_beep",
    "riser",
    "payoff_chime",
)
SFX_EXTENSIONS = (".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg")
DEFAULT_SFX_VOLUME = 0.18
ROLE_VOLUME = {
    "tick": 0.12,
    "soft_hit": 0.16,
    "warning_beep": 0.14,
    "whoosh": 0.16,
    "riser": 0.14,
    "payoff_chime": 0.18,
}


def _scene_value(scene: Any, key: str, default: Any = None) -> Any:
    if isinstance(scene, dict):
        return scene.get(key, default)
    return getattr(scene, key, default)


def _scene_id(scene: Any, idx: int) -> str:
    return str(
        _scene_value(scene, "id")
        or _scene_value(scene, "scene_id")
        or _scene_value(scene, "scene")
        or _scene_value(scene, "scene_index")
        or idx + 1
    )


def _scene_duration(scene: Any, fallback: float = 2.6) -> float:
    try:
        duration = float(_scene_value(scene, "duration", fallback) or fallback)
        return max(0.1, duration)
    except (TypeError, ValueError):
        return fallback


def _display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path.resolve()).replace("\\", "/")


def sfx_asset_candidates(role: str, asset_root: str | Path = SFX_ROOT) -> list[Path]:
    """Return deterministic local candidates for a supported SFX role."""
    normalized = str(role or "").strip().lower()
    if normalized not in SFX_ROLES:
        return []
    root = Path(asset_root)
    candidates = [root / normalized / f"{normalized}{ext}" for ext in SFX_EXTENSIONS]
    candidates.extend(root / f"{normalized}{ext}" for ext in SFX_EXTENSIONS)
    role_dir = root / normalized
    if role_dir.exists():
        candidates.extend(
            path
            for path in sorted(role_dir.iterdir())
            if path.is_file() and path.suffix.lower() in SFX_EXTENSIONS
        )
    deduped: list[Path] = []
    for path in candidates:
        if path not in deduped:
            deduped.append(path)
    return deduped


def resolve_sfx_asset(role: str, asset_root: str | Path = SFX_ROOT) -> dict[str, Any]:
    """Resolve one local SFX role without fabricating success."""
    candidates = sfx_asset_candidates(role, asset_root)
    for path in candidates:
        if path.exists() and path.is_file():
            return {
                "role": role,
                "status": "resolved",
                "path": str(path.resolve()),
                "display_path": _display_path(path),
                "candidates_checked": [_display_path(candidate) for candidate in candidates],
            }
    return {
        "role": role,
        "status": "missing",
        "path": None,
        "display_path": None,
        "candidates_checked": [_display_path(candidate) for candidate in candidates],
    }


def _auto_roles_for_scene(scene: Any, idx: int) -> list[dict[str, Any]]:
    scene_id = _scene_id(scene, idx).lower()
    template = str(_scene_value(scene, "template", "") or _scene_value(scene, "hybrid_template", "")).lower()
    role = str(_scene_value(scene, "scene_type", "") or _scene_value(scene, "beat_role", "")).lower()
    text = " ".join(
        str(_scene_value(scene, key, "") or "")
        for key in ("caption_text", "narration_text", "visual_description", "description")
    ).lower()
    duration = _scene_duration(scene)
    cues: list[dict[str, Any]] = []

    if idx == 0 or "hook" in scene_id or role == "hook":
        cues.append({"role": "whoosh", "local_time": 0.08, "reason": "hook_open"})
        cues.append({"role": "soft_hit", "local_time": min(0.55, duration * 0.35), "reason": "hook_punch"})
    if "compare" in scene_id or "comparison" in template or "checklist" in template:
        cues.append({"role": "tick", "local_time": min(0.4, duration * 0.25), "reason": "comparison_tick"})
    if "warning" in text or "stop " in text or "leak" in text or "hidden" in text:
        cues.append({"role": "warning_beep", "local_time": min(0.7, duration * 0.3), "reason": "warning_language"})
    if "payoff" in scene_id or "payoff" in template or role == "payoff":
        cues.append({"role": "riser", "local_time": max(0.1, duration - 1.1), "reason": "payoff_rise"})
        cues.append({"role": "payoff_chime", "local_time": max(0.1, duration - 0.25), "reason": "payoff_resolution"})
    if role == "cta" or "cta" in scene_id:
        cues.append({"role": "soft_hit", "local_time": 0.12, "reason": "cta_entry"})

    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, float]] = set()
    for cue in cues:
        key = (str(cue["role"]), round(float(cue["local_time"]), 2))
        if key not in seen:
            deduped.append(cue)
            seen.add(key)
    return deduped


def _explicit_cues_for_scene(scene: Any) -> list[dict[str, Any]]:
    raw = _scene_value(scene, "sfx_cues", None) or _scene_value(scene, "sound_design", None) or []
    if isinstance(raw, dict):
        raw = raw.get("cues", [])
    cues: list[dict[str, Any]] = []
    for item in raw:
        if isinstance(item, str):
            cues.append({"role": item, "local_time": 0.0, "reason": "explicit"})
        elif isinstance(item, dict):
            cue = dict(item)
            cue["role"] = str(cue.get("role") or cue.get("type") or "").strip()
            cue["local_time"] = float(cue.get("local_time", cue.get("time", 0.0)) or 0.0)
            cue.setdefault("reason", "explicit")
            cues.append(cue)
    return [cue for cue in cues if str(cue.get("role") or "").strip()]


def build_sfx_plan(
    scenes: list[Any],
    scene_timings: list[dict[str, Any]] | None = None,
    asset_root: str | Path = SFX_ROOT,
) -> dict[str, Any]:
    """Plan conservative local SFX cues and resolve local assets if present."""
    timings = scene_timings or []
    if not timings:
        cursor = 0.0
        for idx, scene in enumerate(scenes):
            duration = _scene_duration(scene)
            timings.append({"scene_id": _scene_id(scene, idx), "start": cursor, "end": cursor + duration, "duration": duration})
            cursor += duration

    timing_by_scene = {str(row.get("scene_id")): row for row in timings}
    resolutions = {role: resolve_sfx_asset(role, asset_root) for role in SFX_ROLES}
    cues: list[dict[str, Any]] = []

    for idx, scene in enumerate(scenes):
        scene_id = _scene_id(scene, idx)
        timing = timing_by_scene.get(scene_id, {})
        scene_start = float(timing.get("start", 0.0) or 0.0)
        scene_duration = float(timing.get("duration", _scene_duration(scene)) or _scene_duration(scene))
        planned = _explicit_cues_for_scene(scene) or _auto_roles_for_scene(scene, idx)
        for cue in planned:
            role = str(cue.get("role") or "").strip().lower()
            if role not in SFX_ROLES:
                cues.append({
                    "scene_id": scene_id,
                    "role": role,
                    "status": "unsupported_role",
                    "path": None,
                    "timeline_time": round(scene_start, 3),
                    "local_time": 0.0,
                    "volume": DEFAULT_SFX_VOLUME,
                    "reason": cue.get("reason") or "unknown",
                })
                continue
            local_time = min(max(0.0, float(cue.get("local_time", 0.0) or 0.0)), max(0.0, scene_duration - 0.05))
            resolution = resolutions[role]
            cues.append({
                "scene_id": scene_id,
                "role": role,
                "status": resolution["status"],
                "path": resolution["path"],
                "display_path": resolution["display_path"],
                "timeline_time": round(scene_start + local_time, 3),
                "local_time": round(local_time, 3),
                "volume": round(float(cue.get("volume", ROLE_VOLUME.get(role, DEFAULT_SFX_VOLUME))), 3),
                "reason": cue.get("reason") or "auto",
            })

    missing_roles = sorted({cue["role"] for cue in cues if cue["status"] == "missing"})
    return {
        "schema_version": 1,
        "asset_root": _display_path(Path(asset_root)),
        "supported_roles": list(SFX_ROLES),
        "volume_policy": {
            "voice_and_captions_primary": True,
            "default_sfx_volume": DEFAULT_SFX_VOLUME,
            "role_volume": ROLE_VOLUME,
        },
        "cues": cues,
        "resolved_cues": [cue for cue in cues if cue["status"] == "resolved"],
        "missing_roles": missing_roles,
        "missing_cues": [cue for cue in cues if cue["status"] in {"missing", "unsupported_role"}],
        "resolutions": resolutions,
        "render_required": False,
    }


def attach_sfx_plan_to_report(report: dict[str, Any], sfx_plan: dict[str, Any]) -> dict[str, Any]:
    """Attach SFX metadata to a render report and each scene report."""
    report["sfx_plan"] = sfx_plan
    by_scene: dict[str, list[dict[str, Any]]] = {}
    for cue in sfx_plan.get("cues", []):
        by_scene.setdefault(str(cue.get("scene_id")), []).append(cue)
    for row in report.get("scene_reports", []):
        row["sfx_cues"] = by_scene.get(str(row.get("scene_id")), [])
    return report


def build_sfx_mix_command(
    base_audio_path: str | Path,
    output_audio_path: str | Path,
    cues: list[dict[str, Any]],
    *,
    audio_bitrate: str = "160k",
) -> list[str]:
    """Build an ffmpeg command that mixes resolved SFX under the primary audio."""
    resolved = [cue for cue in cues if cue.get("status") == "resolved" and cue.get("path")]
    cmd = ["ffmpeg", "-y", "-i", str(base_audio_path)]
    for cue in resolved:
        cmd.extend(["-i", str(cue["path"])])
    if not resolved:
        return [*cmd, "-c:a", "aac", "-b:a", audio_bitrate, str(output_audio_path)]

    filters = ["[0:a]volume=1.0[voice]"]
    mix_inputs = ["[voice]"]
    for idx, cue in enumerate(resolved, start=1):
        delay_ms = max(0, int(round(float(cue.get("timeline_time", 0.0) or 0.0) * 1000)))
        volume = min(0.35, max(0.01, float(cue.get("volume", DEFAULT_SFX_VOLUME) or DEFAULT_SFX_VOLUME)))
        label = f"sfx{idx}"
        filters.append(f"[{idx}:a]asetpts=PTS-STARTPTS,volume={volume:.3f},adelay={delay_ms}|{delay_ms}[{label}]")
        mix_inputs.append(f"[{label}]")
    filters.append(f"{''.join(mix_inputs)}amix=inputs={len(mix_inputs)}:duration=first:dropout_transition=0,alimiter=limit=0.95[mixed]")
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
