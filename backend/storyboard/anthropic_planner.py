"""Anthropic-based creative planner wrapper (SSP2)

Uses Anthropic/Claude for creative planning when enabled. Returns
strict JSON plan per scene. Falls back to rule-based planner when
Anthropic not available or disabled.
"""
import os
import json
from typing import List, Dict

from . import provider_availability


def _rule_based_plan(scenes: List[Dict], providers: Dict) -> List[Dict]:
    plans = []
    for i, s in enumerate(scenes):
        text = (s.get("text") or s.get("narration") or "").lower()
        beat = s.get("beat_role") or ("hook" if i == 0 else "setup")
        chosen_medium = "generated_card_last_resort"
        chosen_provider = None
        asset_query = s.get("asset_query") or text[:120]

        # simple deterministic rules
        if any(k in text for k in ("prompt", "ai prompt")):
            chosen_medium = "playwright_browser_capture" if providers.get("playwright_sandbox_profile") else "local_ai_prompt_capture"
        elif any(k in text for k in ("receipt", "receipt", "proof", "money", "price")):
            chosen_medium = "proof_screenshot"
        elif beat in ("hook", "cold_open", "shock"):
            chosen_medium = "stock_clip" if providers.get("pexels_configured") or providers.get("pixabay_configured") else "user_manual_clip"
        elif beat in ("comparison", "reveal"):
            chosen_medium = "comparison_card"
        elif beat == "payoff":
            chosen_medium = "payoff_card"
        else:
            chosen_medium = "stock_clip" if providers.get("local_stock_exists") else "generated_card_last_resort"

        # provider preference
        if chosen_medium == "stock_clip":
            if providers.get("pexels_configured"):
                chosen_provider = "pexels"
            elif providers.get("pixabay_configured"):
                chosen_provider = "pixabay"
            else:
                chosen_provider = "local_stock"

        plan = {
            "scene_id": s.get("scene_id") or f"scene_{i}",
            "narration_text": s.get("text") or s.get("narration") or "",
            "beat_role": beat,
            "emotional_intent": s.get("emotional_intent") or "informative",
            "viewer_question": s.get("viewer_question") or "",
            "chosen_medium": chosen_medium,
            "chosen_provider": chosen_provider,
            "asset_query_or_capture_instruction": asset_query,
            "edit_pattern": "cut_on_phrase",
            "motion_profile": {"type": "subtle"},
            "retention_strategy": {"interrupt_allowed": True},
            "why_this_medium": "rule_fallback",
            "rejected_media_with_reasons": [],
            "fallback_medium": "generated_card_last_resort",
            "hard_reject_conditions": [],
            "required_visual_objects": [],
        }
        plans.append(plan)
    return plans


def plan_with_anthropic(scenes: List[Dict]) -> List[Dict]:
    # Only run if enabled
    prov = provider_availability.check_providers()
    if not (prov.get("anthropic_available") and prov.get("enable_anthropic_planner")):
        return _rule_based_plan(scenes, prov)

    try:
        import anthropic
        client = anthropic.Client(os.getenv("ANTHROPIC_API_KEY"))
        # Build a single prompt asking for JSON for all scenes
        system = "You are a creative director and retention editor. For each scene, provide a JSON object with keys: beat_role, emotional_intent, chosen_medium, assets, why_this_medium, rejected_media, edit_pattern. Return a JSON list."
        messages = system + "\nScenes:\n"
        for s in scenes:
            messages += (s.get("text") or s.get("narration") or "") + "\n---\n"
        resp = client.completions.create(model="claude-2.1", prompt=messages, max_tokens=2000)
        text = resp.completion or resp["completion"]
        data = json.loads(text)
        return data
    except Exception:
        # On any failure, fallback
        return _rule_based_plan(scenes, prov)


if __name__ == "__main__":
    import json, sys
    prov = provider_availability.check_providers()
    sample = [{"scene_id":"s1","text":"Buy coffee and save $"}]
    out = plan_with_anthropic(sample)
    print(json.dumps(out, indent=2))
