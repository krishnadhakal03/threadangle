from __future__ import annotations

import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def test_quick_cut_schedule_uses_caption_phrase_timing_and_payoff_hit():
    from utils.hmr_editing_rhythm import build_quick_cut_schedule

    schedule = build_quick_cut_schedule(
        script_text="I found $43 hiding in one bill. Compare it before you pay.",
        scene_timings=[
            {"scene_id": "hook", "start": 0.0, "end": 2.4, "label": "hook"},
            {"scene_id": "payoff", "start": 2.4, "end": 5.0, "label": "payoff_number_reveal"},
        ],
        caption_events=[
            {"start": 0.0, "end": 1.2, "text": "I found $43"},
            {"start": 1.2, "end": 2.4, "text": "hiding in one bill"},
            {"start": 2.4, "end": 3.5, "text": "Compare it"},
            {"start": 3.5, "end": 5.0, "text": "before you pay"},
        ],
    )

    assert schedule["profile"]["cut_frequency"] == "fast"
    assert schedule["profile"]["max_shot_duration"] == 1.15
    assert schedule["timing_confidence"] == "caption_phrase_timing"
    assert schedule["fallback_timing_used"] is False
    assert schedule["payoff_hit_time"] == 0.0
    assert schedule["debug"]["render_required"] is False
    assert schedule["debug"]["planned_cut_count"] >= 5
    assert max(cut["duration"] for cut in schedule["cut_schedule"]) <= 1.15
    assert any(cut["cue"] == "payoff_hit" for cut in schedule["cut_schedule"])


def test_quick_cut_schedule_falls_back_without_caption_events():
    from utils.hmr_editing_rhythm import build_quick_cut_schedule

    schedule = build_quick_cut_schedule(
        script_text="Stop scrolling. Check this number. Save $27 today.",
        scene_timings=[
            {"scene_id": "hook", "start": 0.0, "end": 1.8},
            {"scene_id": "proof", "start": 1.8, "end": 4.2},
        ],
        caption_events=[],
    )

    assert schedule["timing_confidence"] == "fallback_estimated"
    assert schedule["fallback_timing_used"] is True
    assert schedule["debug"]["caption_event_count"] >= 2
    assert schedule["scene_schedules"][0]["planned_shot_count"] >= 2


def test_attach_quick_cut_schedule_to_report_adds_scene_debug():
    from utils.hmr_editing_rhythm import attach_quick_cut_schedule_to_report, build_quick_cut_schedule

    schedule = build_quick_cut_schedule(
        script_text="Save $27 today.",
        scene_timings=[{"scene_id": "hook", "start": 0.0, "end": 2.0}],
        caption_events=[{"start": 0.0, "end": 2.0, "text": "Save $27 today"}],
    )
    report = attach_quick_cut_schedule_to_report(
        {"scene_reports": [{"scene_id": "hook", "duration": 2.0}]},
        schedule=schedule,
    )

    assert report["editing_rhythm_plan"]["profile"]["id"] == "quick_cut_shorts"
    assert report["scene_reports"][0]["planned_quick_cut_count"] >= 2
    assert report["scene_reports"][0]["planned_quick_cuts"][0]["transition"] == "hard_cut"
