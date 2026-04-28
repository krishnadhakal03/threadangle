"""Repair Day7 Coffee Fireship50 storyboard visuals (Scene Selection Policy)

Apply repair policy to day7_coffee_fireship50_storyboard.json:
- Hook: must NOT be generated_card → fallback to generated_card (no stock providers)
- Shock/Proof scenes: prefer proof_screenshot with overlay, fallback to generated_card
- Prompt scenes: use local_dom_reconstruction
- Reveal scenes: use generated_card with comparison_layout layer
- Payoff scenes: use proof_screenshot
- CTA: use generated_card with required visual callback

Reporter will show:
- before/after generated-card %
- critic pass/fail
- issue count
"""

import json
from pathlib import Path
from typing import List, Dict

from backend.storyboard.schema import load_storyboard, save_storyboard, VisualSource
from backend.storyboard import provider_availability


OUT = Path(__file__).resolve().parents[1] / "generated_videos" / "storyboard_review"
OUT.mkdir(parents=True, exist_ok=True)


def repair_visuals(storyboard):
    """Apply scene selection repair policy to storyboard.
    
    Hard rules:
    - generated-card fallback under 20%
    - hook cannot be generated card
    - shock cannot be generated card
    - prompt cannot be generated card
    - reveal cannot be generated card
    - payoff may be premium payoff card
    - CTA must have visual callback
    """
    providers = provider_availability.check_providers()
    has_stock = providers.get("pexels_configured") or providers.get("pixabay_configured")
    
    before_generated = sum(1 for s in storyboard.scenes if s.visual_source == VisualSource.generated_card)
    
    issues = []
    
    for i, scene in enumerate(storyboard.scenes):
        scene_id = scene.scene_id.lower()
        beat = scene.beat_role.value if hasattr(scene.beat_role, 'value') else str(scene.beat_role)
        narration = (scene.narration_text or "").lower()
        
        # Apply repair policy
        if scene.visual_source == VisualSource.generated_card:
            
            # Hook: forbidden from generated card
            if "hook" in beat or "hook" in scene_id:
                scene.visual_source = VisualSource.proof_screenshot
                scene.proof_label = f"Hook must use proof screenshot (hard rule)"
                if not has_stock:
                    issues.append(f"Scene {i} ({scene_id}): hook fallback to proof_screenshot (no stock available)")
            
            # Shock/proof: prefer proof_screenshot with overlay
            elif beat in ("shock", "proof", "setup") or any(k in scene_id for k in ("shock", "receipt", "cost", "price", "money", "math", "proof")):
                scene.visual_source = VisualSource.proof_screenshot
                scene.proof_label = "Proof screenshot with cost/math overlay"
                if "money" in narration or "cost" in narration or "$" in narration or "price" in narration:
                    if "comparison" not in narration and "compare" not in narration:
                        scene.visual_layers.append("overlay:cost_calculator_ui:0.7")
                if not has_stock:
                    issues.append(f"Scene {i} ({scene_id}): shock/proof fallback to proof_screenshot")
            
            # Prompt: use local_dom_reconstruction
            elif "prompt" in narration or "prompt" in scene_id:
                scene.visual_source = VisualSource.local_dom_reconstruction
                scene.capture_notes = "AI prompt input in terminal/browser window"
                issues.append(f"Scene {i} ({scene_id}): prompt → local_dom_reconstruction")
            
            # Reveal/Comparison: generated_card with comparison_layout
            elif beat == "reveal" or "reveal" in scene_id or "compare" in narration:
                # Keep as generated_card but add comparison layer
                if "comparison" not in str(scene.visual_layers):
                    scene.visual_layers.append('comparison_layout:::{"left":"coffee shop","right":"home brew"}')
                issues.append(f"Scene {i} ({scene_id}): reveal with comparison_layout")
            
            # Payoff: use proof_screenshot
            elif beat == "payoff" or "payoff" in scene_id:
                scene.visual_source = VisualSource.proof_screenshot
                scene.proof_label = "$1500+ annual savings highlight"
                issues.append(f"Scene {i} ({scene_id}): payoff → proof_screenshot")
            
            # CTA: keep generated_card but add visual callback requirement
            elif beat == "cta":
                # Keep as generated_card but mark it requires visual callback
                scene.capture_notes = "Must include visual callback to coffee/savings theme"
                issues.append(f"Scene {i} ({scene_id}): CTA with visual callback requirement")
    
    after_generated = sum(1 for s in storyboard.scenes if s.visual_source == VisualSource.generated_card)
    after_pct = after_generated / max(1, len(storyboard.scenes))
    
    return {
        "before_generated_count": before_generated,
        "before_pct": before_generated / max(1, len(storyboard.scenes)),
        "after_generated_count": after_generated,
        "after_pct": after_pct,
        "issues": issues,
        "hard_rules_met": {
            "hook_not_generated": not any(s.scene_id.lower() == "hook" and s.visual_source == VisualSource.generated_card for s in storyboard.scenes),
            "shock_not_generated": not any("shock" in s.scene_id.lower() and s.visual_source == VisualSource.generated_card for s in storyboard.scenes),
            "prompt_not_generated": not any("prompt" in (s.narration_text or "").lower() and s.visual_source == VisualSource.generated_card for s in storyboard.scenes),
            "reveal_not_generated": not any("reveal" in s.scene_id.lower() and s.visual_source == VisualSource.generated_card for s in storyboard.scenes),
            "generated_under_20pct": after_pct < 0.20,
        }
    }


def main():
    repo_root = Path(__file__).resolve().parents[2]
    sb_path = repo_root / "backend" / "day7_coffee_fireship50_storyboard.json"
    
    print(f"Loading storyboard: {sb_path}")
    storyboard = load_storyboard(sb_path)
    
    print(f"Repairing {len(storyboard.scenes)} scenes...")
    repair_report = repair_visuals(storyboard)
    
    # Save repaired storyboard
    repaired_path = OUT / "day7_coffee_fireship50_repaired.json"
    save_storyboard(storyboard, repaired_path)
    print(f"Repaired storyboard saved: {repaired_path}")
    
    # Generate report
    report = {
        "original_storyboard": str(sb_path),
        "repaired_storyboard": str(repaired_path),
        "repair_summary": {
            "before_generated_pct": repair_report["before_pct"],
            "after_generated_pct": repair_report["after_pct"],
            "generated_cards_before": repair_report["before_generated_count"],
            "generated_cards_after": repair_report["after_generated_count"],
            "total_scenes": len(storyboard.scenes),
        },
        "hard_rules_met": repair_report["hard_rules_met"],
        "repair_issues": repair_report["issues"],
    }
    
    report_path = OUT / "repair_fireship50_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nRepair report:")
    print(json.dumps(report, indent=2))
    
    return report_path


if __name__ == "__main__":
    main()
