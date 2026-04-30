from pathlib import Path

import cv2

from utils.hybrid_motion_qa import run_hybrid_motion_qa
from utils.hybrid_motion_renderer import render_hybrid_video, split_caption_events
from utils.hmr_scene_asset_strategy import plan_hmr_scene_assets
from utils.hybrid_scene_templates import ai_prompt_mock, money_shock_math, payoff_number_reveal
from utils.run_hybrid_motion_poc import build_day8_scenes
from utils.run_visual_realism_sprint1 import build_grocery_scenes


def _tiny_scenes():
    return [
        {
            "id": "hook",
            "template": "hook_footage_overlay",
            "duration": 0.45,
            "headline": "Coffee looked cheap",
            "caption_text": "Coffee looked cheap",
        },
        {
            "id": "prompt",
            "template": "ai_prompt_mock",
            "duration": 0.45,
            "prompt": "Compare coffee costs.",
            "caption_text": "AI compared the habit",
        },
        {
            "id": "payoff",
            "template": "payoff_number_reveal",
            "duration": 0.45,
            "number": "${count}",
            "caption_text": "Over fifteen hundred yearly",
        },
    ]


def test_renderer_creates_mp4(tmp_path, monkeypatch):
    monkeypatch.delenv("PEXELS_API_KEY", raising=False)
    monkeypatch.delenv("PIXABAY_API_KEY", raising=False)
    out = tmp_path / "hybrid.mp4"
    result = render_hybrid_video(
        _tiny_scenes(),
        "Coffee looked cheap until AI compared the habit.",
        out,
        fps=8,
        width=270,
        height=480,
        use_stock_backgrounds=False,
        use_free_tts=False,
    )
    assert out.exists()
    assert out.stat().st_size > 1000
    cap = cv2.VideoCapture(str(out))
    assert cap.isOpened()
    assert int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) > 0
    cap.release()
    assert result["video_path"] == str(out)
    assert result["render_profile"]["frame_count"] > 0
    assert result["render_profile"]["per_scene"]
    assert result["render_profile"]["per_template"]


def test_scene_reports_include_media_classification(tmp_path, monkeypatch):
    monkeypatch.delenv("PEXELS_API_KEY", raising=False)
    monkeypatch.delenv("PIXABAY_API_KEY", raising=False)
    result = render_hybrid_video(
        _tiny_scenes(),
        "One two three four five six.",
        tmp_path / "report.mp4",
        fps=8,
        width=270,
        height=480,
        use_stock_backgrounds=False,
        use_free_tts=False,
    )
    classes = {row["media_classification"] for row in result["scene_reports"]}
    assert "ANIMATED_FALLBACK" in classes
    assert "LOCAL_CAPTURE" in classes
    assert "MOTION_CARD" in classes
    assert result["media_mix"]
    assert result["scene_asset_strategy"]
    assert all("scene_asset_strategy" in row for row in result["scene_reports"])
    assert all("resolved_asset_type" in row for row in result["scene_reports"])
    assert all("asset_resolution_status" in row for row in result["scene_reports"])
    assert result["visual_realism_human_gate"]["planned_real_sources"] >= 1
    assert result["visual_realism_human_gate"]["scene_asset_strategy_used"] is True


def test_hmr_scene_asset_strategy_plans_grocery_visual_sources():
    strategy = plan_hmr_scene_assets(build_grocery_scenes())
    by_id = {row["scene_id"]: row for row in strategy}
    assert by_id["hook"]["visual_medium"] == "stock_footage"
    assert by_id["hook"]["asset_role"] == "thumb_stop_real_world_context"
    assert any("grocery receipt" in query.lower() for query in by_id["hook"]["query_candidates"])
    assert by_id["ai_compare"]["visual_medium"] == "playwright_capture"
    assert by_id["ai_compare"]["capture_hint"] == "receipt_audit_comparison"
    assert "motion_template" in by_id["ai_compare"]["fallback_order"]
    assert by_id["payoff"]["visual_medium"] == "stock_image"


def test_captions_stay_under_max_words():
    events = split_caption_events("one two three four five six seven eight nine", duration=3.0, max_words=4)
    assert events
    assert all(len(event["text"].split()) <= 4 for event in events)


