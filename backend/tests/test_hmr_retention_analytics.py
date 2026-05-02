from __future__ import annotations

import sys
from pathlib import Path

import pytest


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def _record(**overrides):
    base = {
        "platform": "tiktok",
        "post_url_or_id": "https://tiktok.example/post/1",
        "topic_domain": "bill_leak",
        "hook_used": "I found a hidden fee",
        "agency_template": "bill_leak_expose",
        "first_frame_style": "bill closeup",
        "video_duration_sec": 24,
        "three_second_hold": 0.42,
        "average_view_duration_sec": 8.5,
        "completion_rate": 0.31,
        "rewatch_rate": 0.05,
        "saves": 3,
        "shares": 2,
        "comments": 1,
        "follows_gained": 0,
        "posted_at": "2026-05-01T18:00:00-04:00",
        "notes": "First read window",
        "manifest_path": "backend/generated_videos/storyboard_review/run/review_package",
        "issue_number": 31,
    }
    base.update(overrides)
    return base


def test_analytics_record_validation_normalizes_schema():
    from utils.hmr_retention_analytics import validate_analytics_record

    record = validate_analytics_record(_record(platform="YouTube_Shorts", saves="4"))

    assert record["schema_version"] == 1
    assert record["platform"] == "youtube_shorts"
    assert record["saves"] == 4
    assert record["completion_rate"] == 0.31
    assert record["issue_number"] == 31


def test_append_and_read_analytics_records(tmp_path):
    from utils.hmr_retention_analytics import append_analytics_record, read_analytics_records

    path = tmp_path / "analytics.jsonl"
    append_analytics_record(_record(post_url_or_id="one"), path)
    append_analytics_record(_record(post_url_or_id="two", platform="instagram_reels"), path)

    records = read_analytics_records(path)

    assert [record["post_url_or_id"] for record in records] == ["one", "two"]
    assert records[1]["platform"] == "instagram_reels"


def test_invalid_analytics_record_is_rejected():
    from utils.hmr_retention_analytics import validate_analytics_record

    with pytest.raises(ValueError, match="Missing required"):
        validate_analytics_record({"platform": "tiktok"})
    with pytest.raises(ValueError, match="Unsupported platform"):
        validate_analytics_record(_record(platform="vine"))


def test_summary_prefers_stronger_hook_and_template():
    from utils.hmr_retention_analytics import summarize_next_video_decisions

    records = [
        _record(hook_used="weak hook", completion_rate=0.12, three_second_hold=0.2),
        _record(hook_used="strong hook", agency_template="receipt_shock", completion_rate=0.55, three_second_hold=0.6),
    ]
    summary = summarize_next_video_decisions(records)

    assert summary["record_count"] == 2
    assert summary["best_hook"]["hook_used"] == "strong hook"
    assert summary["best_template"]["agency_template"] == "receipt_shock"
    assert any("first-frame proof" in note for note in summary["notes"])


def test_manifest_linking_uses_manifest_path():
    from utils.hmr_retention_analytics import link_analytics_to_manifest

    manifest = {"review_package_path": "backend/generated_videos/storyboard_review/run/review_package"}
    linked = link_analytics_to_manifest(manifest, [_record(), _record(manifest_path="other")])

    assert linked["retention_analytics"]["linked_record_count"] == 1
    assert linked["retention_analytics"]["platforms"] == ["tiktok"]
