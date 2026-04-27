from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from backend.storyboard.schema import Storyboard, StoryboardScene, VisualSource


def classify_scene(scene: Dict[str, Any]) -> Dict[str, Any]:
    sid = scene.get("scene_id", "")
    role = scene.get("beat_role") or scene.get("scene_type") or sid
    text = (scene.get("narration_text") or scene.get("caption_text") or "").lower()

    # Simple beat_role mapping
    beat_role = None
    if "hook" in sid or role == "hook":
        beat_role = "hook"
    elif "shock" in sid or role == "setup":
        beat_role = "shock"
    elif "turn" in sid or role == "proof":
        beat_role = "turn"
    elif "prompt" in sid or "prompt" in text:
        beat_role = "prompt"
    elif "reveal" in sid or "reveal" in text:
        beat_role = "reveal"
    elif "payoff" in sid or role == "payoff":
        beat_role = "payoff"
    elif "cta" in sid or role == "cta":
        beat_role = "cta"
    else:
        beat_role = "proof"

    # emotional intent heuristic
    if any(w in text for w in ("surprise", "shock", "whoa", "wait")):
        emotional_intent = "surprise"
    elif any(w in text for w in ("save", "save", "$", "month", "year")):
        emotional_intent = "relief"
    elif any(w in text for w in ("proof", "ai", "prompt")):
        emotional_intent = "proof"
    else:
        emotional_intent = "curiosity"

    # best visual medium rules
    if beat_role == "hook":
        best = "stock_clip"
    elif beat_role == "shock":
        best = "comparison_card"
    elif beat_role == "prompt":
        best = "browser_capture"
    elif beat_role == "reveal":
        best = "comparison_card"
    elif beat_role == "payoff":
        best = "payoff_card"
    elif beat_role == "cta":
        best = "icon_animation"
    else:
        best = "proof_card"

    required_objects: List[str] = []
    if beat_role == "hook":
        required_objects = ["coffee cup", "receipt", "hand"]
    elif beat_role == "shock":
        required_objects = ["receipt", "calculator"]
    elif beat_role == "prompt":
        required_objects = ["browser", "prompt text"]
    elif beat_role == "reveal":
        required_objects = ["coffee shop", "home brew", "money"]
    elif beat_role == "payoff":
        required_objects = ["money", "year"]

    return {
        "scene_id": sid,
        "beat_role": beat_role,
        "emotional_intent": emotional_intent,
        "best_visual_medium": best,
        "fallback_visual_medium": "proof_card",
        "required_visual_objects": required_objects,
    }


def plan_assets(storyboard: Storyboard, out_dir: Path) -> Dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    plan: Dict[str, Any] = {"project_id": storyboard.project_id, "scenes": []}
    for scene in storyboard.scenes:
        info = classify_scene(scene.model_dump())
        asset_query = " ".join(info.get("required_visual_objects", [])) or scene.scene_id
        capture_instruction = "" if info["best_visual_medium"] not in ("browser_capture", "local_ai_capture") else "capture browser session or local AI prompt"
        plan_entry = {
            "scene_id": scene.scene_id,
            "visual_medium": info["best_visual_medium"],
            "asset_query": asset_query,
            "capture_instruction": capture_instruction,
            "fallback_strategy": info["fallback_visual_medium"],
            "required_layers": scene.visual_layers or [],
            "reject_conditions": [],
        }
        plan["scenes"].append(plan_entry)

    plan_path = out_dir / "asset_plan.json"
    import json

    plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")
    return plan


def visual_modality_breakdown(storyboard: Storyboard, plan: Dict[str, Any]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for entry in plan["scenes"]:
        m = entry["visual_medium"]
        counts[m] = counts.get(m, 0) + 1
    return counts
