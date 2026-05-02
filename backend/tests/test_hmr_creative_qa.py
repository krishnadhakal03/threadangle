from __future__ import annotations

import sys
from pathlib import Path

import pytest


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def _scorecard(**overrides):
    base = {
        "hook_strength": 8,
        "first_frame_strength": 8,
        "proof_credibility": 7,
        "pacing": 7,
        "visual_novelty": 7,
        "caption_readability": 8,
        "sound_feel": 7,
        "platform_fit": 8,
        "post_worthiness": 8,
    }
    base.update(overrides)
    return base


def test_creative_qa_record_derives_pass_status():
    from utils.hmr_creative_qa import STATUS_PASS, build_creative_qa_record

    record = build_creative_qa_record(
        review_id="run-1",
        reviewer="Krishna",
        scorecard=_scorecard(),
        improvement_notes="Strong enough to post.",
    )

    assert record["creative_status"] == STATUS_PASS
    assert record["average_creative_score"] >= 7
    assert record["separate_from"] == ["technical_status", "postability_status", "human_posting_gate"]


def test_creative_qa_accepts_numeric_string_scores():
    from utils.hmr_creative_qa import STATUS_PASS, build_creative_qa_record, derive_creative_status

    string_scorecard = {field: str(value) for field, value in _scorecard(post_worthiness=7).items()}
    record = build_creative_qa_record(
        review_id="run-string-scores",
        reviewer="Krishna",
        scorecard=string_scorecard,
    )

    assert derive_creative_status(string_scorecard) == STATUS_PASS
    assert record["creative_status"] == STATUS_PASS
    assert all(isinstance(value, int) for value in record["scorecard"].values())
    assert record["scorecard"]["post_worthiness"] == 7


def test_creative_qa_record_blocks_low_post_worthiness():
    from utils.hmr_creative_qa import STATUS_BLOCKED, build_creative_qa_record

    record = build_creative_qa_record(
        review_id="run-2",
        reviewer="Krishna",
        scorecard=_scorecard(post_worthiness=4),
    )

    assert record["creative_status"] == STATUS_BLOCKED


def test_creative_qa_validation_rejects_missing_or_out_of_range_scores():
    from utils.hmr_creative_qa import build_creative_qa_record

    with pytest.raises(ValueError, match="Missing creative QA"):
        build_creative_qa_record(review_id="x", reviewer="Krishna", scorecard={"hook_strength": 8})
    with pytest.raises(ValueError, match="1 to 10"):
        build_creative_qa_record(review_id="x", reviewer="Krishna", scorecard=_scorecard(sound_feel=11))


def test_creative_qa_read_write_update(tmp_path):
    from utils.hmr_creative_qa import STATUS_REVIEW, build_creative_qa_record, read_creative_qa_record, update_creative_qa_record, write_creative_qa_record

    record = build_creative_qa_record(review_id="run 3", reviewer="Krishna", scorecard=_scorecard())
    path = write_creative_qa_record(record, tmp_path)
    loaded = read_creative_qa_record("run 3", tmp_path)
    updated = update_creative_qa_record("run 3", {"scorecard": {"visual_novelty": 4}, "improvement_notes": "Needs fresher visuals."}, tmp_path)

    assert path.name == "run_3.json"
    assert loaded["review_id"] == "run 3"
    assert updated["creative_status"] == STATUS_REVIEW
    assert updated["improvement_notes"] == "Needs fresher visuals."


def test_manifest_can_carry_creative_qa_without_changing_technical_status(tmp_path):
    from utils.hmr_artifact_manifest import build_manifest
    from utils.hmr_creative_qa import build_creative_qa_record

    creative = build_creative_qa_record(review_id="run-4", reviewer="Krishna", scorecard=_scorecard(post_worthiness=4))
    manifest = build_manifest(
        topic="Bill leak",
        hook="I found a hidden fee.",
        video_path=tmp_path / "video.mp4",
        review_package_path=tmp_path,
        qa_report={"technical_status": "PASS", "postability_status": "STRONG_PASS"},
        creative_qa=creative,
    )

    assert manifest["technical_status"] == "PASS"
    assert manifest["postability_status"] == "STRONG_PASS"
    assert manifest["creative_qa"]["creative_status"] == "CREATIVE_BLOCKED"
