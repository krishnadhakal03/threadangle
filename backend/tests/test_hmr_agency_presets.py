from __future__ import annotations

import sys
from pathlib import Path

import pytest


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def test_agency_preset_pack_contains_candidate_presets():
    from utils.hmr_agency_presets import list_agency_presets

    presets = {preset["preset_id"]: preset for preset in list_agency_presets()}

    assert set(presets) == {
        "money_saving_agency",
        "bill_leak_expose",
        "receipt_shock",
        "proof_first_short",
        "fast_listicle_warning",
    }
    bill = presets["bill_leak_expose"]
    assert bill["hook_lab_profile"] == "hidden_fee_shock"
    assert bill["agency_template_default"] == "bill_leak_expose"
    assert bill["sfx_profile"]
    assert bill["caption_style_hints"]["emphasize_numbers"] is True
    assert bill["export_preset_recommendation"] == "instagram_reels"


def test_agency_preset_selection_uses_domain_keywords_and_template():
    from utils.hmr_agency_presets import select_agency_preset

    selected = select_agency_preset(
        "I found a hidden charge in my monthly bill",
        domain="bill_leak",
        agency_template_id="bill_leak_expose",
    )

    assert selected["selected_preset_id"] == "bill_leak_expose"
    assert selected["selected_preset"]["proof_asset_requirement_level"] == "required"
    assert any(row["preset_id"] == "bill_leak_expose" and row["score"] > 0 for row in selected["compatibility"])


def test_explicit_preset_selection_and_unknown_guard():
    from utils.hmr_agency_presets import select_agency_preset

    selected = select_agency_preset("any topic", preset_id="proof_first_short")

    assert selected["selected_preset_id"] == "proof_first_short"
    assert selected["selection_reason"] == "explicit preset requested"
    with pytest.raises(ValueError, match="Unknown agency preset"):
        select_agency_preset("any topic", preset_id="missing")


def test_scene_based_preset_selection_reads_scene_text_and_template():
    from utils.hmr_agency_presets import select_agency_preset_for_scenes

    selected = select_agency_preset_for_scenes(
        [{"id": "hook", "caption_text": "This receipt total shocked me at grocery checkout."}],
        agency_template={"selected_template_id": "receipt_shock"},
    )

    assert selected["selected_preset_id"] == "receipt_shock"
    assert selected["selected_preset"]["first_3_sec_profile"] == "receipt_closeup_plus_total"


def test_manifest_can_carry_agency_preset_metadata(tmp_path):
    from utils.hmr_artifact_manifest import build_manifest
    from utils.hmr_agency_presets import select_agency_preset

    preset = select_agency_preset("receipt shock grocery total", domain="grocery_savings")
    manifest = build_manifest(
        topic="Grocery receipt",
        hook="This receipt total shocked me.",
        video_path=tmp_path / "video.mp4",
        review_package_path=tmp_path,
        render_report={"agency_preset": preset},
    )

    assert manifest["agency_preset"]["selected_preset_id"] == "receipt_shock"
