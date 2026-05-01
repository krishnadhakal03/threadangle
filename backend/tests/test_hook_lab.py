from __future__ import annotations

import sys
from pathlib import Path

import pytest


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def test_hook_lab_generates_ranked_local_candidates_without_paid_providers():
    from utils.hook_lab import HOOK_SCORE_DIMENSIONS, build_hook_lab

    lab = build_hook_lab(
        topic="monthly grocery bill leaks",
        category="personal finance",
        candidate_count=8,
    )

    assert lab["candidate_count"] == 8
    assert lab["score_dimensions"] == list(HOOK_SCORE_DIMENSIONS)
    assert lab["paid_providers_used"] == {
        "elevenlabs": False,
        "runwayml": False,
        "paid_llm": False,
    }
    assert lab["selected_hook"]["rank"] == 1
    assert lab["selected_hook"]["selected"] is True
    scores = [candidate["total_score"] for candidate in lab["candidates"]]
    assert scores == sorted(scores, reverse=True)
    assert all(set(candidate["scores"]) == set(HOOK_SCORE_DIMENSIONS) for candidate in lab["candidates"])


def test_hook_lab_manual_candidate_selection_marks_winner():
    from utils.hook_lab import build_hook_lab

    lab = build_hook_lab(
        topic="AI receipt comparison",
        selected_hook_id="03_mistake_reversal",
    )

    assert lab["selected_hook"]["id"] == "03_mistake_reversal"
    assert lab["selected_hook"]["selected"] is True
    selected_rows = [candidate for candidate in lab["candidates"] if candidate["selected"]]
    assert [row["id"] for row in selected_rows] == ["03_mistake_reversal"]


def test_hook_lab_override_builds_manifest_friendly_metadata():
    from utils.hook_lab import build_hook_lab

    lab = build_hook_lab(
        topic="subscription audit",
        override_hook="I found $43 hiding in one subscription screen.",
    )

    selected = lab["selected_hook"]
    metadata = lab["manifest_metadata"]
    assert selected["id"] == "manual_override"
    assert selected["override"] is True
    assert metadata["selected_hook_text"] == "I found $43 hiding in one subscription screen."
    assert metadata["manual_override"] is True
    assert metadata["selected_hook_scores"] == selected["scores"]


def test_manifest_can_store_hook_lab_metadata(tmp_path):
    from utils.hmr_artifact_manifest import build_manifest
    from utils.hook_lab import build_hook_lab

    lab = build_hook_lab(topic="budget leaks", candidate_count=5)
    manifest = build_manifest(
        topic="budget leaks",
        hook=lab["selected_hook"]["text"],
        video_path=tmp_path / "video.mp4",
        review_package_path=tmp_path / "review_package",
        hook_lab=lab["manifest_metadata"],
    )

    assert manifest["hook"] == lab["selected_hook"]["text"]
    assert manifest["hook_lab"]["selected_hook_id"] == lab["selected_hook"]["id"]
    assert manifest["hook_lab"]["manual_override"] is False


def test_hook_lab_rejects_empty_topic():
    from utils.hook_lab import build_hook_lab

    with pytest.raises(ValueError, match="Topic cannot be empty"):
        build_hook_lab(topic="  ")
