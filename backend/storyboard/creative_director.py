"""Creative Director v1 - scene-level creative planning

This module generates a CreativePlan per scene describing beat role,
visual medium, required assets, motion profiles, edit events, and a
concise rationale `why_this_visual` so downstream systems and humans
can understand choices.

This is a review-draft implementation (CD1). It intentionally avoids
any paid providers and heavy external calls. Later commits add asset
planner and QA gate logic.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import os
import json

BEAT_ROLES = [
    "cold_open",
    "shock",
    "curiosity",
    "proof",
    "comparison",
    "reveal",
    "payoff",
    "cta",
]

VISUAL_MODALITIES = [
    "stock_clip",
    "playwright_browser_capture",
    "local_ai_prompt_capture",
    "proof_screenshot",
    "diagram_animation",
    "comparison_card",
    "payoff_card",
    "generated_card_last_resort",
]


@dataclass
class CreativePlan:
    scene_index: int
    beat_role: str
    emotional_intent: str
    visual_medium: str
    required_assets: List[str] = field(default_factory=list)
    motion_profile: Dict[str, str] = field(default_factory=dict)
    edit_events: List[str] = field(default_factory=list)
    reject_conditions: List[str] = field(default_factory=list)
    why_this_visual: str = ""


def _pick_beat_role(scene_text: str, index: int, total: int) -> str:
    # Lightweight heuristic for beat role based on keywords and position
    text = (scene_text or "").lower()
    if index == 0:
        return "cold_open"
    if any(k in text for k in ("shock", "surprise", "unexpected", "shock")):
        return "shock"
    if any(k in text for k in ("proof", "receipt", "evidence", "math", "calculator")):
        return "proof"
    if any(k in text for k in ("compare", "vs", "versus", "instead")):
        return "comparison"
    if any(k in text for k in ("reveal", "reveal", "turn", "but then")):
        return "reveal"
    if index >= total - 2:
        return "payoff" if index == total - 2 else "cta"
    return "curiosity"


def _pick_visual_medium(scene_text: str, beat_role: str, allow_generated_last_resort: bool = True) -> str:
    text = (scene_text or "").lower()
    # Enforce rules at a draft level (detailed rules added in CD2)
    if "prompt" in text or "ai prompt" in text:
        return "playwright_browser_capture"
    if beat_role == "comparison":
        return "comparison_card"
    if beat_role == "payoff":
        return "payoff_card"
    # Hook (cold_open/shock/curiosity) must prefer real footage
    if beat_role in ("cold_open", "shock", "curiosity"):
        return "stock_clip"
    # Fallbacks
    if allow_generated_last_resort:
        return "generated_card_last_resort"
    return "comparison_card"


def generate_creative_plan(scene: Dict, scene_index: int, total_scenes: int) -> CreativePlan:
    text = scene.get("text") or scene.get("narration") or ""
    beat = scene.get("beat_role") or _pick_beat_role(text, scene_index, total_scenes)
    visual = scene.get("visual_medium") or _pick_visual_medium(text, beat)
    emotional_intent = scene.get("emotional_intent") or "informative"

    required_assets = []
    if visual == "stock_clip":
        # simple query hint
        required_assets.append("stock_query:" + (scene.get("asset_query") or text[:80]))
    if visual == "playwright_browser_capture":
        required_assets.append("browser_capture_target:" + (scene.get("capture_target") or "prompt_page"))

    why = f"Beat='{beat}' -> chosen '{visual}' because scene text suggests {emotional_intent}."

    return CreativePlan(
        scene_index=scene_index,
        beat_role=beat,
        emotional_intent=emotional_intent,
        visual_medium=visual,
        required_assets=required_assets,
        motion_profile={"type": "subtle"},
        edit_events=["cut_on_phrase"],
        reject_conditions=[],
        why_this_visual=why,
    )


@dataclass
class AssetPlan:
    scene_index: int
    asset_query: str
    provider_order: List[str]
    fallback: str
    required_layers: List[str]
    reject_conditions: List[str]


def plan_assets_for_scene(plan: CreativePlan, scene: Dict) -> AssetPlan:
    # Provider order per spec (simplified decision tree)
    providers = [
        "user_locked",
        "user_manual",
        "playwright_browser_capture",
        "pexels",
        "pixabay",
        "local_stock",
        "generated_diagram",
        "generated_card_last_resort",
    ]

    query = scene.get("asset_query") or (scene.get("text") or "").strip()[:120]
    required_layers = ["base_visual"]
    if plan.visual_medium in ("comparison_card", "payoff_card"):
        required_layers.append("text_overlay")

    fallback = "generated_card_last_resort"

    # If PEXELS/Pixabay keys missing, deprioritize
    pexels_key = os.getenv("PEXELS_API_KEY") or os.getenv("PEXELS_KEY")
    pixabay_key = os.getenv("PIXABAY_API_KEY") or os.getenv("PIXABAY_KEY")
    if not pexels_key:
        providers.remove("pexels") if "pexels" in providers else None
    if not pixabay_key:
        providers.remove("pixabay") if "pixabay" in providers else None

    return AssetPlan(
        scene_index=plan.scene_index,
        asset_query=query,
        provider_order=providers,
        fallback=fallback,
        required_layers=required_layers,
        reject_conditions=[],
    )


@dataclass
class QAResult:
    passed: bool
    failures: List[str]
    details: Dict[str, List[str]]


def run_qa_on_plans(plans: List[CreativePlan]) -> QAResult:
    failures = []
    details = {}
    generated_cards = 0
    modalities = set()
    for p in plans:
        modalities.add(p.visual_medium)
        if p.visual_medium == "generated_card_last_resort":
            generated_cards += 1
        # Hook check
        if p.scene_index == 0 and p.visual_medium.startswith("generated"):
            failures.append("Hook is text-only/generated: hook must be real footage or strong visual")
            details.setdefault("scene_0", []).append("hook_is_generated")
        # Every non-payoff needs a visual object beyond text
        if p.beat_role != "payoff" and p.visual_medium in ("comparison_card", "payoff_card"):
            failures.append(f"Scene {p.scene_index} may be text-first; needs visual object")
            details.setdefault(f"scene_{p.scene_index}", []).append("no_visual_object")

    max_generated = max(1, int(len(plans) * 0.2))
    if generated_cards > max_generated:
        failures.append(f"Generated-card usage {generated_cards} exceeds max {max_generated}")

    # distinct modality count
    if len(modalities) < 4:
        failures.append("Fewer than 4 distinct visual modalities in contact sheet")

    passed = len(failures) == 0
    return QAResult(passed=passed, failures=failures, details=details)



if __name__ == "__main__":
    print("Creative Director module (CD1) loaded. Use generate_creative_plan(scene, i, total).")
