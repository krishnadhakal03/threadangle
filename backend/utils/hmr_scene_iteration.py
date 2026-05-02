"""Scene lock and override workflow helpers for HMR iteration."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


OVERRIDE_FIELD_GROUPS = {
    "script": {"script", "narration", "narration_text", "voiceover"},
    "visual": {"visual", "template", "hybrid_template", "visual_description", "style"},
    "asset": {"asset", "asset_path", "proof_asset_path", "proof_asset", "resolved_asset_path"},
    "timing": {"timing", "duration", "start", "end"},
    "caption": {"caption", "caption_text", "caption_behavior", "allow_caption_edit"},
}
SUPPORTED_OVERRIDE_FIELDS = sorted({field for fields in OVERRIDE_FIELD_GROUPS.values() for field in fields})


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


def _normalize_allowed(fields: list[str] | None) -> set[str]:
    if not fields:
        return set()
    normalized = {str(field).strip().lower() for field in fields if str(field).strip()}
    expanded = set(normalized)
    for field in list(normalized):
        expanded.update(OVERRIDE_FIELD_GROUPS.get(field, set()))
    return expanded


def _normalize_lock(raw: Any, scene_id: str | None = None) -> dict[str, Any]:
    data = dict(raw or {})
    lock_scene_id = str(data.get("scene_id") or data.get("target_scene_id") or scene_id or "")
    allowed = data.get("allowed_override_fields") or data.get("allowed_overrides") or []
    return {
        "scene_id": lock_scene_id,
        "lock_reason": data.get("lock_reason") or data.get("reason") or "approved_scene_locked",
        "locked_asset_reference": data.get("locked_asset_reference") or data.get("asset_reference"),
        "locked_render_reference": data.get("locked_render_reference") or data.get("render_reference"),
        "allowed_override_fields": sorted(_normalize_allowed(allowed)),
        "source": data.get("source") or "input",
    }


def _embedded_locks(scenes: list[Any]) -> list[dict[str, Any]]:
    locks = []
    for idx, scene in enumerate(scenes):
        scene_id = _scene_id(scene, idx)
        raw_lock = _scene_value(scene, "scene_lock")
        if raw_lock:
            locks.append(_normalize_lock(raw_lock, scene_id))
        elif _scene_value(scene, "lock_scene") or _scene_value(scene, "lock_visual"):
            locks.append(
                _normalize_lock(
                    {
                        "scene_id": scene_id,
                        "lock_reason": _scene_value(scene, "lock_reason", "scene_marked_locked"),
                        "locked_asset_reference": _scene_value(scene, "asset_path") or _scene_value(scene, "proof_asset_path"),
                        "allowed_override_fields": _scene_value(scene, "allowed_override_fields", []),
                        "source": "scene_flags",
                    },
                    scene_id,
                )
            )
    return locks


def normalize_scene_locks(scenes: list[Any], scene_locks: list[dict[str, Any]] | None = None) -> dict[str, dict[str, Any]]:
    """Return scene locks keyed by scene id, including embedded scene flags."""
    locks = [_normalize_lock(lock) for lock in (scene_locks or [])]
    locks.extend(_embedded_locks(scenes))
    out: dict[str, dict[str, Any]] = {}
    for lock in locks:
        if lock["scene_id"]:
            out[lock["scene_id"]] = lock
    return out


def _normalize_override(raw: dict[str, Any]) -> dict[str, Any]:
    data = dict(raw or {})
    scene_id = str(data.get("scene_id") or data.get("target_scene_id") or "")
    fields = dict(data.get("fields") or {})
    for key in SUPPORTED_OVERRIDE_FIELDS:
        if key in data and key not in fields:
            fields[key] = data[key]
    return {
        "scene_id": scene_id,
        "fields": fields,
        "reason": data.get("reason") or "manual_scene_override",
        "source": data.get("source") or "input",
    }


def _field_group(field: str) -> str:
    normalized = str(field).strip().lower()
    for group, fields in OVERRIDE_FIELD_GROUPS.items():
        if normalized == group or normalized in fields:
            return group
    return normalized


def _can_override(lock: dict[str, Any] | None, field: str) -> bool:
    if not lock:
        return True
    allowed = set(lock.get("allowed_override_fields") or [])
    if not allowed:
        return False
    normalized = str(field).strip().lower()
    return normalized in allowed or _field_group(normalized) in allowed


def _apply_field(scene: dict[str, Any], field: str, value: Any) -> tuple[str, Any]:
    normalized = str(field).strip()
    aliases = {
        "script": "narration_text",
        "narration": "narration_text",
        "visual": "template",
        "asset": "asset_path",
        "timing": "duration",
        "caption": "caption_text",
        "caption_behavior": "allow_caption_edit",
    }
    target = aliases.get(normalized, normalized)
    scene[target] = value
    return target, value


def apply_scene_locks_and_overrides(
    scenes: list[Any],
    *,
    scene_locks: list[dict[str, Any]] | None = None,
    scene_overrides: list[dict[str, Any]] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Apply per-scene overrides while preserving locked scenes unless allowed."""
    copied = [deepcopy(scene) if isinstance(scene, dict) else deepcopy(getattr(scene, "model_dump", lambda **_: vars(scene))()) for scene in scenes]
    locks_by_scene = normalize_scene_locks(copied, scene_locks)
    overrides = [_normalize_override(item) for item in (scene_overrides or [])]
    applied: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    missing_targets: list[dict[str, Any]] = []

    scene_by_id = {_scene_id(scene, idx): scene for idx, scene in enumerate(copied)}
    for override in overrides:
        scene_id = override["scene_id"]
        scene = scene_by_id.get(scene_id)
        if scene is None:
            missing_targets.append({**override, "status": "target_scene_not_found"})
            continue
        lock = locks_by_scene.get(scene_id)
        applied_fields = []
        rejected_fields = []
        for field, value in override["fields"].items():
            if _can_override(lock, field):
                target, applied_value = _apply_field(scene, field, value)
                applied_fields.append({"field": field, "target": target, "value": applied_value})
            else:
                rejected_fields.append({"field": field, "reason": "scene_locked_field_not_allowed"})
        if applied_fields:
            applied.append({"scene_id": scene_id, "reason": override["reason"], "fields": applied_fields})
        if rejected_fields:
            rejected.append({
                "scene_id": scene_id,
                "lock_reason": lock.get("lock_reason") if lock else None,
                "fields": rejected_fields,
            })

    locked_scene_rows = []
    for idx, scene in enumerate(copied):
        scene_id = _scene_id(scene, idx)
        lock = locks_by_scene.get(scene_id)
        if not lock:
            continue
        scene["scene_lock"] = lock
        locked_scene_rows.append({
            **lock,
            "preserved": not any(row["scene_id"] == scene_id for row in applied),
            "applied_override_count": sum(1 for row in applied if row["scene_id"] == scene_id),
        })

    return copied, {
        "schema_version": 1,
        "supported_override_fields": SUPPORTED_OVERRIDE_FIELDS,
        "locked_scenes": locked_scene_rows,
        "applied_overrides": applied,
        "rejected_overrides": rejected,
        "missing_override_targets": missing_targets,
        "preservation_policy": "locked scenes are unchanged unless the override field is explicitly allowed",
    }
