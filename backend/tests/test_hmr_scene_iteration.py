from __future__ import annotations

import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def test_locked_scene_rejects_unallowed_override_and_preserves_scene():
    from utils.hmr_scene_iteration import apply_scene_locks_and_overrides

    scenes = [{"id": "hook", "template": "hook_footage_overlay", "duration": 2.0, "caption_text": "Original hook"}]
    updated, report = apply_scene_locks_and_overrides(
        scenes,
        scene_locks=[
            {
                "scene_id": "hook",
                "lock_reason": "approved hook visual",
                "locked_asset_reference": "review_package/hook.mp4",
                "allowed_override_fields": ["caption"],
            }
        ],
        scene_overrides=[{"scene_id": "hook", "fields": {"template": "money_shock_math"}}],
    )

    assert updated[0]["template"] == "hook_footage_overlay"
    assert updated[0]["scene_lock"]["lock_reason"] == "approved hook visual"
    assert report["locked_scenes"][0]["preserved"] is True
    assert report["rejected_overrides"][0]["fields"][0]["field"] == "template"


def test_locked_scene_allows_declared_caption_override():
    from utils.hmr_scene_iteration import apply_scene_locks_and_overrides

    scenes = [{"id": "hook", "template": "hook_footage_overlay", "duration": 2.0, "caption_text": "Original hook"}]
    updated, report = apply_scene_locks_and_overrides(
        scenes,
        scene_locks=[{"scene_id": "hook", "allowed_override_fields": ["caption"]}],
        scene_overrides=[{"scene_id": "hook", "fields": {"caption_text": "Tighter hook caption"}}],
    )

    assert updated[0]["caption_text"] == "Tighter hook caption"
    assert report["applied_overrides"][0]["fields"][0]["target"] == "caption_text"
    assert report["locked_scenes"][0]["applied_override_count"] == 1
    assert report["rejected_overrides"] == []


def test_unlocked_scene_accepts_asset_timing_and_script_overrides():
    from utils.hmr_scene_iteration import apply_scene_locks_and_overrides

    scenes = [{"id": "proof", "duration": 3.0, "narration_text": "Old", "asset_path": "old.png"}]
    updated, report = apply_scene_locks_and_overrides(
        scenes,
        scene_overrides=[
            {
                "scene_id": "proof",
                "fields": {
                    "script": "New narration",
                    "asset": "assets/proof/run/proof.png",
                    "timing": 4.25,
                },
            }
        ],
    )

    assert updated[0]["narration_text"] == "New narration"
    assert updated[0]["asset_path"] == "assets/proof/run/proof.png"
    assert updated[0]["duration"] == 4.25
    assert {row["target"] for row in report["applied_overrides"][0]["fields"]} == {"narration_text", "asset_path", "duration"}


def test_missing_override_target_is_reported():
    from utils.hmr_scene_iteration import apply_scene_locks_and_overrides

    _, report = apply_scene_locks_and_overrides(
        [{"id": "hook", "duration": 2.0}],
        scene_overrides=[{"scene_id": "missing", "fields": {"caption_text": "Nope"}}],
    )

    assert report["missing_override_targets"][0]["status"] == "target_scene_not_found"
