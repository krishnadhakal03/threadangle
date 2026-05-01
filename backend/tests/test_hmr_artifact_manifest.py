import json

import pytest

from utils.hmr_artifact_manifest import (
    FrozenArtifactError,
    assert_not_frozen_output,
    build_manifest,
    write_manifest,
)


def test_frozen_manifest_blocks_overwrite(tmp_path):
    package = tmp_path / "review_package"
    manifest = build_manifest(
        topic="Grocery receipt",
        hook="I found a $40/week leak.",
        video_path=package / "grocery.mp4",
        review_package_path=package,
        human_posting_gate="READY_FOR_HUMAN_POST_REVIEW",
        frozen=True,
    )
    write_manifest(package, manifest)

    with pytest.raises(FrozenArtifactError) as exc:
        assert_not_frozen_output(package / "render_report.json")

    assert "READY_FOR_HUMAN_POST_REVIEW" in str(exc.value)


def test_non_frozen_output_is_allowed(tmp_path):
    package = tmp_path / "review_package"
    manifest = build_manifest(
        topic="Draft",
        hook="Draft hook",
        video_path=package / "draft.mp4",
        review_package_path=package,
        human_posting_gate="DRAFT",
        frozen=False,
    )
    write_manifest(package, manifest)

    assert_not_frozen_output(package)
    assert_not_frozen_output(tmp_path)


def test_missing_manifest_does_not_block_generation(tmp_path):
    assert_not_frozen_output(tmp_path / "new_output" / "review_package")


def test_force_true_is_explicit_escape_hatch(tmp_path):
    package = tmp_path / "review_package"
    manifest = build_manifest(
        topic="Frozen",
        hook="Frozen hook",
        video_path=package / "frozen.mp4",
        review_package_path=package,
        human_posting_gate="READY_FOR_HUMAN_POST_REVIEW",
        frozen=True,
    )
    write_manifest(package, manifest)

    assert_not_frozen_output(package, force=True)
    updated = dict(manifest)
    updated["posted_platforms"] = ["youtube_shorts"]
    path = write_manifest(package, updated, force=True)

    assert json.loads(path.read_text(encoding="utf-8"))["posted_platforms"] == ["youtube_shorts"]


def test_manifest_schema_includes_production_safety_fields(tmp_path):
    manifest = build_manifest(
        topic="Bill leak",
        hook="I found a $27/month leak.",
        video_path=tmp_path / "bill.mp4",
        review_package_path=tmp_path,
        render_report={
            "media_mix": {"REAL_STOCK": 2},
            "scene_reports": [
                {
                    "scene_id": "hook",
                    "resolved_asset_type": "stock_footage",
                    "resolved_asset_provider": "pexels",
                    "resolved_asset_path": "hook.mp4",
                }
            ],
        },
        qa_report={
            "technical_status": "PASS",
            "postability_status": "STRONG_PASS",
            "postability_score": {"average_score": 8.4},
        },
        frozen=False,
    )

    assert manifest["schema_version"] == 1
    assert manifest["technical_status"] == "PASS"
    assert manifest["postability_status"] == "STRONG_PASS"
    assert manifest["average_score"] == 8.4
    assert manifest["media_mix"] == {"REAL_STOCK": 2}
    assert manifest["resolved_real_assets"][0]["provider"] == "pexels"
    assert manifest["paid_providers_used"] == {
        "elevenlabs": False,
        "runwayml": False,
        "paid_llm": False,
    }
    assert manifest["frozen"] is False
    assert manifest["posted_platforms"] == []
    assert set(manifest["analytics_placeholders"]) == {
        "youtube_shorts",
        "tiktok",
        "instagram_reels",
        "facebook_reels",
    }
