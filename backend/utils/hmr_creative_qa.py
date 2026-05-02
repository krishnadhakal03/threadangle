"""Manual creative QA scorecard helpers for HMR review packages."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CREATIVE_QA_DIR = REPO_ROOT / "backend" / "data" / "creative_qa"
SCORE_FIELDS = (
    "hook_strength",
    "first_frame_strength",
    "proof_credibility",
    "pacing",
    "visual_novelty",
    "caption_readability",
    "sound_feel",
    "platform_fit",
    "post_worthiness",
)
STATUS_PASS = "CREATIVE_PASS"
STATUS_REVIEW = "CREATIVE_REVIEW"
STATUS_BLOCKED = "CREATIVE_BLOCKED"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _score(value: Any, field: str) -> int:
    try:
        score = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be an integer score from 1 to 10") from exc
    if score < 1 or score > 10:
        raise ValueError(f"{field} must be an integer score from 1 to 10")
    return score


def derive_creative_status(scorecard: dict[str, Any]) -> str:
    scores = [_score(scorecard[field], field) for field in SCORE_FIELDS]
    average = sum(scores) / len(scores)
    if scorecard["post_worthiness"] <= 4 or min(scores) <= 3:
        return STATUS_BLOCKED
    if min(scores) <= 5:
        return STATUS_REVIEW
    if average >= 7.0 and scorecard["post_worthiness"] >= 7:
        return STATUS_PASS
    return STATUS_REVIEW


def build_creative_qa_record(
    *,
    review_id: str,
    reviewer: str,
    scorecard: dict[str, Any],
    improvement_notes: str = "",
    manifest_path: str | None = None,
    review_package_path: str | None = None,
    platform: str | None = None,
) -> dict[str, Any]:
    """Validate and build one human creative QA record."""
    if not str(review_id or "").strip():
        raise ValueError("review_id is required")
    if not str(reviewer or "").strip():
        raise ValueError("reviewer is required")
    missing = [field for field in SCORE_FIELDS if field not in scorecard]
    if missing:
        raise ValueError(f"Missing creative QA score fields: {', '.join(missing)}")
    normalized_scorecard = {field: _score(scorecard[field], field) for field in SCORE_FIELDS}
    status = derive_creative_status(normalized_scorecard)
    return {
        "schema_version": 1,
        "review_id": str(review_id).strip(),
        "reviewer": str(reviewer).strip(),
        "reviewed_at": _now(),
        "creative_status": status,
        "average_creative_score": round(sum(normalized_scorecard.values()) / len(normalized_scorecard), 2),
        "scorecard": normalized_scorecard,
        "improvement_notes": str(improvement_notes or "").strip(),
        "manifest_path": str(manifest_path).strip() if manifest_path else None,
        "review_package_path": str(review_package_path).strip() if review_package_path else None,
        "platform": str(platform).strip() if platform else None,
        "separate_from": ["technical_status", "postability_status", "human_posting_gate"],
    }


def creative_qa_path(review_id: str, root: str | Path = DEFAULT_CREATIVE_QA_DIR) -> Path:
    safe = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in str(review_id).strip())
    return Path(root) / f"{safe}.json"


def write_creative_qa_record(record: dict[str, Any], root: str | Path = DEFAULT_CREATIVE_QA_DIR) -> Path:
    path = creative_qa_path(record["review_id"], root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def read_creative_qa_record(review_id: str, root: str | Path = DEFAULT_CREATIVE_QA_DIR) -> dict[str, Any]:
    path = creative_qa_path(review_id, root)
    return json.loads(path.read_text(encoding="utf-8"))


def update_creative_qa_record(
    review_id: str,
    updates: dict[str, Any],
    root: str | Path = DEFAULT_CREATIVE_QA_DIR,
) -> dict[str, Any]:
    record = read_creative_qa_record(review_id, root)
    scorecard = dict(record.get("scorecard") or {})
    scorecard.update(updates.get("scorecard") or {})
    if "improvement_notes" in updates:
        record["improvement_notes"] = str(updates["improvement_notes"] or "").strip()
    if "reviewer" in updates:
        record["reviewer"] = str(updates["reviewer"] or "").strip()
    normalized = build_creative_qa_record(
        review_id=record["review_id"],
        reviewer=record["reviewer"],
        scorecard=scorecard,
        improvement_notes=record.get("improvement_notes") or "",
        manifest_path=record.get("manifest_path"),
        review_package_path=record.get("review_package_path"),
        platform=record.get("platform"),
    )
    normalized["reviewed_at"] = record.get("reviewed_at") or normalized["reviewed_at"]
    write_creative_qa_record(normalized, root)
    return normalized


def attach_creative_qa(target: dict[str, Any], creative_qa: dict[str, Any] | None) -> dict[str, Any]:
    out = dict(target)
    out["creative_qa"] = creative_qa or {}
    return out
