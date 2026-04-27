"""
Retention Smoke Tests

Render Day6 storyboard with and without retention editing.
"""

import json
import shutil
from pathlib import Path

from .render import render_draft_video
from .schema import BeatRole, load_storyboard, save_storyboard


REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE = REPO_ROOT / "backend" / "storyboard" / "examples" / "day6_walmart_storyboard.json"
OUT_DIR = REPO_ROOT / "backend" / "generated_videos" / "storyboard_review" / "retention_smoke"


def render_with_retention(storyboard_path: Path, apply_retention: bool, out_subdir: str) -> dict:
    """Render storyboard with or without retention editing."""
    storyboard = load_storyboard(storyboard_path)
    if apply_retention:
        # Apply retention metadata
        for i, scene in enumerate(storyboard.scenes):
            if i == 0:
                scene.beat_role = BeatRole.hook
            elif i == len(storyboard.scenes) - 1:
                scene.beat_role = BeatRole.cta
            elif "proof" in scene.narration_text.lower():
                scene.beat_role = BeatRole.proof
            else:
                scene.beat_role = BeatRole.setup
            scene.novelty_interval_seconds = 1.2
            scene.emphasis_terms = ["save", "proof", "money"]
    temp_path = OUT_DIR / f"temp_{'retention' if apply_retention else 'normal'}.json"
    save_storyboard(storyboard, temp_path)
    result = render_draft_video(storyboard, REPO_ROOT, OUT_DIR / out_subdir)
    return result


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Normal render
    normal_result = render_with_retention(FIXTURE, False, "normal")

    # Retention edit render
    retention_result = render_with_retention(FIXTURE, True, "retention_edit")

    # Create widescreen tutorial fixture
    tutorial_storyboard = load_storyboard(FIXTURE)
    tutorial_storyboard.format = "wide_16x9"
    tutorial_storyboard.title = "Tutorial Retention Smoke"
    for scene in tutorial_storyboard.scenes:
        scene.beat_role = BeatRole.tension
        scene.micro_beats = ["punch_in", "focus_crop"]
    tutorial_path = OUT_DIR / "tutorial_fixture.json"
    save_storyboard(tutorial_storyboard, tutorial_path)
    tutorial_result = render_draft_video(tutorial_storyboard, REPO_ROOT, OUT_DIR / "tutorial_wide")

    proof = {
        "normal_render": normal_result,
        "retention_edit_render": retention_result,
        "tutorial_wide_render": tutorial_result,
        "contact_sheets": [
            normal_result.get("contact_sheet"),
            retention_result.get("contact_sheet"),
            tutorial_result.get("contact_sheet")
        ]
    }
    proof_path = OUT_DIR / "retention_smoke_proof.json"
    proof_path.write_text(json.dumps(proof, indent=2), encoding="utf-8")
    print(json.dumps(proof, indent=2))


if __name__ == "__main__":
    main()