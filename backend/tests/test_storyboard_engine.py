from __future__ import annotations

from pathlib import Path

import pytest

from storyboard.provider_router import route_scene_provider
from storyboard.qa import run_qa
from storyboard.render_modes import assert_provider_allowed
from storyboard.schema import Storyboard, StoryboardScene, VideoFormat, VisualSource, load_storyboard


REPO_ROOT = Path(__file__).resolve().parents[2]
DAY6_FIXTURE = REPO_ROOT / "backend" / "storyboard" / "examples" / "day6_walmart_storyboard.json"


def test_day6_storyboard_fixture_loads():
    storyboard = load_storyboard(DAY6_FIXTURE)
    assert storyboard.project_id == "storyboard_day6_smoke"
    assert storyboard.format == VideoFormat.short_9x16
    assert len(storyboard.scenes) == 6
    assert storyboard.scenes[0].lock_visual is True


def test_draft_mode_blocks_paid_providers():
    storyboard = load_storyboard(DAY6_FIXTURE)
    with pytest.raises(RuntimeError, match="Draft mode blocks paid provider"):
        assert_provider_allowed(storyboard, "elevenlabs", "test narration")
    with pytest.raises(RuntimeError, match="Draft mode blocks paid provider"):
        assert_provider_allowed(storyboard, "runwayml", "test visual")


def test_provider_router_reports_fallback_usage(tmp_path):
    fallback = tmp_path / "fallback.png"
    fallback.write_bytes(b"not-a-real-image-but-existing")
    scene = StoryboardScene(
        scene_id="fallback",
        scene_type="proof",
        duration=2,
        narration_text="Fallback test",
        visual_source=VisualSource.proof_screenshot,
        asset_path=str(tmp_path / "missing.png"),
        fallback_asset_path=str(fallback),
    )
    decision = route_scene_provider(scene, REPO_ROOT)
    assert decision.status == "fallback_used"
    assert decision.asset_path == fallback


def test_qa_flags_locked_missing_asset(tmp_path):
    storyboard = Storyboard(
        project_id="qa_missing",
        title="QA missing",
        niche="test",
        template_id="test",
        scenes=[
            StoryboardScene(
                scene_id="hook",
                scene_type="hook",
                duration=2,
                narration_text="Hook",
                visual_source=VisualSource.proof_screenshot,
                asset_path=str(tmp_path / "missing.png"),
                lock_visual=True,
                privacy_reviewed=True,
            )
        ],
    )
    report = run_qa(storyboard, REPO_ROOT, tmp_path / "qa_report.json")
    codes = {issue["code"] for issue in report["issues"]}
    assert "locked_asset_missing" in codes
    assert "missing_visual" in codes
