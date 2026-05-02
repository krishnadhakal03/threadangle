from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


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


def _hook_endpoint_client() -> TestClient:
    from routes.free import router

    app = FastAPI()
    app.include_router(router, prefix="/api/free")
    return TestClient(app)


def test_generate_hooks_endpoint_preserves_legacy_and_rich_contract():
    client = _hook_endpoint_client()

    response = client.post(
        "/api/free/generate-hooks",
        json={
            "topic": "monthly grocery bill leaks",
            "category": "Finance",
            "candidate_count": 5,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["schema_version"] == 1
    assert payload["paid_providers_used"] == {
        "elevenlabs": False,
        "runwayml": False,
        "paid_llm": False,
    }

    hooks = payload["hooks"]
    candidates = payload["candidates"]
    assert len(hooks) == 5
    assert len(candidates) == 5
    assert [hook["text"] for hook in hooks] == [candidate["text"] for candidate in candidates]
    assert hooks[0] == {
        "type": candidates[0]["archetype"],
        "text": candidates[0]["text"],
        "why_it_works": candidates[0]["why_it_works"],
        "score": candidates[0]["total_score"],
        "rank": candidates[0]["rank"],
    }

    selected = payload["selected_hook"]
    metadata = payload["manifest_metadata"]
    assert selected["id"] == candidates[0]["id"]
    assert selected["selected"] is True
    assert metadata["selected_hook_id"] == selected["id"]
    assert metadata["selected_hook_text"] == selected["text"]
    assert metadata["selected_hook_scores"] == selected["scores"]


def test_generate_hooks_endpoint_accepts_selection_and_manual_override():
    client = _hook_endpoint_client()

    selected_response = client.post(
        "/api/free/generate-hooks",
        json={
            "topic": "subscription audit",
            "category": "Finance",
            "selected_hook_id": "03_mistake_reversal",
        },
    )
    assert selected_response.status_code == 200
    selected_payload = selected_response.json()
    assert selected_payload["selected_hook"]["id"] == "03_mistake_reversal"
    assert selected_payload["selected_hook"]["selected"] is True
    assert selected_payload["manifest_metadata"]["manual_override"] is False

    override_response = client.post(
        "/api/free/generate-hooks",
        json={
            "topic": "subscription audit",
            "category": "Finance",
            "override_hook": "I found $43 hiding in one subscription screen.",
        },
    )
    assert override_response.status_code == 200
    override_payload = override_response.json()
    assert len(override_payload["hooks"]) == override_payload["candidate_count"]
    assert override_payload["selected_hook"]["id"] == "manual_override"
    assert override_payload["selected_hook"]["override"] is True
    assert override_payload["manifest_metadata"]["manual_override"] is True
    assert (
        override_payload["manifest_metadata"]["selected_hook_text"]
        == "I found $43 hiding in one subscription screen."
    )
