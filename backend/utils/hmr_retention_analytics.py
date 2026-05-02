"""Manual retention analytics tracker for HMR posts."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ANALYTICS_PATH = REPO_ROOT / "backend" / "data" / "hmr_retention_analytics.jsonl"
PLATFORMS = {"youtube_shorts", "tiktok", "instagram_reels", "facebook_reels", "other"}
REQUIRED_FIELDS = {"platform", "post_url_or_id", "topic_domain", "hook_used", "posted_at"}
OPTIONAL_METRIC_FIELDS = {
    "agency_template",
    "first_frame_style",
    "video_duration_sec",
    "three_second_hold",
    "average_view_duration_sec",
    "completion_rate",
    "rewatch_rate",
    "saves",
    "shares",
    "comments",
    "follows_gained",
    "notes",
    "manifest_path",
    "issue_number",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _as_float(value: Any, field: str) -> float | None:
    if value in {None, ""}:
        return None
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be numeric") from exc


def _as_int(value: Any, field: str) -> int | None:
    if value in {None, ""}:
        return None
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be an integer") from exc


def validate_analytics_record(record: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalize one manual post-performance record."""
    missing = sorted(field for field in REQUIRED_FIELDS if not str(record.get(field) or "").strip())
    if missing:
        raise ValueError(f"Missing required analytics fields: {', '.join(missing)}")
    platform = str(record["platform"]).strip().lower()
    if platform not in PLATFORMS:
        raise ValueError(f"Unsupported platform: {platform}")
    out = {
        "schema_version": 1,
        "recorded_at": str(record.get("recorded_at") or _now()),
        "platform": platform,
        "post_url_or_id": str(record["post_url_or_id"]).strip(),
        "topic_domain": str(record["topic_domain"]).strip(),
        "hook_used": str(record["hook_used"]).strip(),
        "agency_template": str(record.get("agency_template") or "").strip() or None,
        "first_frame_style": str(record.get("first_frame_style") or "").strip() or None,
        "video_duration_sec": _as_float(record.get("video_duration_sec"), "video_duration_sec"),
        "three_second_hold": _as_float(record.get("three_second_hold"), "three_second_hold"),
        "average_view_duration_sec": _as_float(record.get("average_view_duration_sec"), "average_view_duration_sec"),
        "completion_rate": _as_float(record.get("completion_rate"), "completion_rate"),
        "rewatch_rate": _as_float(record.get("rewatch_rate"), "rewatch_rate"),
        "saves": _as_int(record.get("saves"), "saves"),
        "shares": _as_int(record.get("shares"), "shares"),
        "comments": _as_int(record.get("comments"), "comments"),
        "follows_gained": _as_int(record.get("follows_gained"), "follows_gained"),
        "posted_at": str(record["posted_at"]).strip(),
        "notes": str(record.get("notes") or "").strip(),
        "manifest_path": str(record.get("manifest_path") or "").strip() or None,
        "issue_number": _as_int(record.get("issue_number"), "issue_number"),
    }
    return out


def append_analytics_record(record: dict[str, Any], path: str | Path = DEFAULT_ANALYTICS_PATH) -> dict[str, Any]:
    normalized = validate_analytics_record(record)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(normalized, sort_keys=True) + "\n")
    return normalized


def read_analytics_records(path: str | Path = DEFAULT_ANALYTICS_PATH) -> list[dict[str, Any]]:
    target = Path(path)
    if not target.exists():
        return []
    records = []
    for line in target.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(validate_analytics_record(json.loads(line)))
    return records


def link_analytics_to_manifest(manifest: dict[str, Any], records: list[dict[str, Any]]) -> dict[str, Any]:
    """Attach lightweight analytics references to a manifest/report dict."""
    package_path = str(manifest.get("review_package_path") or manifest.get("manifest_path") or "")
    linked = [
        record
        for record in records
        if record.get("manifest_path") and (str(record["manifest_path"]) == package_path or str(record["manifest_path"]) in package_path)
    ]
    out = dict(manifest)
    out["retention_analytics"] = {
        "linked_record_count": len(linked),
        "platforms": sorted({record["platform"] for record in linked}),
        "latest_records": linked[-5:],
    }
    return out


def summarize_next_video_decisions(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize manual analytics into next-video planning notes."""
    if not records:
        return {
            "record_count": 0,
            "best_hook": None,
            "best_template": None,
            "notes": ["No analytics records yet. Post a candidate and capture platform metrics manually."],
        }
    by_hook: dict[str, list[dict[str, Any]]] = {}
    by_template: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        by_hook.setdefault(record["hook_used"], []).append(record)
        if record.get("agency_template"):
            by_template.setdefault(str(record["agency_template"]), []).append(record)

    def score(items: list[dict[str, Any]]) -> float:
        values = []
        for item in items:
            if item.get("completion_rate") is not None:
                values.append(float(item["completion_rate"]))
            elif item.get("average_view_duration_sec") and item.get("video_duration_sec"):
                values.append(float(item["average_view_duration_sec"]) / max(0.1, float(item["video_duration_sec"])))
            elif item.get("three_second_hold") is not None:
                values.append(float(item["three_second_hold"]))
        return sum(values) / len(values) if values else 0.0

    best_hook = max(by_hook.items(), key=lambda item: score(item[1]))
    best_template = max(by_template.items(), key=lambda item: score(item[1])) if by_template else (None, [])
    notes = [
        f"Lean toward hook `{best_hook[0]}`; it has the strongest available retention score.",
    ]
    if best_template[0]:
        notes.append(f"Reuse or adapt agency template `{best_template[0]}` for the next related topic.")
    low_early = [record for record in records if record.get("three_second_hold") is not None and float(record["three_second_hold"]) < 0.35]
    if low_early:
        notes.append("Several records show weak 3-second hold; make the first-frame proof/payoff clearer.")
    return {
        "record_count": len(records),
        "best_hook": {"hook_used": best_hook[0], "score": round(score(best_hook[1]), 3), "records": len(best_hook[1])},
        "best_template": (
            {"agency_template": best_template[0], "score": round(score(best_template[1]), 3), "records": len(best_template[1])}
            if best_template[0]
            else None
        ),
        "notes": notes,
    }