def test_captions_keep_semantic_sentence_boundaries():
    script = (
        "That small habit was one hundred fifty dollars a month. "
        "Coffee shop was one hundred fifty. Home brew was about twenty. "
        "That is over fifteen hundred dollars a year."
    )
    captions = [event["text"] for event in split_caption_events(script, duration=12.0, max_words=4)]
    assert "small habit was one" not in captions
    assert "at home Coffee shop" not in captions
    assert "twenty That is over" not in captions
    assert "one hundred fifty dollars" in captions
    assert "Home brew was about" in captions


def test_qa_catches_card_only_sequence():
    qa = run_hybrid_motion_qa({
        "media_mix": {"MOTION_CARD": 3},
        "scene_reports": [
            {"scene_id": "a", "duration": 2.1, "media_classification": "MOTION_CARD", "motion_score": 0.5},
            {"scene_id": "b", "duration": 2.1, "media_classification": "MOTION_CARD", "motion_score": 0.5},
            {"scene_id": "c", "duration": 2.1, "media_classification": "MOTION_CARD", "motion_score": 0.5},
        ],
        "stock_status": {"provider_available": False},
    })
    assert qa["status"] == "FAIL"
    assert qa["technical_status"] == "FAIL"
    assert qa["postability_status"] == "FAIL"
    assert qa["postability_score"]["categories"]["hook_visual_strength"] < 7
    assert any(issue["code"] == "more_than_2_consecutive_static_card_scenes" for issue in qa["issues"])


def test_qa_marks_technically_valid_benchmark_for_postability_review():
    qa = run_hybrid_motion_qa({
        "media_mix": {
            "ANIMATED_FALLBACK": 2,
            "MOTION_CARD": 2,
            "MOTION_SCENE": 1,
            "LOCAL_CAPTURE": 1,
        },
        "scene_reports": [
            {"scene_id": "hook", "duration": 2.6, "template": "hook_footage_overlay", "media_classification": "ANIMATED_FALLBACK", "motion_score": 0.85},
            {"scene_id": "shock", "duration": 2.7, "template": "money_shock_math", "media_classification": "MOTION_CARD", "motion_score": 0.9},
            {"scene_id": "prompt", "duration": 3.2, "template": "ai_prompt_mock", "media_classification": "LOCAL_CAPTURE", "motion_score": 0.88},
            {"scene_id": "comparison", "duration": 2.8, "template": "comparison_split", "media_classification": "MOTION_CARD", "motion_score": 0.8},
            {"scene_id": "payoff", "duration": 2.8, "template": "payoff_number_reveal", "media_classification": "MOTION_CARD", "motion_score": 0.92},
            {"scene_id": "cta", "duration": 2.4, "template": "cta_callback", "media_classification": "ANIMATED_FALLBACK", "motion_score": 0.78},
        ],
        "warnings": ["tts_provider:gtts"],
        "caption_report": {"violations": []},
        "stock_status": {"provider_available": False},
        "benchmark": {"width": 1080, "height": 1920, "fps": 30},
    })
    assert qa["technical_status"] == "PASS"
    assert qa["postability_status"] == "REVIEW"
    assert qa["postability_score"]["categories"]["hook_visual_strength"] < 7
    assert qa["postability_score"]["recommendations"]


def test_qa_scores_measured_audio_alignment_as_acceptable():
    qa = run_hybrid_motion_qa({
        "media_mix": {
            "ANIMATED_FALLBACK": 2,
            "MOTION_CARD": 2,
            "MOTION_SCENE": 1,
            "LOCAL_CAPTURE": 1,
        },
        "scene_reports": [
                {
                    "scene_id": "hook",
                    "duration": 2.6,
                "template": "hook_footage_overlay",
                "media_classification": "ANIMATED_FALLBACK",
                "motion_score": 0.94,
                "postability_signals": {"early_number_snap": True, "hook_treatment": "price_snap_receipt_coffee"},
            },
            {"scene_id": "shock", "duration": 4.2, "template": "money_shock_math", "media_classification": "MOTION_CARD", "motion_score": 0.93, "postability_signals": {"motion_interruption": "price_check_sweep"}},
            {"scene_id": "prompt", "duration": 5.0, "template": "ai_prompt_mock", "media_classification": "LOCAL_CAPTURE", "motion_score": 0.88},
            {"scene_id": "comparison", "duration": 4.4, "template": "comparison_split", "media_classification": "MOTION_SCENE", "motion_score": 0.9},
            {
                "scene_id": "payoff",
                "duration": 4.4,
                "template": "payoff_number_reveal",
                "media_classification": "MOTION_CARD",
                "motion_score": 0.92,
                "number_reveal": True,
                "postability_signals": {
                    "scene_treatment": "platform_payoff_phone_overlay",
                    "foreground_layers": 3,
                    "share_energy": True,
                },
            },
            {"scene_id": "cta", "duration": 3.8, "template": "cta_callback", "media_classification": "ANIMATED_FALLBACK", "motion_score": 0.78},
        ],
        "warnings": ["tts_provider:gtts"],
        "caption_report": {"violations": []},
        "stock_status": {"provider_available": False},
        "benchmark": {"width": 1080, "height": 1920, "fps": 30},
        "audio_sync_report": {
            "duration_delta_sec": 0.05,
            "duration_strategy": "scaled_to_audio_duration_preserve_hook",
        },
    })
    assert qa["technical_status"] == "PASS"
    assert qa["postability_score"]["categories"]["audio_video_sync"] == 7
    assert qa["postability_score"]["categories"]["social_platform_readiness"] >= 8
    assert qa["postability_status"] == "STRONG_PASS"


