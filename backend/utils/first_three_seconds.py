"""First-three-seconds planning for short-form HMR openings."""

from __future__ import annotations

import re
from typing import Any


FIRST_3_SECONDS_SCHEMA_VERSION = 1
FIRST_3_SECONDS_VISUAL_EXECUTION_STATUS = "planned_only"


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _clip_words(value: str, max_words: int) -> str:
    words = _clean_text(value).split()
    return " ".join(words[:max_words])


def _extract_number_or_payoff(hook_text: str) -> str:
    money = re.search(r"\$\s?\d+(?:[,.]\d+)?(?:\s?\/\s?(?:mo|month|year|yr))?", hook_text, re.IGNORECASE)
    if money:
        return money.group(0).replace(" ", "")
    number = re.search(r"\b\d+(?:[,.]\d+)?\b", hook_text)
    if number:
        return number.group(0)
    if re.search(r"\b(save|savings|payoff|keep|leak)\b", hook_text, re.IGNORECASE):
        return "hidden savings"
    return "fast payoff"


def _infer_proof_object(hook_text: str, topic: str | None = None) -> str:
    combined = f"{hook_text} {topic or ''}".lower()
    object_rules = [
        (("receipt", "grocery", "groceries"), "receipt or grocery total"),
        (("bill", "subscription", "charge"), "bill or subscription screen"),
        (("coffee", "cup", "cafe"), "coffee receipt"),
        (("ai", "chatgpt", "compare"), "AI comparison screen"),
        (("budget", "money", "savings", "leak"), "money leak proof"),
    ]
    for terms, label in object_rules:
        if any(term in combined for term in terms):
            return label
    return "visible proof object"


def _urgency_label(hook_text: str) -> str:
    text = hook_text.lower()
    if any(term in text for term in ("stop", "before", "warning", "mistake")):
        return "CHECK THIS FIRST"
    if any(term in text for term in ("leak", "hidden", "hiding", "missed")):
        return "HIDDEN LEAK"
    return "WATCH THIS"


def build_first_3_seconds_plan(
    *,
    selected_hook: str,
    topic: str | None = None,
    platform: str = "short_form",
) -> dict[str, Any]:
    """Build a structured opening plan without rendering video."""
    hook = _clean_text(selected_hook)
    if not hook:
        raise ValueError("selected_hook is required.")
    payoff = _extract_number_or_payoff(hook)
    proof_object = _infer_proof_object(hook, topic)
    big_claim = _clip_words(hook, 11)
    return {
        "schema_version": FIRST_3_SECONDS_SCHEMA_VERSION,
        "platform": platform,
        "hook_text": hook,
        "first_frame_style": "claim_proof_payoff",
        "big_claim_text": big_claim,
        "proof_object": proof_object,
        "number_payoff_preview": payoff,
        "urgency_warning_label": _urgency_label(hook),
        "no_slow_intro": True,
        "caption_text_preserved": hook,
        "pattern_interrupt": {
            "time_seconds": 1.2,
            "before_second": 2.0,
            "type": "snap_zoom_or_hard_cut",
            "instruction": f"Interrupt on {proof_object} before the viewer can scroll.",
        },
        "timing_hints": [
            {"start": 0.0, "end": 0.45, "layer": "big_claim_text"},
            {"start": 0.45, "end": 1.2, "layer": "proof_object"},
            {"start": 1.2, "end": 1.65, "layer": "pattern_interrupt"},
            {"start": 1.65, "end": 3.0, "layer": "number_payoff_preview"},
        ],
        "render_notes": {
            "requires_render": False,
            "preserve_existing_script_flow": True,
            "avoid": ["slow_intro", "logo_intro", "empty_establishing_shot"],
            "visual_execution_status": FIRST_3_SECONDS_VISUAL_EXECUTION_STATUS,
            "truthfulness_note": "This plan is metadata for review/planning; renderer templates do not yet consume it as a guaranteed visual treatment.",
        },
    }


def first_3_seconds_report_fields(plan: dict[str, Any]) -> dict[str, Any]:
    """Return report-friendly fields for render reports/manifests."""
    return {
        "first_frame_style": plan["first_frame_style"],
        "first_3_sec_strategy": {
            "visual_execution_status": FIRST_3_SECONDS_VISUAL_EXECUTION_STATUS,
            "big_claim_text": plan["big_claim_text"],
            "proof_object": plan["proof_object"],
            "number_payoff_preview": plan["number_payoff_preview"],
            "urgency_warning_label": plan["urgency_warning_label"],
            "no_slow_intro": plan["no_slow_intro"],
            "pattern_interrupt": plan["pattern_interrupt"],
            "timing_hints": plan["timing_hints"],
            "implementation_status": {
                "big_claim_text": "planned_only",
                "proof_object": "planned_only",
                "pattern_interrupt": "planned_only",
                "number_payoff_preview": "planned_only",
            },
        },
    }


def attach_first_3_seconds_to_report(report: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    """Attach first-three-second metadata without changing renderer output."""
    updated = dict(report or {})
    fields = first_3_seconds_report_fields(plan)
    updated.update(fields)
    human_review = dict(updated.get("human_review") or {})
    human_review["first_frame_style"] = fields["first_frame_style"]
    human_review["first_three_seconds_strategy"] = fields["first_3_sec_strategy"]
    updated["human_review"] = human_review
    return updated
