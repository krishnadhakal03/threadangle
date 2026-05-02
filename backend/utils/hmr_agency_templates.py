"""Agency-style HMR template library and selection helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

try:
    from .hmr_scene_asset_strategy import detect_hmr_asset_domain_from_text
except ImportError:  # pragma: no cover - direct script execution fallback
    from hmr_scene_asset_strategy import detect_hmr_asset_domain_from_text


@dataclass(frozen=True)
class AgencyTemplate:
    template_id: str
    name: str
    supported_domains: list[str]
    hook_type: str
    scene_roles: list[str]
    proof_requirement: str
    pacing_profile: str
    pattern_interrupt_profile: str
    sound_design_profile: str
    expected_cta_style: str
    keywords: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


AGENCY_TEMPLATES = [
    AgencyTemplate(
        template_id="bill_leak_expose",
        name="Bill Leak Expose",
        supported_domains=["bill_leak", "generic_money_problem"],
        hook_type="hidden_cost_shock",
        scene_roles=["hook", "bill_context", "proof", "replacement", "payoff", "cta"],
        proof_requirement="bill_or_subscription_statement",
        pacing_profile="fast_reveal_then_proof",
        pattern_interrupt_profile="warning_label_number_flip_payoff_meter",
        sound_design_profile="warning_beep_soft_hit_riser_payoff_chime",
        expected_cta_style="comment_keyword_for_prompt_or_checklist",
        keywords=["bill", "subscription", "monthly", "plan", "price changed", "leak", "hidden fee"],
    ),
    AgencyTemplate(
        template_id="receipt_shock",
        name="Receipt Shock",
        supported_domains=["grocery_savings", "generic_money_problem"],
        hook_type="receipt_number_shock",
        scene_roles=["hook", "receipt_context", "proof", "swap", "payoff", "cta"],
        proof_requirement="receipt_or_checkout_screenshot",
        pacing_profile="dominant_number_first",
        pattern_interrupt_profile="red_circle_tick_number_flip",
        sound_design_profile="whoosh_tick_soft_hit_payoff_chime",
        expected_cta_style="comment_keyword_for_list_or_prompt",
        keywords=["receipt", "grocery", "checkout", "cart", "supermarket", "inflation"],
    ),
    AgencyTemplate(
        template_id="checked_this_so_you_dont",
        name="I Checked This So You Don't Have To",
        supported_domains=["creator_tools", "bill_leak", "grocery_savings", "coffee_savings", "generic_money_problem"],
        hook_type="curiosity_research_claim",
        scene_roles=["hook", "method", "proof", "result", "payoff", "cta"],
        proof_requirement="screen_capture_or_result_card",
        pacing_profile="curiosity_then_fast_evidence",
        pattern_interrupt_profile="swipe_transition_highlight_tick",
        sound_design_profile="whoosh_tick_soft_hit",
        expected_cta_style="save_or_comment_for_steps",
        keywords=["checked", "tested", "i asked", "ai", "compare", "research", "looked up"],
    ),
    AgencyTemplate(
        template_id="three_mistakes_costing_money",
        name="3 Mistakes Costing You Money",
        supported_domains=["bill_leak", "grocery_savings", "coffee_savings", "generic_money_problem"],
        hook_type="mistake_list_warning",
        scene_roles=["hook", "mistake_1", "mistake_2", "mistake_3", "fix", "cta"],
        proof_requirement="one_proof_asset_or_clear_calculation",
        pacing_profile="numbered_fast_list",
        pattern_interrupt_profile="checklist_tick_warning_label",
        sound_design_profile="tick_warning_beep_soft_hit",
        expected_cta_style="comment_keyword_for_checklist",
        keywords=["mistake", "mistakes", "costing", "stop doing", "overpay"],
    ),
    AgencyTemplate(
        template_id="before_after_savings",
        name="Before vs After Savings",
        supported_domains=["grocery_savings", "coffee_savings", "bill_leak", "generic_money_problem"],
        hook_type="before_after_delta",
        scene_roles=["hook", "before", "change", "after", "payoff", "cta"],
        proof_requirement="before_after_numbers_or_screenshots",
        pacing_profile="split_screen_delta",
        pattern_interrupt_profile="split_screen_before_after_payoff_meter",
        sound_design_profile="whoosh_tick_riser_payoff_chime",
        expected_cta_style="comment_keyword_for_prompt",
        keywords=["before", "after", "saved", "savings", "swap", "replace"],
    ),
    AgencyTemplate(
        template_id="hidden_fee_reveal",
        name="Hidden Fee Reveal",
        supported_domains=["bill_leak", "generic_money_problem"],
        hook_type="hidden_fee_warning",
        scene_roles=["hook", "fee_source", "proof", "why_it_matters", "fix", "cta"],
        proof_requirement="fee_line_item_or_statement",
        pacing_profile="warning_then_line_item",
        pattern_interrupt_profile="warning_label_red_circle_highlight",
        sound_design_profile="warning_beep_soft_hit_riser",
        expected_cta_style="comment_keyword_for_audit",
        keywords=["hidden fee", "fee", "charge", "billing", "statement"],
    ),
    AgencyTemplate(
        template_id="one_setting_saved_me",
        name="One Setting Saved Me $X",
        supported_domains=["bill_leak", "creator_tools", "generic_money_problem"],
        hook_type="single_setting_payoff",
        scene_roles=["hook", "setting", "proof", "before_after", "payoff", "cta"],
        proof_requirement="settings_screen_or_billing_result",
        pacing_profile="micro_tutorial_with_payoff",
        pattern_interrupt_profile="highlight_tick_payoff_meter",
        sound_design_profile="tick_soft_hit_payoff_chime",
        expected_cta_style="comment_keyword_for_setting",
        keywords=["setting", "saved me", "toggle", "changed this", "one setting"],
    ),
    AgencyTemplate(
        template_id="stop_paying_for_this",
        name="Stop Paying For This",
        supported_domains=["bill_leak", "coffee_savings", "generic_money_problem"],
        hook_type="direct_stop_command",
        scene_roles=["hook", "cost_context", "proof", "alternative", "payoff", "cta"],
        proof_requirement="cost_proof_and_alternative",
        pacing_profile="command_then_alternative",
        pattern_interrupt_profile="warning_label_swipe_transition_number_flip",
        sound_design_profile="warning_beep_whoosh_soft_hit",
        expected_cta_style="comment_keyword_for_alternative",
        keywords=["stop paying", "cancel", "downgrade", "alternative", "instead"],
    ),
]


def list_agency_templates() -> list[dict[str, Any]]:
    return [template.to_dict() for template in AGENCY_TEMPLATES]


def get_agency_template(template_id: str) -> dict[str, Any] | None:
    normalized = str(template_id or "").strip().lower()
    for template in AGENCY_TEMPLATES:
        if template.template_id == normalized:
            return template.to_dict()
    return None


def _score_template(template: AgencyTemplate, topic_text: str, domain: str) -> int:
    text = topic_text.lower()
    score = 0
    if domain and domain in template.supported_domains:
        score += 8
    score += sum(3 for keyword in template.keywords if keyword in text)
    if template.template_id in text or template.name.lower() in text:
        score += 20
    return score


def select_agency_template(topic: str, *, domain: str | None = None) -> dict[str, Any]:
    """Select the best agency template for a topic/domain."""
    topic_text = str(topic or "")
    detected_domain = domain or detect_hmr_asset_domain_from_text(topic_text)
    ranked = sorted(
        AGENCY_TEMPLATES,
        key=lambda template: (_score_template(template, topic_text, detected_domain), -AGENCY_TEMPLATES.index(template)),
        reverse=True,
    )
    selected = ranked[0]
    return {
        "selected_template": selected.to_dict(),
        "selected_template_id": selected.template_id,
        "domain": detected_domain or "",
        "selection_reason": (
            f"Matched domain `{detected_domain}` and topic keywords"
            if detected_domain
            else "Selected default agency template from topic keywords"
        ),
        "compatibility": [
            {
                "template_id": template.template_id,
                "score": _score_template(template, topic_text, detected_domain),
                "compatible": not detected_domain or detected_domain in template.supported_domains,
            }
            for template in AGENCY_TEMPLATES
        ],
    }


def select_agency_template_for_scenes(scenes: list[Any], script_text: str = "") -> dict[str, Any]:
    parts = [script_text]
    for scene in scenes or []:
        if isinstance(scene, dict):
            parts.extend(str(scene.get(key) or "") for key in ("id", "scene_id", "template", "caption_text", "narration_text", "visual_description"))
        else:
            parts.extend(str(getattr(scene, key, "") or "") for key in ("scene_id", "scene_type", "template", "caption_text", "narration_text"))
    return select_agency_template(" ".join(parts))
