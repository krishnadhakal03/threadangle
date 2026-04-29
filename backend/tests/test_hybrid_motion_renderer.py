from pathlib import Path

import cv2

from utils.hybrid_motion_qa import run_hybrid_motion_qa
from utils.hybrid_motion_renderer import render_hybrid_video, split_caption_events
from utils.hybrid_scene_templates import ai_prompt_mock, payoff_number_reveal


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


def test_captions_stay_under_max_words():
    events = split_caption_events("one two three four five six seven eight nine", duration=3.0, max_words=4)
    assert events
    assert all(len(event["text"].split()) <= 4 for event in events)


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
            "MOTION_CARD": 3,
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
            "MOTION_CARD": 3,
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
            {"scene_id": "comparison", "duration": 4.4, "template": "comparison_split", "media_classification": "MOTION_CARD", "motion_score": 0.8},
            {"scene_id": "payoff", "duration": 4.4, "template": "payoff_number_reveal", "media_classification": "MOTION_CARD", "motion_score": 0.92},
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
    assert qa["postability_status"] == "PASS"
    assert qa["postability_score"]["categories"]["audio_video_sync"] == 7


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


def test_ai_prompt_mock_renders_without_browser_dependency():
    import numpy as np

    canvas = np.zeros((480, 270, 3), dtype=np.uint8)
    report = ai_prompt_mock(8, 0.75, canvas, {"prompt": "Compare costs.", "response": "A: $150\nB: $20"})
    assert report["template"] == "ai_prompt_mock"
    assert canvas.sum() > 0
