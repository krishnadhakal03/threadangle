"""Manifest and freeze guards for HMR review artifacts."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from .hmr_posting_gate import compute_human_posting_gate
except ImportError:  # pragma: no cover - direct script execution fallback
    from hmr_posting_gate import compute_human_posting_gate


MANIFEST_FILENAME = "manifest.json"
SCHEMA_VERSION = 1


class FrozenArtifactError(RuntimeError):
    """Raised when a write targets a frozen HMR artifact package."""


def _read_manifest(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _candidate_manifest_paths(path: Path) -> list[Path]:
    resolved = Path(path).expanduser().resolve()
    base = resolved.parent if resolved.suffix else resolved
    candidates = [base / MANIFEST_FILENAME, base / "review_package" / MANIFEST_FILENAME]
    candidates.extend(parent / MANIFEST_FILENAME for parent in base.parents)
    deduped: list[Path] = []
    for candidate in candidates:
        if candidate not in deduped:
            deduped.append(candidate)
    return deduped


def find_frozen_manifest(path: str | Path) -> tuple[Path, dict[str, Any]] | None:
    """Return the nearest frozen manifest protecting path, if one exists."""
    for manifest_path in _candidate_manifest_paths(Path(path)):
        manifest = _read_manifest(manifest_path)
        if manifest and manifest.get("frozen") is True:
            return manifest_path, manifest
    return None


def assert_not_frozen_output(path: str | Path, *, force: bool = False) -> None:
    """Refuse writes under frozen HMR artifact packages unless force is explicit."""
    frozen = find_frozen_manifest(path)
    if not frozen or force:
        return
    manifest_path, manifest = frozen
    gate = manifest.get("human_posting_gate") or manifest.get("final_human_decision") or "frozen"
    raise FrozenArtifactError(
        f"Refusing to write under frozen HMR artifact package protected by {manifest_path} "
        f"(human_posting_gate={gate!r}). Pass force=True only for an explicit maintenance task."
    )


def build_manifest(
    *,
    topic: str,
    hook: str,
    video_path: str | Path,
    review_package_path: str | Path,
    render_report: dict[str, Any] | None = None,
    qa_report: dict[str, Any] | None = None,
    human_posting_gate: str | None = None,
    frozen: bool = False,
    paid_providers_used: dict[str, bool] | None = None,
    hook_lab: dict[str, Any] | None = None,
    first_3_seconds: dict[str, Any] | None = None,
    pattern_interrupts: dict[str, Any] | None = None,
    creative_qa: dict[str, Any] | None = None,
    agency_preset: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a lightweight manifest for a newly generated HMR review package."""
    render_report = render_report or {}
    qa_report = qa_report or {}
    postability = qa_report.get("postability_score") or {}
    gate = human_posting_gate or compute_human_posting_gate(render_report=render_report, qa_report=qa_report)
    scene_reports = render_report.get("scene_reports") or []
    resolved_real_assets = [
        {
            "scene_id": row.get("scene_id"),
            "type": row.get("resolved_asset_type"),
            "provider": row.get("resolved_asset_provider"),
            "path": row.get("resolved_asset_path"),
        }
        for row in scene_reports
        if row.get("resolved_asset_path")
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "topic": topic,
        "hook": hook,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "video_path": str(video_path),
        "review_package_path": str(review_package_path),
        "technical_status": qa_report.get("technical_status"),
        "postability_status": qa_report.get("postability_status"),
        "average_score": postability.get("average_score"),
        "human_posting_gate": gate,
        "media_mix": render_report.get("media_mix") or {},
        "hook_lab": hook_lab or render_report.get("hook_lab") or {},
        "first_3_seconds": first_3_seconds or render_report.get("first_3_sec_strategy") or {},
        "pattern_interrupts": pattern_interrupts or render_report.get("pattern_interrupt_plan") or {},
        "agency_preset": agency_preset or render_report.get("agency_preset") or {},
        "creative_qa": creative_qa or render_report.get("creative_qa") or qa_report.get("creative_qa") or {},
        "resolved_real_assets": resolved_real_assets,
        "paid_providers_used": paid_providers_used
        or {
            "elevenlabs": False,
            "runwayml": False,
            "paid_llm": False,
        },
        "frozen": frozen,
        "posted_platforms": [],
        "analytics_placeholders": {
            "youtube_shorts": None,
            "tiktok": None,
            "instagram_reels": None,
            "facebook_reels": None,
        },
    }


def write_manifest(review_package_path: str | Path, manifest: dict[str, Any], *, force: bool = False) -> Path:
    """Write manifest.json after checking the target package is writable."""
    review_dir = Path(review_package_path).expanduser().resolve()
    assert_not_frozen_output(review_dir, force=force)
    review_dir.mkdir(parents=True, exist_ok=True)
    path = review_dir / MANIFEST_FILENAME
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return path
