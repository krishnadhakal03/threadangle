"""
Close the Gaps Smoke Tests

Demonstrate P0-P3 features with Day6 fixture.
"""

import json
from pathlib import Path

from .hook_lab import generate_hook_variants
from .render import render_draft_video
from .routes.storyboard import _path as get_storyboard_path
from .schema import load_storyboard, save_storyboard


REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_ID = "day6_walmart"
OUT_DIR = REPO_ROOT / "backend" / "generated_videos" / "storyboard_review" / "close_gaps_smoke"


def smoke_test():
    """Run smoke tests for close the gaps features."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Review manifest (P0)
    from .routes.storyboard import review
    review_result = review(FIXTURE_ID)
    print("Review manifest generated")

    # 2. Manual upload mode (P1) - simulate
    path = get_storyboard_path(FIXTURE_ID)
    storyboard = load_storyboard(path)
    # Simulate replacing a scene
    for scene in storyboard.scenes:
        if scene.scene_id == "before_cost":
            scene.visual_source = "user_manual_capture"
            scene.asset_path = "simulated_manual_capture.mp4"
            scene.capture_notes = "Smoke test manual capture"
            break
    temp_path = OUT_DIR / "temp_manual_capture.json"
    save_storyboard(storyboard, temp_path)
    print("Manual capture mode simulated")

    # 3. Sound accents (P2) - enable on storyboard
    for scene in storyboard.scenes:
        scene.sound_accent_profile = "enabled"
    temp_path2 = OUT_DIR / "temp_sound_accents.json"
    save_storyboard(storyboard, temp_path2)
    result = render_draft_video(storyboard, REPO_ROOT, OUT_DIR / "sound_accents_render")
    print("Sound accents render completed")

    # 4. Hook variants (P3)
    hook_variants = generate_hook_variants(storyboard)
    hook_path = OUT_DIR / "hook_variants.json"
    hook_path.write_text(json.dumps(hook_variants, indent=2), encoding="utf-8")
    print("Hook variants generated")

    # Summary
    summary = {
        "review_manifest": review_result,
        "manual_capture_simulated": str(temp_path),
        "sound_accents_render": result,
        "hook_variants": str(hook_path)
    }
    summary_path = OUT_DIR / "close_gaps_smoke_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Smoke tests completed. Summary: {summary_path}")


if __name__ == "__main__":
    smoke_test()