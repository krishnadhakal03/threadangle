from __future__ import annotations

import json
from pathlib import Path

from .asset_resolver import resolve_assets
from .hook_lab import check_hook_quality
from .motion_rules import check_motion_rules
from .retention_qa import check_retention_rules_scene
from .render_modes import assert_draft_mode_safe
from .schema import Storyboard


def run_qa(storyboard: Storyboard, repo_root: Path, out_path: Path, manifest: dict | None = None) -> dict:
    issues: list[dict] = []
    if not storyboard.scenes[0].narration_text and not storyboard.scenes[0].caption_text:
        issues.append({"severity": "error", "code": "missing_hook", "message": "First scene has no hook text"})

    for warning in assert_draft_mode_safe(storyboard):
        issues.append({"severity": "error", "code": "paid_provider_blocked", "message": warning})

    for resolved in resolve_assets(storyboard, repo_root):
        scene = resolved.scene
        if not scene.narration_text:
            issues.append({"severity": "error", "code": "missing_narration", "scene_id": scene.scene_id})
        if not resolved.exists and scene.visual_source.value != "generated_card":
            issues.append({"severity": "error", "code": "missing_visual", "scene_id": scene.scene_id, "message": resolved.decision.reason})
        if scene.lock_visual and not resolved.exists:
            issues.append({"severity": "error", "code": "locked_asset_missing", "scene_id": scene.scene_id})
        if resolved.decision.status.value == "fallback_used":
            issues.append({"severity": "warning", "code": "provider_fallback_used", "scene_id": scene.scene_id, "message": resolved.decision.reason})
        if scene.visual_source.value in {"user_image", "user_video", "proof_screenshot"} and not scene.privacy_reviewed:
            issues.append({"severity": "warning", "code": "privacy_review_missing", "scene_id": scene.scene_id})
        if scene.caption_text and len(scene.caption_text.split()) > 18:
            issues.append({"severity": "info", "code": "caption_chunk_review", "scene_id": scene.scene_id, "message": "long caption text will be chunked for review"})
        if "$" in (scene.caption_text or scene.narration_text) and scene.caption_safe_zone.y < 1200:
            issues.append({"severity": "warning", "code": "caption_may_overlap_numbers", "scene_id": scene.scene_id})
        if scene.duration > 4.5 and scene.visual_source.value == "generated_card":
            issues.append({"severity": "info", "code": "static_too_long", "scene_id": scene.scene_id})
        motion_warnings = check_motion_rules(scene)
        for warning in motion_warnings:
            issues.append({"severity": "warning", "code": "motion_novelty", "scene_id": scene.scene_id, "message": warning})
        retention_warnings = check_retention_rules_scene(scene)
        for warning in retention_warnings:
            issues.append({"severity": "warning", "code": "retention", "scene_id": scene.scene_id, "message": warning})
        hook_warning = check_hook_quality(scene)
        if hook_warning:
            issues.append({"severity": "warning", "code": "hook_quality", "scene_id": scene.scene_id, "message": hook_warning})

    report = {
        "project_id": storyboard.project_id,
        "format": storyboard.format.value,
        "render_mode": storyboard.render_mode.value,
        "issue_count": len(issues),
        "issues": issues,
        "review_manifest": manifest.get("manifest_path") if manifest else None,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
