from __future__ import annotations

import sys
from pathlib import Path

import numpy as np


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def test_modern_bounce_caption_profile_and_style_plan():
    from utils.hmr_caption_style import build_caption_style_plan

    plan = build_caption_style_plan(
        caption_events=[
            {"start": 0.0, "end": 1.0, "text": "I found $43"},
            {"start": 1.0, "end": 2.0, "text": "hidden leak today"},
        ],
        profile_id="modern_bounce",
    )

    assert plan["profile"]["bounce_enabled"] is True
    assert plan["profile"]["pop_scale"] == 1.12
    assert plan["profile"]["max_words_per_chunk"] == 4
    assert plan["profile"]["safe_area"] == {"top": 0.12, "bottom": 0.82, "left": 0.08, "right": 0.92}
    assert plan["profile"]["animation_in"] == 0.16
    assert plan["profile"]["animation_out"] == 0.1
    assert plan["profile"]["highlight_style"] == "mint_keyword_pop"
    assert plan["styled_events"][0]["emphasis_words"] == ["found", "$43"]
    assert plan["debug"]["violations"] == []
    assert plan["debug"]["render_required"] is False


def test_caption_animation_state_pops_in_and_holds():
    from utils.hmr_caption_style import caption_animation_state, get_caption_style_profile

    profile = get_caption_style_profile("modern_bounce")
    pop = caption_animation_state(event_start=0.0, event_end=1.2, current_time=0.04, profile=profile)
    hold = caption_animation_state(event_start=0.0, event_end=1.2, current_time=0.6, profile=profile)

    assert pop["phase"] == "pop_in"
    assert pop["scale"] > 1.0
    assert hold["phase"] == "hold"
    assert hold["scale"] == 1.0


def test_draw_caption_band_accepts_modern_bounce_style_without_breaking_legacy():
    from utils.hmr_caption_style import caption_animation_state, get_caption_style_profile
    from utils.hybrid_scene_templates import draw_caption_band

    canvas = np.zeros((1280, 720, 3), dtype=np.uint8)
    profile = get_caption_style_profile("high_energy")
    animation = caption_animation_state(event_start=0.0, event_end=1.0, current_time=0.03, profile=profile)
    report = draw_caption_band(
        canvas,
        "Stop this $27 leak today",
        caption_style=profile.to_dict(),
        animation_state=animation,
    )
    legacy_report = draw_caption_band(np.zeros((1280, 720, 3), dtype=np.uint8), "Save $27 today")

    assert report["caption_style"] == "high_energy"
    assert report["word_count"] == 3
    assert report["bounce_phase"] == "pop_in"
    assert report["animation_scale"] > 1.0
    assert "$27" in report["emphasis_words"]
    assert legacy_report["caption_style"] is None
    assert legacy_report["word_count"] == 3


def test_attach_caption_style_to_report_sets_caption_report_metadata():
    from utils.hmr_caption_style import attach_caption_style_to_report, build_caption_style_plan

    plan = build_caption_style_plan(caption_events=[{"start": 0, "end": 1, "text": "Save $27"}])
    report = attach_caption_style_to_report({"caption_report": {"event_count": 1}}, plan)

    assert report["caption_style_plan"]["profile"]["id"] == "modern_bounce"
    assert report["caption_report"]["style_profile"] == "modern_bounce"
    assert report["caption_report"]["bounce_enabled"] is True
    assert report["caption_report"]["highlight_style"] == "mint_keyword_pop"
