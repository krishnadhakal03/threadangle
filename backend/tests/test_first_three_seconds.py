from __future__ import annotations

import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def test_first_3_seconds_plan_extracts_opening_attributes():
    from utils.first_three_seconds import build_first_3_seconds_plan

    plan = build_first_3_seconds_plan(
        selected_hook="I found $43 hiding in one subscription screen.",
        topic="subscription audit",
    )

    assert plan["first_frame_style"] == "claim_proof_payoff"
    assert plan["big_claim_text"] == "I found $43 hiding in one subscription screen."
    assert plan["proof_object"] == "bill or subscription screen"
    assert plan["number_payoff_preview"] == "$43"
    assert plan["urgency_warning_label"] == "HIDDEN LEAK"
    assert plan["no_slow_intro"] is True
    assert plan["caption_text_preserved"] == "I found $43 hiding in one subscription screen."


def test_first_3_seconds_plan_interrupts_before_second_two():
    from utils.first_three_seconds import build_first_3_seconds_plan

    plan = build_first_3_seconds_plan(
        selected_hook="Stop fixing your grocery budget until you check this first.",
        topic="grocery bill",
    )

    interrupt = plan["pattern_interrupt"]
    assert interrupt["time_seconds"] < 2.0
    assert interrupt["before_second"] == 2.0
    assert plan["urgency_warning_label"] == "CHECK THIS FIRST"
    assert plan["proof_object"] == "receipt or grocery total"
    assert "slow_intro" in plan["render_notes"]["avoid"]


def test_first_3_seconds_report_fields_attach_without_rendering():
    from utils.first_three_seconds import attach_first_3_seconds_to_report, build_first_3_seconds_plan

    plan = build_first_3_seconds_plan(selected_hook="Give me 10 seconds and I will show the payoff.")
    report = attach_first_3_seconds_to_report({"video_path": "demo.mp4"}, plan)

    assert report["video_path"] == "demo.mp4"
    assert report["first_frame_style"] == "claim_proof_payoff"
    assert report["first_3_sec_strategy"]["no_slow_intro"] is True
    assert report["human_review"]["first_frame_style"] == "claim_proof_payoff"
    assert report["human_review"]["first_three_seconds_strategy"]["pattern_interrupt"]["time_seconds"] == 1.2


def test_manifest_can_store_first_3_seconds_strategy(tmp_path):
    from utils.first_three_seconds import build_first_3_seconds_plan, first_3_seconds_report_fields
    from utils.hmr_artifact_manifest import build_manifest

    plan = build_first_3_seconds_plan(selected_hook="Before you pay that bill, compare this number.")
    fields = first_3_seconds_report_fields(plan)
    manifest = build_manifest(
        topic="bill comparison",
        hook=plan["hook_text"],
        video_path=tmp_path / "video.mp4",
        review_package_path=tmp_path / "review_package",
        first_3_seconds=fields["first_3_sec_strategy"],
    )

    assert manifest["first_3_seconds"]["big_claim_text"] == "Before you pay that bill, compare this number."
    assert manifest["first_3_seconds"]["pattern_interrupt"]["time_seconds"] < 2
