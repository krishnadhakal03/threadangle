from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from .render import regenerate_audio_captions_and_restitch, render_draft_video, render_locked_visuals
from .schema import ProviderStatus, VisualSource, load_storyboard, save_storyboard


REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE = REPO_ROOT / "backend" / "storyboard" / "examples" / "day6_walmart_storyboard.json"
OUT_DIR = REPO_ROOT / "backend" / "generated_videos" / "storyboard_review" / "storyboard_day6_smoke"
REPLACEMENT_ASSET = "launch_assets/day6_walmart_receipts/02_onepay_5percent_cashback.jpeg"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    storyboard = load_storyboard(FIXTURE)
    initial = render_draft_video(storyboard, REPO_ROOT, OUT_DIR)

    test_storyboard_path = OUT_DIR / "day6_replace_lock_test_storyboard.json"
    shutil.copyfile(FIXTURE, test_storyboard_path)
    replaced = load_storyboard(test_storyboard_path)
    for scene in replaced.scenes:
        if scene.scene_id == "replacement_math":
            scene.asset_path = REPLACEMENT_ASSET
            scene.visual_source = VisualSource.proof_screenshot
            scene.lock_visual = True
            scene.privacy_reviewed = True
            scene.provider_status = ProviderStatus.pending
            break
    save_storyboard(replaced, test_storyboard_path)

    locked_silent = render_locked_visuals(replaced, REPO_ROOT, OUT_DIR / "raw_locked_replace")
    before_hash = sha256(locked_silent)
    regen = regenerate_audio_captions_and_restitch(replaced, locked_silent, OUT_DIR)
    after_hash = sha256(locked_silent)

    proof = {
        "initial_render": initial,
        "replacement_storyboard": str(test_storyboard_path),
        "replacement_scene_id": "replacement_math",
        "replacement_asset": REPLACEMENT_ASSET,
        "lock_visual": True,
        "locked_silent_video": str(locked_silent),
        "locked_silent_sha256_before_audio_regen": before_hash,
        "locked_silent_sha256_after_audio_regen": after_hash,
        "locked_visual_survived_audio_regen": before_hash == after_hash,
        "audio_regen": regen,
    }
    proof_path = OUT_DIR / "smoke_proof.json"
    proof_path.write_text(json.dumps(proof, indent=2), encoding="utf-8")
    print(json.dumps(proof, indent=2))


if __name__ == "__main__":
    main()
