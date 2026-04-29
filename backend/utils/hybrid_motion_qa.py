"""QA checks for Hybrid Motion Renderer outputs."""

from __future__ import annotations

from collections import Counter
from typing import Any


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

    status = "FAIL" if any(i.get("severity") == "fail" for i in issues) else "PASS"
    return {
        "status": status,
        "issues": issues,
        "scene_ids": sorted({sid for issue in issues for sid in issue.get("scene_ids", []) if sid is not None}),
        "recommendations": recommendations,
    }
