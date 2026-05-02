from __future__ import annotations

import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def test_proof_asset_plan_resolves_scene_replacement(tmp_path):
    from utils.hmr_proof_assets import build_proof_asset_plan, proof_asset_for_scene, proof_asset_resolution_fields

    proof = tmp_path / "assets" / "proof" / "bill_leak" / "statement.png"
    proof.parent.mkdir(parents=True)
    proof.write_bytes(b"fake png")
    scenes = [{"id": "proof", "template": "ai_prompt_mock", "duration": 2.0}]
    plan = build_proof_asset_plan(
        scenes,
        [
            {
                "scene_id": "proof",
                "asset_path": "bill_leak/statement.png",
                "asset_type": "screenshot",
                "crop_fit": "contain",
                "lock_behavior": "lock",
            }
        ],
        asset_root=tmp_path / "assets" / "proof",
    )

    row = proof_asset_for_scene(plan, "proof")
    fields = proof_asset_resolution_fields(row)

    assert plan["convention"] == "assets/proof/<topic_or_run>/"
    assert row["status"] == "resolved"
    assert row["proof_asset"]["resolved_path"] == str(proof.resolve())
    assert row["proof_asset"]["crop_fit"] == "contain"
    assert row["proof_asset"]["locks_replacement"] is True
    assert fields["resolved_asset_provider"] == "user_proof_asset"
    assert fields["resolved_asset_type"] == "stock_image"
    assert fields["fallback_used"] is False


def test_missing_proof_asset_is_truthful_and_keeps_fallback(tmp_path):
    from utils.hmr_proof_assets import build_proof_asset_plan, proof_asset_for_scene

    scenes = [{"id": "hook", "template": "hook_footage_overlay", "duration": 2.0}]
    plan = build_proof_asset_plan(
        scenes,
        [{"scene_id": "hook", "asset_path": "grocery/missing.png", "asset_type": "image"}],
        asset_root=tmp_path / "assets" / "proof",
    )

    assert plan["missing_assets"][0]["scene_id"] == "hook"
    assert plan["missing_assets"][0]["proof_asset"]["candidate_path"].endswith("assets/proof/grocery/missing.png")
    assert proof_asset_for_scene(plan, "hook") is None
    assert plan["fallback_behavior"] == "missing proof assets are reported and existing scene fallback continues"


def test_embedded_scene_proof_asset_path_is_supported(tmp_path):
    from utils.hmr_proof_assets import build_proof_asset_plan

    proof = tmp_path / "assets" / "proof" / "run42" / "receipt.mp4"
    proof.parent.mkdir(parents=True)
    proof.write_bytes(b"fake mp4")
    scenes = [
        {
            "id": "reveal",
            "duration": 2.0,
            "proof_asset_path": "run42/receipt.mp4",
            "proof_asset_type": "video",
            "proof_asset_crop_fit": "cover",
        }
    ]

    plan = build_proof_asset_plan(scenes, asset_root=tmp_path / "assets" / "proof")
    proof_asset = plan["resolved_assets"][0]["proof_asset"]

    assert proof_asset["asset_type"] == "video"
    assert proof_asset["renderer_asset_type"] == "stock_footage"
    assert proof_asset["replaces_scene_visual"] is True


def test_role_target_reports_unmatched_targets(tmp_path):
    from utils.hmr_proof_assets import build_proof_asset_plan

    plan = build_proof_asset_plan(
        [{"id": "hook", "scene_type": "hook", "duration": 2.0}],
        [{"scene_role": "payoff", "asset_path": "run/payoff.png"}],
        asset_root=tmp_path / "assets" / "proof",
    )

    assert plan["scene_assets"][0]["status"] == "not_targeted"
    assert plan["unresolved_targets"][0]["status"] == "target_scene_not_found"
