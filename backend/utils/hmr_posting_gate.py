"""Human posting gate for HMR production reports."""

from __future__ import annotations

from typing import Any


READY_FOR_HUMAN_POST_REVIEW = "READY_FOR_HUMAN_POST_REVIEW"
BLOCKED_ASSET_MISSING = "BLOCKED_ASSET_MISSING"
BLOCKED_PLATFORM_EXPORT = "BLOCKED_PLATFORM_EXPORT"
BLOCKED_HUMAN_VISUAL_REVIEW = "BLOCKED_HUMAN_VISUAL_REVIEW"
POSTED = "POSTED"
UNKNOWN = "UNKNOWN"

HUMAN_POSTING_GATE_STATUSES = {
    READY_FOR_HUMAN_POST_REVIEW,
    BLOCKED_ASSET_MISSING,
    BLOCKED_PLATFORM_EXPORT,
    BLOCKED_HUMAN_VISUAL_REVIEW,
    POSTED,
    UNKNOWN,
}


def normalize_human_posting_gate(value: Any) -> str:
    """Normalize arbitrary gate text to one of the supported statuses."""
    normalized = str(value or "").strip().upper().replace(" ", "_").replace("-", "_")
    aliases = {
        "READY": READY_FOR_HUMAN_POST_REVIEW,
        "POST_REVIEW_CANDIDATE": READY_FOR_HUMAN_POST_REVIEW,
        "READY_FOR_POST_REVIEW": READY_FOR_HUMAN_POST_REVIEW,
        "READY_FOR_HUMAN_REVIEW": READY_FOR_HUMAN_POST_REVIEW,
        "DO_NOT_POST": BLOCKED_HUMAN_VISUAL_REVIEW,
        "NO_POST": BLOCKED_HUMAN_VISUAL_REVIEW,
        "BLOCKED": BLOCKED_HUMAN_VISUAL_REVIEW,
    }
    normalized = aliases.get(normalized, normalized)
    return normalized if normalized in HUMAN_POSTING_GATE_STATUSES else UNKNOWN


def _planned_real_asset_rows(render_report: dict[str, Any]) -> list[dict[str, Any]]:
    rows = render_report.get("scene_reports") or []
    planned_media = {"stock_footage", "stock_image", "playwright_capture", "local_asset"}
    return [
        row
        for row in rows
        if (row.get("scene_asset_strategy") or {}).get("visual_medium") in planned_media
        and (row.get("scene_asset_strategy") or {}).get("visual_medium") != "motion_template"
    ]


def _has_unresolved_real_assets(render_report: dict[str, Any]) -> bool:
    gate = render_report.get("visual_realism_human_gate") or {}
    planned = gate.get("planned_real_sources")
    resolved = gate.get("resolved_real_assets")
    if planned is not None and resolved is not None:
        try:
            if int(resolved) < int(planned):
                return True
        except (TypeError, ValueError):
            pass
    for row in _planned_real_asset_rows(render_report):
        if row.get("fallback_used") or not row.get("resolved_asset_type"):
            return True
    return False


def _has_platform_export_failure(*reports: dict[str, Any]) -> bool:
    failure_values = {"FAIL", "FAILED", "ERROR", "BLOCKED", "MISSING", "UNREADABLE"}
    for report in reports:
        if not report:
            continue
        if report.get("platform_export_failed") is True or report.get("platform_export_error"):
            return True
        status = str(report.get("platform_export_status") or report.get("platform_exports_status") or "").upper()
        if status in failure_values:
            return True
        exports = report.get("platform_exports") or {}
        if isinstance(exports, dict):
            for value in exports.values():
                if isinstance(value, dict) and str(value.get("status") or "").upper() in failure_values:
                    return True
    return False


def _human_review_gate(human_review: dict[str, Any]) -> str:
    explicit = normalize_human_posting_gate(human_review.get("human_posting_gate"))
    if explicit != UNKNOWN:
        return explicit
    recommendation = str(human_review.get("post_no_post_recommendation") or "").strip().lower()
    if not recommendation:
        return UNKNOWN
    if any(token in recommendation for token in ("do not post", "no-post", "no post", "blocked")):
        return BLOCKED_HUMAN_VISUAL_REVIEW
    if any(token in recommendation for token in ("post review candidate", "ready for human", "ready for today", "post next")):
        return READY_FOR_HUMAN_POST_REVIEW
    if recommendation == "posted":
        return POSTED
    return UNKNOWN


def compute_human_posting_gate(
    *,
    render_report: dict[str, Any] | None = None,
    qa_report: dict[str, Any] | None = None,
    human_review: dict[str, Any] | None = None,
    manifest: dict[str, Any] | None = None,
) -> str:
    """Compute the separate production posting gate without changing QA scores."""
    render_report = render_report or {}
    qa_report = qa_report or {}
    human_review = human_review or render_report.get("human_review") or qa_report.get("human_review") or {}
    manifest = manifest or {}

    explicit_gates = []
    for report in (manifest, qa_report, render_report):
        explicit = normalize_human_posting_gate(report.get("human_posting_gate"))
        if explicit != UNKNOWN:
            explicit_gates.append(explicit)

    if POSTED in explicit_gates:
        return POSTED

    if _has_platform_export_failure(manifest, qa_report, render_report):
        return BLOCKED_PLATFORM_EXPORT

    if _has_unresolved_real_assets(render_report):
        return BLOCKED_ASSET_MISSING

    if explicit_gates:
        return explicit_gates[0]

    review_gate = _human_review_gate(human_review)
    if review_gate != UNKNOWN:
        return review_gate

    return UNKNOWN
