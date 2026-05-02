"""User proof asset injection for Hybrid Motion Renderer scenes."""

from __future__ import annotations

from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
PROOF_ASSET_ROOT = REPO_ROOT / "assets" / "proof"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".webm"}
PROOF_ASSET_TYPES = {"image", "video", "screenshot", "browser_capture"}
CROP_FIT_MODES = {"cover", "contain", "crop", "fit"}
LOCK_BEHAVIORS = {"replace", "lock", "prefer", "fallback_only"}


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


def _scene_role(scene: Any, idx: int) -> str:
    raw = " ".join(
        str(_scene_value(scene, key, "") or "").lower()
        for key in ("id", "scene_id", "scene", "scene_type", "part", "template", "beat_role")
    )
    if idx == 0 or "hook" in raw:
        return "hook"
    if "cta" in raw:
        return "cta"
    if any(token in raw for token in ("proof", "prompt", "compare", "comparison", "ai")):
        return "proof"
    if any(token in raw for token in ("payoff", "result", "saving")):
        return "payoff"
    if any(token in raw for token in ("reveal", "context", "setup")):
        return "context"
    return "scene"


def _display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path.resolve()).replace("\\", "/")


def _resolve_path(raw_path: str | Path | None, asset_root: str | Path = PROOF_ASSET_ROOT) -> Path | None:
    if not raw_path:
        return None
    path = Path(raw_path).expanduser()
    candidates = [path] if path.is_absolute() else [REPO_ROOT / path, Path(asset_root) / path]
    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate.resolve()
    if not path.is_absolute() and not str(path).replace("\\", "/").startswith("assets/proof/"):
        return (Path(asset_root) / path).resolve()
    return candidates[0].resolve()


def _infer_asset_type(path: Path | None, explicit: str | None = None) -> str:
    normalized = str(explicit or "").strip().lower()
    if normalized in PROOF_ASSET_TYPES:
        return normalized
    suffix = path.suffix.lower() if path else ""
    if suffix in VIDEO_EXTENSIONS:
        return "video"
    if suffix in IMAGE_EXTENSIONS:
        return "screenshot"
    return "image"


def _renderer_asset_type(asset_type: str, path: Path | None) -> str:
    suffix = path.suffix.lower() if path else ""
    if asset_type in {"video", "browser_capture"} or suffix in VIDEO_EXTENSIONS:
        return "stock_footage"
    return "stock_image"


def _normalize_proof_asset(raw: Any, idx: int, source: str) -> dict[str, Any]:
    if isinstance(raw, str):
        data = {"asset_path": raw}
    else:
        data = dict(raw or {})
    scene_id = data.get("scene_id") or data.get("target_scene_id")
    scene_role = data.get("scene_role") or data.get("role")
    crop_fit = str(data.get("crop_fit") or data.get("fit") or "cover").strip().lower()
    lock_behavior = str(data.get("lock_behavior") or data.get("replacement_behavior") or "replace").strip().lower()
    return {
        "id": str(data.get("id") or scene_id or scene_role or f"proof_asset_{idx + 1}"),
        "scene_id": str(scene_id) if scene_id is not None else None,
        "scene_role": str(scene_role).lower() if scene_role is not None else None,
        "asset_path": data.get("asset_path") or data.get("path"),
        "asset_type": str(data.get("asset_type") or data.get("type") or "").strip().lower() or None,
        "crop_fit": crop_fit if crop_fit in CROP_FIT_MODES else "cover",
        "lock_behavior": lock_behavior if lock_behavior in LOCK_BEHAVIORS else "replace",
        "label": data.get("label") or data.get("proof_label"),
        "notes": data.get("notes"),
        "source": source,
    }


def _embedded_assets_from_scenes(scenes: list[Any]) -> list[dict[str, Any]]:
    assets: list[dict[str, Any]] = []
    for idx, scene in enumerate(scenes):
        scene_id = _scene_id(scene, idx)
        embedded = _scene_value(scene, "proof_asset")
        if embedded:
            item = _normalize_proof_asset(embedded, len(assets), "scene.proof_asset")
            item.setdefault("scene_id", scene_id)
            if not item.get("scene_id"):
                item["scene_id"] = scene_id
            assets.append(item)
        proof_path = _scene_value(scene, "proof_asset_path")
        if proof_path:
            assets.append(
                _normalize_proof_asset(
                    {
                        "scene_id": scene_id,
                        "asset_path": proof_path,
                        "asset_type": _scene_value(scene, "proof_asset_type"),
                        "crop_fit": _scene_value(scene, "proof_asset_crop_fit", "cover"),
                        "lock_behavior": _scene_value(scene, "proof_asset_lock_behavior", "replace"),
                        "label": _scene_value(scene, "proof_label"),
                    },
                    len(assets),
                    "scene.proof_asset_path",
                )
            )
    return assets


