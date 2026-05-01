from __future__ import annotations

import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def test_pattern_interrupt_plan_includes_required_primitives():
    from utils.pattern_interrupts import PATTERN_INTERRUPT_PRIMITIVES, build_pattern_interrupt_plan

    plan = build_pattern_interrupt_plan(
        [
            {
                "id": "hook",
                "template": "hook_footage_overlay",
                "duration": 3.0,
                "caption_text": "Stop paying this hidden bill leak.",
            }
        ]
    )

    assert set(PATTERN_INTERRUPT_PRIMITIVES) == {
        "punch_zoom",
        "number_flip",
        "red_circle",
        "highlight",
        "swipe_transition",
        "checklist_tick",
        "split_screen_before_after",
        "warning_label",
        "payoff_meter",
    }
    assert plan["debug"]["scene_count"] == 1
    assert plan["debug"]["render_required"] is False
    assert plan["interrupts"][0]["type"] == "punch_zoom"
    assert plan["interrupts"][0]["local_time"] < 2


def test_pattern_interrupt_rules_vary_by_scene_role():
    from utils.pattern_interrupts import build_pattern_interrupt_plan

    plan = build_pattern_interrupt_plan(
        [
            {"id": "payoff", "template": "payoff_number_reveal", "duration": 3.2, "caption_text": "Save $43 this month."},
            {"id": "compare", "template": "comparison_split", "duration": 3.0, "caption_text": "Before and after comparison."},
            {"id": "steps", "template": "checklist", "duration": 3.0, "caption_text": "First check the bill. Second compare."},
        ]
    )

    by_scene = {row["scene_id"]: row for row in plan["scenes"]}
    assert by_scene["payoff"]["interrupts"][0]["type"] == "number_flip"
    assert by_scene["compare"]["interrupts"][0]["type"] == "split_screen_before_after"
    assert by_scene["steps"]["interrupts"][0]["type"] == "checklist_tick"


def test_pattern_interrupt_readability_limits_dense_caption():
    from utils.pattern_interrupts import build_scene_interrupt_schedule

    dense_scene = {
        "id": "dense",
        "template": "body",
        "duration": 5.0,
        "caption_text": "This caption has many words and should not get covered by too many visual effects at once.",
    }

    interrupts = build_scene_interrupt_schedule(dense_scene)

    assert len(interrupts) == 1
    assert interrupts[0]["readability_guard"]["avoid_caption_overlap"] is True


def test_attach_pattern_interrupts_to_report_adds_scene_debug():
    from utils.pattern_interrupts import attach_pattern_interrupts_to_report, build_pattern_interrupt_plan

    scenes = [{"id": "hook", "template": "hook", "duration": 3.0, "caption_text": "Wait. Check this bill first."}]
    plan = build_pattern_interrupt_plan(scenes)
    report = attach_pattern_interrupts_to_report(
        {"scene_reports": [{"scene_id": "hook", "template": "hook"}]},
        plan,
    )

    assert report["pattern_interrupt_plan"]["debug"]["interrupt_count"] >= 1
    assert report["scene_reports"][0]["planned_pattern_interrupts"][0]["type"] == "punch_zoom"


def test_legacy_interrupt_schedule_stays_compatible():
    from utils.pattern_interrupts import build_interrupt_schedule

    schedule = build_interrupt_schedule(7.0, min_gap=2.0, max_gap=3.0)

    assert schedule == [
        {"time": 2.0, "type": "punch_zoom"},
        {"time": 5.0, "type": "highlight"},
    ]
