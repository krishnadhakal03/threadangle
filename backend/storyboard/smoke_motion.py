"""
Motion Smoke Tests

Render Day6 storyboard with different motion profiles for comparison.
"""

import json
import shutil
from pathlib import Path

from .render import render_draft_video
from .schema import MotionProfile, load_storyboard, save_storyboard


REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE = REPO_ROOT / "backend" / "storyboard" / "examples" / "day6_walmart_storyboard.json"
OUT_DIR = REPO_ROOT / "backend" / "generated_videos" / "storyboard_review" / "motion_smoke"


def render_with_profile(storyboard_path: Path, profile: MotionProfile, out_subdir: str) -> dict:
    """Render storyboard with given motion profile."""
    storyboard = load_storyboard(storyboard_path)
    for scene in storyboard.scenes:
        scene.motion_profile = profile
    temp_path = OUT_DIR / f"temp_{profile.value}.json"
    save_storyboard(storyboard, temp_path)
    result = render_draft_video(storyboard, REPO_ROOT, OUT_DIR / out_subdir)
    return result


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Base render (static_clean)
    base_result = render_with_profile(FIXTURE, MotionProfile.static_clean, "base_static")

    # Documentary dynamic render
    dynamic_result = render_with_profile(FIXTURE, MotionProfile.documentary_dynamic, "documentary_dynamic")

    # For tutorial, create a dummy wide storyboard
    # For simplicity, use the day6 but change format to wide
    tutorial_storyboard = load_storyboard(FIXTURE)
    tutorial_storyboard.format = "wide_16x9"
    tutorial_storyboard.title = "Tutorial Motion Smoke"
    for scene in tutorial_storyboard.scenes:
        scene.motion_profile = MotionProfile.tutorial_followcam
    tutorial_path = OUT_DIR / "tutorial_fixture.json"
    save_storyboard(tutorial_storyboard, tutorial_path)
    tutorial_result = render_draft_video(tutorial_storyboard, REPO_ROOT, OUT_DIR / "tutorial_followcam")

    proof = {
        "base_static_render": base_result,
        "documentary_dynamic_render": dynamic_result,
        "tutorial_followcam_render": tutorial_result,
        "contact_sheets": [
            base_result.get("contact_sheet"),
            dynamic_result.get("contact_sheet"),
            tutorial_result.get("contact_sheet")
        ]
    }
    proof_path = OUT_DIR / "motion_smoke_proof.json"
    proof_path.write_text(json.dumps(proof, indent=2), encoding="utf-8")
    print(json.dumps(proof, indent=2))


if __name__ == "__main__":
    main()