def _asset_matches_scene(asset: dict[str, Any], scene: Any, idx: int) -> bool:
    target_id = asset.get("scene_id")
    target_role = asset.get("scene_role")
    if target_id and str(target_id) == _scene_id(scene, idx):
        return True
    if target_role and str(target_role).lower() == _scene_role(scene, idx):
        return True
    return False


def build_proof_asset_plan(
    scenes: list[Any],
    proof_assets: list[dict[str, Any]] | None = None,
    *,
    asset_root: str | Path = PROOF_ASSET_ROOT,
) -> dict[str, Any]:
    """Resolve proof assets against scenes without blocking missing fallbacks."""
    normalized = [_normalize_proof_asset(item, idx, "input") for idx, item in enumerate(proof_assets or [])]
    normalized.extend(_embedded_assets_from_scenes(scenes))
    scene_rows = []
    used_asset_ids: set[str] = set()

    for idx, scene in enumerate(scenes):
        scene_id = _scene_id(scene, idx)
        scene_role = _scene_role(scene, idx)
        matches = [
            asset
            for asset in normalized
            if _asset_matches_scene(asset, scene, idx) and asset["id"] not in used_asset_ids
        ]
        chosen = matches[0] if matches else None
        if not chosen:
            scene_rows.append({"scene_id": scene_id, "scene_role": scene_role, "status": "not_targeted", "proof_asset": None})
            continue

        used_asset_ids.add(str(chosen["id"]))
        resolved_path = _resolve_path(chosen.get("asset_path"), asset_root)
        asset_type = _infer_asset_type(resolved_path, chosen.get("asset_type"))
        exists = bool(resolved_path and resolved_path.exists() and resolved_path.is_file())
        scene_rows.append(
            {
                "scene_id": scene_id,
                "scene_role": scene_role,
                "status": "resolved" if exists else "missing",
                "proof_asset": {
                    **chosen,
                    "asset_type": asset_type,
                    "resolved_path": str(resolved_path) if exists else None,
                    "display_path": _display_path(resolved_path) if exists and resolved_path else None,
                    "candidate_path": _display_path(resolved_path) if resolved_path else None,
                    "renderer_asset_type": _renderer_asset_type(asset_type, resolved_path),
                    "replaces_scene_visual": exists and chosen["lock_behavior"] in {"replace", "lock", "prefer"},
                    "locks_replacement": chosen["lock_behavior"] == "lock",
                },
            }
        )

    unresolved_targets = []
    for asset in normalized:
        if not any(_asset_matches_scene(asset, scene, idx) for idx, scene in enumerate(scenes)):
            unresolved_targets.append({**asset, "status": "target_scene_not_found"})

    return {
        "schema_version": 1,
        "asset_root": _display_path(Path(asset_root)),
        "convention": "assets/proof/<topic_or_run>/",
        "supported_asset_types": sorted(PROOF_ASSET_TYPES),
        "scene_assets": scene_rows,
        "resolved_assets": [row for row in scene_rows if row["status"] == "resolved"],
        "missing_assets": [row for row in scene_rows if row["status"] == "missing"],
        "unresolved_targets": unresolved_targets,
        "fallback_behavior": "missing proof assets are reported and existing scene fallback continues",
    }


def proof_asset_for_scene(proof_plan: dict[str, Any], scene_id: Any) -> dict[str, Any] | None:
    """Return a resolved proof asset row for a scene, if one exists."""
    for row in proof_plan.get("scene_assets", []):
        if str(row.get("scene_id")) == str(scene_id) and row.get("status") == "resolved":
            return row
    return None


def proof_asset_resolution_fields(row: dict[str, Any]) -> dict[str, Any]:
    """Map a resolved proof asset row into the renderer's flat asset fields."""
    proof_asset = row.get("proof_asset") or {}
    return {
        "resolved_asset_type": proof_asset.get("renderer_asset_type"),
        "resolved_asset_path": proof_asset.get("resolved_path"),
        "resolved_asset_provider": "user_proof_asset",
        "asset_resolution_status": "resolved",
        "fallback_used": False,
        "query_used": None,
        "queries_attempted": [],
        "provider_available": True,
        "missing_config": [],
        "metadata": {
            "proof_asset": proof_asset,
            "proof_asset_scene_role": row.get("scene_role"),
        },
    }
