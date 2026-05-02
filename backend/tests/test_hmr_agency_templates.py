from __future__ import annotations

import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def test_agency_template_library_contains_initial_templates():
    from utils.hmr_agency_templates import list_agency_templates

    templates = {template["template_id"]: template for template in list_agency_templates()}

    assert set(templates) == {
        "bill_leak_expose",
        "receipt_shock",
        "checked_this_so_you_dont",
        "three_mistakes_costing_money",
        "before_after_savings",
        "hidden_fee_reveal",
        "one_setting_saved_me",
        "stop_paying_for_this",
    }
    receipt = templates["receipt_shock"]
    assert receipt["hook_type"] == "receipt_number_shock"
    assert "scene_roles" in receipt
    assert "proof_requirement" in receipt
    assert "sound_design_profile" in receipt
    assert receipt["expected_cta_style"]


def test_template_selection_uses_topic_domain_and_keywords():
    from utils.hmr_agency_templates import select_agency_template

    selected = select_agency_template("I found a hidden fee in my monthly bill statement")

    assert selected["selected_template_id"] in {"bill_leak_expose", "hidden_fee_reveal"}
    assert selected["domain"] == "bill_leak"
    assert any(row["template_id"] == selected["selected_template_id"] and row["score"] > 0 for row in selected["compatibility"])


def test_template_lookup_and_compatibility_metadata():
    from utils.hmr_agency_templates import get_agency_template, select_agency_template

    template = get_agency_template("before_after_savings")
    selected = select_agency_template("before and after savings from replacing daily coffee", domain="coffee_savings")

    assert template["pacing_profile"] == "split_screen_delta"
    assert selected["selected_template_id"] == "before_after_savings"
    assert selected["selected_template"]["pattern_interrupt_profile"] == "split_screen_before_after_payoff_meter"


def test_scene_based_selection_reads_scene_text():
    from utils.hmr_agency_templates import select_agency_template_for_scenes

    selected = select_agency_template_for_scenes(
        [
            {"id": "hook", "caption_text": "This grocery receipt had a checkout shock."},
            {"id": "payoff", "caption_text": "The swap saved $480/year."},
        ]
    )

    assert selected["selected_template_id"] == "receipt_shock"
    assert selected["selected_template"]["proof_requirement"] == "receipt_or_checkout_screenshot"
