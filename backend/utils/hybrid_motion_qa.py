"""QA checks for Hybrid Motion Renderer outputs."""

from __future__ import annotations

from collections import Counter
from typing import Any

try:
    from .hmr_posting_gate import compute_human_posting_gate
except ImportError:  # pragma: no cover - direct script execution fallback
    from hmr_posting_gate import compute_human_posting_gate


POSTABILITY_RECOMMENDATIONS = {
    "hook_visual_strength": "Strengthen the first two seconds with real footage, a more specific visual object, or a clearer thumb-stopping hook.",
    "template_polish": "Improve template polish before posting: reduce generic card feel, refine typography/spacing, and make scenes look less like a benchmark render.",
    "motion_variety": "Add more visual variety between scenes, especially footage, captures, object movement, or non-card transitions.",
    "pacing_retention": "Tighten pacing for retention with faster visual changes, fewer consecutive card-like beats, and stronger payoff build-up.",
    "caption_readability": "Fix caption readability by avoiding cropped text, key-number overlap, and overly dense caption moments.",
    "audio_video_sync": "Review audio/video sync by checking that narration cadence, captions, and scene changes feel intentionally timed.",
    "social_platform_readiness": "Do a human platform-readiness pass for vertical framing, opening hook, polish, audio, and shareability before posting.",
}


def _clamp_score(score: float) -> int:
    return max(1, min(10, int(round(score))))


