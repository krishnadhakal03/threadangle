from __future__ import annotations

import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def test_montage_plan_sequences_resolved_assets_with_transition_schema():
    from utils.hmr_editing_rhythm import build_quick_cut_schedule
    from utils.hmr_montage import MONTAGE_TRANSITIONS, build_montage_plan

    scene_timings = [
        {"scene_id": "hook", "start": 0.0, "end": 2.4},
        {"scene_id": "payoff", "start": 2.4, "end": 5.0},
    ]
    rhythm = build_quick_cut_schedule(
        script_text="I found $43 hiding in one bill. Save it before you pay.",
        scene_timings=scene_timings,
        caption_events=[
            {"start": 0.0, "end": 1.2, "text": "I found $43"},
            {"start": 1.2, "end": 2.4, "text": "hiding in one bill"},
            {"start": 2.4, "end": 3.5, "text": "Save it"},
            {"start": 3.5, "end": 5.0, "text": "before you pay"},
        ],
    )
    plan = build_montage_plan(
        scene_reports=[
            {
                "scene_id": "hook",
                "template": "hook_footage_overlay",
                "duration": 2.4,
                "resolved_asset_path": "assets/hook.mp4",
                "resolved_asset_paths": ["assets/hook_a.mp4", "assets/hook_b.mp4"],
                "asset_resolution_status": "resolved",
                "media_classification": "REAL_STOCK",
            },
            {
                "scene_id": "payoff",
                "template": "payoff_number_reveal",
                "duration": 2.6,
                "resolved_asset_path": "assets/payoff.mp4",
                "asset_resolution_status": "resolved",
            },
        ],
        scene_timings=scene_timings,
        editing_rhythm_plan=rhythm,
        audio_timeline={
            "events": [
                {"event_type": "voice_segment", "start": 0.0},
                {"event_type": "payoff_hit", "start": 0.0},
                {"event_type": "transition_hit", "start": 1.2},
            ]
        },
    )

    assert plan["profile"]["id"] == "smooth_high_energy_shorts"
    assert plan["transitions_supported"] == list(MONTAGE_TRANSITIONS)
    assert plan["debug"]["render_required"] is False
    assert plan["debug"]["uses_resolved_assets"] is True
    assert len(plan["clips"]) >= 4
    first = plan["clips"][0]
    assert {
        "clip_id",
        "path",
        "trim_start",
        "trim_end",
        "transition_in",
        "transition_out",
        "speed_factor",
        "beat_voice_alignment_marker",
        "motion_continuity_hint",
    }.issubset(first)
    assert first["transition_in"] == "hard_cut"
    assert first["beat_voice_alignment_marker"] == "payoff_hit"
    assert any(clip["transition_in"] in {"whip_cut", "zoom_blend", "match_motion_cut"} for clip in plan["clips"][1:])
    assert max(clip["trim_end"] - clip["trim_start"] for clip in plan["clips"]) <= 1.35


def test_montage_plan_falls_back_to_generated_template_asset():
    from utils.hmr_montage import build_montage_plan

    plan = build_montage_plan(
        scene_reports=[{"scene_id": "proof", "template": "ai_prompt_mock", "duration": 1.8}],
        scene_timings=[{"scene_id": "proof", "start": 0.0, "end": 1.8}],
    )

    assert plan["debug"]["uses_resolved_assets"] is False
    assert plan["clips"][0]["path"] == "generated_motion_template:ai_prompt_mock"
    assert plan["clips"][0]["source_status"] == "generated_template"
    assert plan["clips"][0]["transition_in"] == "hard_cut"


def test_attach_montage_plan_to_report_adds_scene_debug():
    from utils.hmr_montage import attach_montage_plan_to_report, build_montage_plan

    report = {"scene_reports": [{"scene_id": "hook", "duration": 1.2}]}
    plan = build_montage_plan(
        scene_reports=report["scene_reports"],
        scene_timings=[{"scene_id": "hook", "start": 0.0, "end": 1.2}],
    )
    updated = attach_montage_plan_to_report(report, plan)

    assert updated["montage_plan"]["profile"]["id"] == "smooth_high_energy_shorts"
    assert updated["scene_reports"][0]["montage_clip_count"] == 1
    assert updated["scene_reports"][0]["montage_clips"][0]["clip_id"] == "hook_01"
