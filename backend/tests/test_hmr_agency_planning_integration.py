from __future__ import annotations

import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def test_hmr_report_carries_all_agency_planning_layers_without_render():
    from utils.hmr_audio_timeline import attach_audio_timeline_to_report, build_audio_binding_timeline
    from utils.hmr_caption_style import attach_caption_style_to_report, build_caption_style_plan
    from utils.hmr_editing_rhythm import attach_quick_cut_schedule_to_report, build_quick_cut_schedule
    from utils.hmr_montage import attach_montage_plan_to_report, build_montage_plan

    script = "I found $43 hiding in one bill. Compare it before you pay."
    scene_timings = [
        {"scene_id": "hook", "start": 0.0, "end": 2.2, "duration": 2.2},
        {"scene_id": "payoff", "start": 2.2, "end": 4.8, "duration": 2.6},
    ]
    caption_events = [
        {"start": 0.0, "end": 1.1, "text": "I found $43"},
        {"start": 1.1, "end": 2.2, "text": "hiding in one bill"},
        {"start": 2.2, "end": 3.4, "text": "Compare it"},
        {"start": 3.4, "end": 4.8, "text": "before you pay"},
    ]
    report = {
        "scene_reports": [
            {
                "scene_id": "hook",
                "template": "hook_footage_overlay",
                "duration": 2.2,
                "resolved_asset_path": "assets/hook.mp4",
                "asset_resolution_status": "resolved",
            },
            {
                "scene_id": "payoff",
                "template": "payoff_number_reveal",
                "duration": 2.6,
                "resolved_asset_path": "assets/payoff.mp4",
                "asset_resolution_status": "resolved",
                "number_reveal": True,
            },
        ],
        "caption_report": {"event_count": len(caption_events), "violations": []},
    }
    sfx_plan = {
        "cues": [
            {
                "scene_id": "hook",
                "role": "warning_beep",
                "timeline_time": 1.2,
                "volume": 0.14,
                "status": "missing",
                "reason": "warning_language",
            }
        ],
        "render_required": False,
    }

    editing = build_quick_cut_schedule(
        script_text=script,
        scene_timings=scene_timings,
        caption_events=caption_events,
    )
    audio = build_audio_binding_timeline(
        script_text=script,
        scene_timings=scene_timings,
        caption_events=caption_events,
        sfx_plan=sfx_plan,
        editing_rhythm_plan=editing,
    )
    caption_style = build_caption_style_plan(caption_events=caption_events)
    montage = build_montage_plan(
        scene_reports=report["scene_reports"],
        scene_timings=scene_timings,
        editing_rhythm_plan=editing,
        audio_timeline=audio,
    )

    report = attach_quick_cut_schedule_to_report(report, schedule=editing)
    report = attach_audio_timeline_to_report(report, audio)
    report = attach_caption_style_to_report(report, caption_style)
    report = attach_montage_plan_to_report(report, montage)

    assert report["editing_rhythm_plan"]["debug"]["render_required"] is False
    assert report["audio_binding_timeline"]["debug"]["render_required"] is False
    assert report["caption_style_plan"]["debug"]["render_required"] is False
    assert report["montage_plan"]["debug"]["render_required"] is False
    assert report["editing_rhythm_plan"]["timing_confidence"] == "caption_phrase_timing"
    assert report["audio_binding_timeline"]["timing_confidence"] == "caption_phrase_timing"
    assert report["caption_report"]["style_profile"] == "modern_bounce"
    assert report["scene_reports"][0]["planned_quick_cut_count"] > 0
    assert report["scene_reports"][0]["audio_bound_sfx_cues"]
    assert report["scene_reports"][0]["montage_clip_count"] > 0
    assert any(event["event_type"] == "payoff_hit" for event in report["audio_binding_timeline"]["events"])
    assert any(clip["transition_in"] == "zoom_blend" for clip in report["montage_plan"]["clips"])