def test_qa_marks_all_good_high_average_as_strong_pass():
    qa = run_hybrid_motion_qa({
        "media_mix": {"REAL_STOCK": 3, "LOCAL_CAPTURE": 2},
        "scene_reports": [
            {
                "scene_id": "hook",
                "duration": 2.4,
                "template": "hook_footage_overlay",
                "media_classification": "REAL_STOCK",
                "motion_score": 0.95,
                "postability_signals": {"early_number_snap": True, "hook_treatment": "price_snap_receipt_coffee"},
            },
            {"scene_id": "prompt", "duration": 2.6, "template": "ai_prompt_mock", "media_classification": "LOCAL_CAPTURE", "motion_score": 0.9, "postability_signals": {"motion_interruption": "prompt_sweep"}},
            {"scene_id": "proof", "duration": 2.4, "template": "hook_footage_overlay", "media_classification": "REAL_STOCK", "motion_score": 0.9},
            {"scene_id": "comparison", "duration": 2.4, "template": "comparison_split", "media_classification": "REAL_STOCK", "motion_score": 0.88},
            {"scene_id": "cta", "duration": 2.2, "template": "ai_prompt_mock", "media_classification": "LOCAL_CAPTURE", "motion_score": 0.85},
        ],
        "warnings": ["tts_provider:gtts"],
        "caption_report": {"violations": []},
        "benchmark": {"width": 1080, "height": 1920, "fps": 30},
        "audio_sync_report": {
            "duration_delta_sec": 0.05,
            "duration_strategy": "scaled_to_audio_duration",
        },
    })
    assert qa["technical_status"] == "PASS"
    assert qa["postability_status"] == "STRONG_PASS"
    assert qa["postability_score"]["average_score"] >= 8
    assert not qa["postability_score"]["recommendations"]


def test_payoff_scene_renders_number_reveal_config():
    import numpy as np

    canvas = np.zeros((480, 270, 3), dtype=np.uint8)
    report = payoff_number_reveal(0, 0.5, canvas, {"number": "${count}", "subline": "saved yearly"})
    assert report["number_reveal"] is True
    assert report["key_number_boxes"]
    assert canvas.sum() > 0


def test_day8_story_numbers_match_narration():
    scenes = {scene["id"]: scene for scene in build_day8_scenes()}
    assert scenes["shock_math"]["monthly_number"] == "$150/mo"
    assert scenes["shock_math"]["formula"] == "$5 x 30 = $150/mo"
    assert scenes["comparison"]["savings_number"] == "$130/mo"
    assert scenes["payoff"]["number"] == "$1,500+"

    import numpy as np

    canvas = np.zeros((480, 270, 3), dtype=np.uint8)
    math_report = money_shock_math(0, 0.98, canvas, scenes["shock_math"])
    payoff_report = payoff_number_reveal(0, 0.35, canvas, scenes["payoff"])
    assert math_report["key_number_boxes"]
    assert payoff_report["key_number_boxes"]


def test_ai_prompt_mock_renders_without_browser_dependency():
    import numpy as np

    canvas = np.zeros((480, 270, 3), dtype=np.uint8)
    report = ai_prompt_mock(8, 0.75, canvas, {"prompt": "Compare costs.", "response": "A: $150\nB: $20"})
    assert report["template"] == "ai_prompt_mock"
    assert canvas.sum() > 0
