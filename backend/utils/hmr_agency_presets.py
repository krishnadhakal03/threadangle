"""Agency preset pack for repeatable HMR production modes."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

try:
    from .hmr_scene_asset_strategy import detect_hmr_asset_domain_from_text
except ImportError:  # pragma: no cover - direct script execution fallback
    from hmr_scene_asset_strategy import detect_hmr_asset_domain_from_text


@dataclass(frozen=True)
class AgencyPreset:
    preset_id: str
    compatible_domains: list[str]
    hook_lab_profile: str
    first_3_sec_profile: str
    agency_template_default: str
    pattern_interrupt_profile: str
    sfx_profile: str
    caption_style_hints: dict[str, Any]
    proof_asset_requirement_level: str
    export_preset_recommendation: str
    keywords: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


AGENCY_PRESETS = [
    AgencyPreset(
        preset_id="money_saving_agency",
        compatible_domains=["grocery_savings", "coffee_savings", "bill_leak", "generic_money_problem"],
        hook_lab_profile="payoff_first_money_delta",
        first_3_sec_profile="dominant_number_plus_real_object",
        agency_template_default="before_after_savings",
        pattern_interrupt_profile="number_flip_highlight_payoff_meter",
        sfx_profile="whoosh_tick_riser_payoff_chime",
        caption_style_hints={"max_words": 4, "emphasize_numbers": True, "tone": "plain_spoken"},
        proof_asset_requirement_level="recommended",
        export_preset_recommendation="youtube_shorts",
        keywords=["save", "saving", "money", "spend", "cost", "swap", "before", "after"],
    ),
    AgencyPreset(
        preset_id="bill_leak_expose",
        compatible_domains=["bill_leak", "generic_money_problem"],
        hook_lab_profile="hidden_fee_shock",
        first_3_sec_profile="bill_closeup_hidden_line_item",
        agency_template_default="bill_leak_expose",
        pattern_interrupt_profile="warning_label_red_circle_number_flip",
        sfx_profile="warning_beep_soft_hit_riser",
        caption_style_hints={"max_words": 4, "emphasize_numbers": True, "tone": "urgent_but_clear"},
        proof_asset_requirement_level="required",
        export_preset_recommendation="instagram_reels",
        keywords=["bill", "fee", "subscription", "charge", "billing", "leak"],
    ),
    AgencyPreset(
        preset_id="receipt_shock",
        compatible_domains=["grocery_savings", "generic_money_problem"],
        hook_lab_profile="receipt_total_shock",
        first_3_sec_profile="receipt_closeup_plus_total",
        agency_template_default="receipt_shock",
        pattern_interrupt_profile="red_circle_tick_number_flip",
        sfx_profile="whoosh_tick_soft_hit_payoff_chime",
        caption_style_hints={"max_words": 4, "emphasize_numbers": True, "tone": "curious_direct"},
        proof_asset_requirement_level="required",
        export_preset_recommendation="tiktok",
        keywords=["receipt", "grocery", "checkout", "cart", "inflation", "total"],
    ),
    AgencyPreset(
        preset_id="proof_first_short",
        compatible_domains=["creator_tools", "bill_leak", "grocery_savings", "coffee_savings", "generic_money_problem"],
        hook_lab_profile="proof_object_first",
        first_3_sec_profile="proof_before_claim",
        agency_template_default="checked_this_so_you_dont",
        pattern_interrupt_profile="highlight_swipe_tick",
        sfx_profile="whoosh_tick_soft_hit",
        caption_style_hints={"max_words": 4, "emphasize_numbers": False, "tone": "documentary"},
        proof_asset_requirement_level="required",
        export_preset_recommendation="youtube_shorts",
        keywords=["proof", "checked", "tested", "ai", "screen", "calculator", "receipt"],
    ),
    AgencyPreset(
        preset_id="fast_listicle_warning",
        compatible_domains=["bill_leak", "grocery_savings", "coffee_savings", "generic_money_problem"],
        hook_lab_profile="mistake_warning_list",
        first_3_sec_profile="three_item_warning",
        agency_template_default="three_mistakes_costing_money",
        pattern_interrupt_profile="checklist_tick_warning_label",
        sfx_profile="tick_warning_beep_soft_hit",
        caption_style_hints={"max_words": 3, "emphasize_numbers": True, "tone": "fast_warning"},
        proof_asset_requirement_level="optional",
        export_preset_recommendation="tiktok",
        keywords=["mistakes", "warning", "stop", "three", "3", "costing", "avoid"],
    ),
]


def list_agency_presets() -> list[dict[str, Any]]:
    return [preset.to_dict() for preset in AGENCY_PRESETS]


def get_agency_preset(preset_id: str) -> dict[str, Any] | None:
    normalized = str(preset_id or "").strip().lower()
    for preset in AGENCY_PRESETS:
        if preset.preset_id == normalized:
            return preset.to_dict()
    return None


def _score_preset(preset: AgencyPreset, topic_text: str, domain: str, template_id: str | None = None) -> int:
    text = topic_text.lower()
    score = 0
    if domain and domain in preset.compatible_domains:
        score += 8
    if template_id and template_id == preset.agency_template_default:
        score += 6
    score += sum(3 for keyword in preset.keywords if keyword in text)
    if preset.preset_id in text:
        score += 20
    return score


def select_agency_preset(
    topic: str,
    *,
    domain: str | None = None,
    agency_template_id: str | None = None,
    preset_id: str | None = None,
) -> dict[str, Any]:
    """Select a production preset for a topic/domain."""
    if preset_id:
        preset = get_agency_preset(preset_id)
        if not preset:
            raise ValueError(f"Unknown agency preset: {preset_id}")
        return {
            "selected_preset": preset,
            "selected_preset_id": preset["preset_id"],
            "domain": domain or detect_hmr_asset_domain_from_text(topic),
            "selection_reason": "explicit preset requested",
            "compatibility": [],
        }

    topic_text = str(topic or "")
    detected_domain = domain or detect_hmr_asset_domain_from_text(topic_text)
    ranked = sorted(
        AGENCY_PRESETS,
        key=lambda preset: (_score_preset(preset, topic_text, detected_domain, agency_template_id), -AGENCY_PRESETS.index(preset)),
        reverse=True,
    )
    selected = ranked[0]
    return {
        "selected_preset": selected.to_dict(),
        "selected_preset_id": selected.preset_id,
        "domain": detected_domain or "",
        "selection_reason": (
            f"Matched domain `{detected_domain}` with preset keywords"
            if detected_domain
            else "Selected preset from topic keywords"
        ),
        "compatibility": [
            {
                "preset_id": preset.preset_id,
                "score": _score_preset(preset, topic_text, detected_domain, agency_template_id),
                "compatible": not detected_domain or detected_domain in preset.compatible_domains,
            }
            for preset in AGENCY_PRESETS
        ],
    }


def select_agency_preset_for_scenes(
    scenes: list[Any],
    script_text: str = "",
    *,
    agency_template: dict[str, Any] | None = None,
    preset_id: str | None = None,
) -> dict[str, Any]:
    parts = [script_text]
    for scene in scenes or []:
        if isinstance(scene, dict):
            parts.extend(str(scene.get(key) or "") for key in ("id", "scene_id", "template", "caption_text", "narration_text", "visual_description"))
        else:
            parts.extend(str(getattr(scene, key, "") or "") for key in ("scene_id", "scene_type", "template", "caption_text", "narration_text"))
    selected_template_id = None
    if agency_template:
        selected_template_id = agency_template.get("selected_template_id") or (agency_template.get("selected_template") or {}).get("template_id")
    return select_agency_preset(" ".join(parts), agency_template_id=selected_template_id, preset_id=preset_id)
