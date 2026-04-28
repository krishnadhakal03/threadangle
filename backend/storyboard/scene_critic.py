"""Scene critic for validating scene selection plans (SSP2)

Runs a set of deterministic checks on the planner output and returns
PASS/FAIL plus per-scene issues and suggested fixes.
"""
from typing import List, Dict


def run_critic(plan: List[Dict]) -> Dict:
    issues: Dict[int, List[str]] = {}
    total = len(plan) or 1
    generated_count = 0
    for i, s in enumerate(plan):
        scene_issues = []
        med = s.get("chosen_medium")
        # generated hook
        if i == 0 and med == "generated_card_last_resort":
            scene_issues.append("hook_uses_generated_card")
        if med == "generated_card_last_resort":
            generated_count += 1
        # prompt scenes must be browser/local
        if "prompt" in (s.get("narration_text") or "").lower() and med not in ("playwright_browser_capture", "local_ai_prompt_capture"):
            scene_issues.append("prompt_not_capture")
        # shock scenes should have proof/object
        if s.get("beat_role") in ("shock", "proof"):
            rt = s.get("required_visual_objects") or []
            if not rt:
                scene_issues.append("shock_missing_proof_object")
        # check why
        if not s.get("why_this_medium"):
            scene_issues.append("missing_why")
        if scene_issues:
            issues[i] = scene_issues

    # overall checks
    overall = []
    if generated_count > max(1, int(total * 0.2)):
        overall.append("generated_card_overuse")

    # consecutive same medium
    for i in range(1, len(plan)):
        if plan[i].get("chosen_medium") == plan[i - 1].get("chosen_medium"):
            # allow if explicitly justified
            if not plan[i].get("rejected_media_with_reasons"):
                overall.append(f"consecutive_same_medium_at_{i}")

    passed = not issues and not overall
    report = {
        "passed": passed,
        "scene_issues": issues,
        "overall_issues": overall,
        "generated_card_count": generated_count,
        "generated_card_pct": generated_count / total,
    }
    return report


if __name__ == "__main__":
    import json
    print(json.dumps(run_critic([],), indent=2))