def _score_postability(
    render_result: dict[str, Any],
    technical_issues: list[dict[str, Any]],
    technical_status: str,
) -> dict[str, Any]:
    reports = render_result.get("scene_reports") or []
    media_mix = render_result.get("media_mix") or {}
    warnings = render_result.get("warnings") or []
    benchmark = render_result.get("benchmark") or {}
    caption_report = render_result.get("caption_report") or {}
    audio_sync_report = render_result.get("audio_sync_report") or {}

    fail_codes = {issue.get("code") for issue in technical_issues if issue.get("severity") == "fail"}
    warn_codes = {issue.get("code") for issue in technical_issues if issue.get("severity") == "warn"}
    media_classes = {str(row.get("media_classification") or "") for row in reports}
    templates = {str(row.get("template") or "") for row in reports}
    motion_scores = [float(row.get("motion_score") or 0) for row in reports]
    avg_motion = sum(motion_scores) / max(1, len(motion_scores))

    first = reports[0] if reports else {}
    first_class = first.get("media_classification")
    first_signals = first.get("postability_signals") or {}
    has_hook_upgrade = first_signals.get("early_number_snap") and first_signals.get("hook_treatment")
    has_motion_interruption = any((row.get("postability_signals") or {}).get("motion_interruption") for row in reports)
    has_platform_payoff = any(
        row.get("template") == "payoff_number_reveal"
        and row.get("number_reveal")
        and (row.get("postability_signals") or {}).get("scene_treatment") == "platform_payoff_phone_overlay"
        and int((row.get("postability_signals") or {}).get("foreground_layers") or 0) >= 3
        and (row.get("postability_signals") or {}).get("share_energy") is True
        for row in reports
    )
    hook_visual_strength = {
        "REAL_STOCK": 8,
        "LOCAL_CAPTURE": 7,
        "ANIMATED_FALLBACK": 5,
        "MOTION_CARD": 3,
    }.get(str(first_class), 4)
    if has_hook_upgrade:
        hook_visual_strength += 2
    if first.get("duration", 0) > 3.0:
        hook_visual_strength -= 1
    if first.get("text_cropped"):
        hook_visual_strength -= 2

    card_count = int(media_mix.get("MOTION_CARD") or 0)
    animated_count = int(media_mix.get("ANIMATED_FALLBACK") or 0)
    real_or_capture_count = int(media_mix.get("REAL_STOCK") or 0) + int(media_mix.get("LOCAL_CAPTURE") or 0)

    template_polish = 7
    if animated_count:
        template_polish -= 1
    if card_count >= 3:
        template_polish -= 1
    if has_hook_upgrade:
        template_polish += 1
    if has_motion_interruption:
        template_polish += 1
    if "text_cropped" in fail_codes or "caption_covers_key_number" in fail_codes:
        template_polish -= 3
    if "same_background_used_3_plus_scenes" in warn_codes:
        template_polish -= 1

    motion_variety = 4 + min(3, len(media_classes)) + min(2, len(templates) // 2)
    if card_count >= 3:
        motion_variety -= 2
    if real_or_capture_count == 0:
        motion_variety -= 1
    if avg_motion >= 0.75:
        motion_variety += 1

    pacing_retention = 7
    if "more_than_2_consecutive_static_card_scenes" in fail_codes:
        pacing_retention -= 3
    if card_count >= 3:
        pacing_retention -= 1
    if has_hook_upgrade:
        pacing_retention += 1
    if has_motion_interruption:
        pacing_retention += 1
    if reports:
        avg_duration = sum(float(row.get("duration") or 0) for row in reports) / len(reports)
        if avg_duration > 3.25:
            pacing_retention -= 1
        if len(reports) < 5:
            pacing_retention -= 1

    caption_readability = 8
    if caption_report.get("violations"):
        caption_readability -= 2
    if "text_cropped" in fail_codes:
        caption_readability -= 3
    if "caption_covers_key_number" in fail_codes:
        caption_readability -= 3

    audio_video_sync = 6
    if any("rendered_with_silent_audio" in str(w) or "silent" in str(w) for w in warnings):
        audio_video_sync = 4
    else:
        duration_delta = audio_sync_report.get("duration_delta_sec")
        duration_strategy = audio_sync_report.get("duration_strategy")
        if duration_delta is not None:
            delta = float(duration_delta)
            if delta <= 0.35 and str(duration_strategy).startswith("scaled_to_audio_duration"):
                audio_video_sync = 7
            elif delta <= 0.75:
                audio_video_sync = 6
            else:
                audio_video_sync = 5
        elif any("tts_provider:gtts" == str(w) for w in warnings):
            audio_video_sync = 6
        elif any("tts_provider:pyttsx3" == str(w) for w in warnings):
            audio_video_sync = 6

    width = int(benchmark.get("width") or 0)
    height = int(benchmark.get("height") or 0)
    fps = int(benchmark.get("fps") or 0)
    social_platform_readiness = 6
    if height > width and height >= 1280 and fps >= 24:
        social_platform_readiness += 1
    if technical_status == "FAIL":
        social_platform_readiness -= 3
    if has_hook_upgrade:
        social_platform_readiness += 1
    if has_platform_payoff:
        social_platform_readiness += 1
    if hook_visual_strength < 7 or template_polish < 7:
        social_platform_readiness -= 1

    categories = {
        "hook_visual_strength": _clamp_score(hook_visual_strength),
        "template_polish": _clamp_score(template_polish),
        "motion_variety": _clamp_score(motion_variety),
        "pacing_retention": _clamp_score(pacing_retention),
        "caption_readability": _clamp_score(caption_readability),
        "audio_video_sync": _clamp_score(audio_video_sync),
        "social_platform_readiness": _clamp_score(social_platform_readiness),
    }
    average_score = round(sum(categories.values()) / len(categories), 2)
    low_score_recommendations = [
        POSTABILITY_RECOMMENDATIONS[name]
        for name, score in categories.items()
        if score < 7
    ]

    has_blocking_issues = any(issue.get("severity") == "fail" for issue in technical_issues)
    has_critical_score = any(score <= 4 for score in categories.values())
    has_review_score = any(score < 7 for score in categories.values())
    if technical_status == "FAIL" or has_critical_score or has_blocking_issues:
        status = "FAIL"
    elif has_review_score or low_score_recommendations:
        status = "REVIEW"
    elif average_score >= 8:
        status = "STRONG_PASS"
    else:
        status = "PASS"

    return {
        "scale": "1-10",
        "categories": categories,
        "average_score": average_score,
        "status": status,
        "recommendations": low_score_recommendations,
        "notes": [
            "Postability is a human-facing quality gate, separate from technical render validation.",
            "PASS means every category is at least 7 and no recommendations remain.",
            "STRONG_PASS means every category is at least 7 with an average score of at least 8.",
        ],
    }


def run_hybrid_motion_qa(render_result: dict[str, Any]) -> dict[str, Any]:
    reports = render_result.get("scene_reports") or []
    media_mix = render_result.get("media_mix") or {}
    issues: list[dict[str, Any]] = []
    recommendations: list[str] = []

    if not media_mix:
        issues.append({"code": "media_mix_missing", "severity": "fail", "scene_ids": []})

    if reports:
        first = reports[0]
        if first.get("duration", 0) >= 2 and first.get("media_classification") not in {"REAL_STOCK", "ANIMATED_FALLBACK", "LOCAL_CAPTURE"}:
            issues.append({
                "code": "no_footage_or_animated_object_first_2s",
                "severity": "fail",
                "scene_ids": [first.get("scene_id")],
            })

    consecutive_cards: list[Any] = []
    for report in reports:
        if report.get("media_classification") == "MOTION_CARD":
            consecutive_cards.append(report.get("scene_id"))
            if len(consecutive_cards) > 2:
                issues.append({
                    "code": "more_than_2_consecutive_static_card_scenes",
                    "severity": "fail",
                    "scene_ids": list(consecutive_cards),
                })
                break
        else:
            consecutive_cards = []

    for report in reports:
        if float(report.get("motion_score") or 0) < 0.15 and float(report.get("duration") or 0) >= 2:
            issues.append({
                "code": "no_visual_change_within_2_seconds",
                "severity": "fail",
                "scene_ids": [report.get("scene_id")],
            })
        if report.get("text_cropped"):
            issues.append({
                "code": "text_cropped",
                "severity": "fail",
                "scene_ids": [report.get("scene_id")],
            })
        caption_report = report.get("caption_report") or {}
        if caption_report.get("overlaps_key_number"):
            issues.append({
                "code": "caption_covers_key_number",
                "severity": "fail",
                "scene_ids": [report.get("scene_id")],
            })

    backgrounds = [r.get("background_id") for r in reports if r.get("background_id")]
    for bg, count in Counter(backgrounds).items():
        if count >= 3:
            issues.append({
                "code": "same_background_used_3_plus_scenes",
                "severity": "warn",
                "scene_ids": [r.get("scene_id") for r in reports if r.get("background_id") == bg],
            })

    stock_status = render_result.get("stock_status") or {}
    if stock_status.get("provider_available") and not stock_status.get("used") and not stock_status.get("reason"):
        issues.append({
            "code": "stock_available_but_ignored_without_reason",
            "severity": "warn",
            "scene_ids": [],
        })

    if any(i["code"] == "more_than_2_consecutive_static_card_scenes" for i in issues):
        recommendations.append("Insert footage, local capture, or animated fallback between card scenes.")
    if any(i["code"] == "caption_covers_key_number" for i in issues):
        recommendations.append("Move captions above/below key-number zones or shorten captions further.")
    if any(i["code"] == "no_visual_change_within_2_seconds" for i in issues):
        recommendations.append("Add camera move, count-up, typewriter, particles, or slide-in animation.")

    technical_status = "FAIL" if any(i.get("severity") == "fail" for i in issues) else "PASS"
    postability_score = _score_postability(render_result, issues, technical_status)
    postability_status = postability_score["status"]
    qa_report = {
        "status": technical_status,
        "technical_status": technical_status,
        "postability_status": postability_status,
        "postability_score": postability_score,
        "issues": issues,
        "scene_ids": sorted({sid for issue in issues for sid in issue.get("scene_ids", []) if sid is not None}),
        "recommendations": recommendations,
    }
    qa_report["human_posting_gate"] = compute_human_posting_gate(render_report=render_result, qa_report=qa_report)
    return qa_report
