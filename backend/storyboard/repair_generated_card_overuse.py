"""SSP8 repair: replace generated_card_last_resort with stock/local where possible

Writes repaired plans and re-runs critic for Day6 and Day7.
If Day7 critic passes, will (optionally) run render step — skipped unless explicitly safe.
"""
import json
from pathlib import Path
from typing import List, Dict

from backend.storyboard import provider_availability
from backend.storyboard import scene_critic

OUT = Path(__file__).resolve().parents[1] / "generated_videos" / "storyboard_review"
OUT.mkdir(parents=True, exist_ok=True)


def load_plan(path: Path) -> List[Dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def save_plan(plan: List[Dict], path: Path):
    path.write_text(json.dumps(plan, indent=2), encoding="utf-8")


def repair_plan(plan: List[Dict], providers: Dict) -> List[Dict]:
    pex = providers.get("pexels_configured")
    pix = providers.get("pixabay_configured")
    play = providers.get("playwright_sandbox_profile")

    def choose_stock():
        if pex:
            return "stock_clip", "pexels"
        if pix:
            return "stock_clip", "pixabay"
        return None, None

    out = []
    for s in plan:
        new = dict(s)
        med = s.get("chosen_medium")
        beat = s.get("beat_role") or ""
        sid = (s.get("scene_id") or "").lower()
        text = (s.get("narration_text") or "").lower()

        if med == "generated_card_last_resort":
            # apply repair policy
            if "hook" in beat or beat == "hook" or "hook" in sid:
                # generated forbidden
                stock, prov = choose_stock()
                if stock:
                    new["chosen_medium"] = stock
                    new["chosen_provider"] = prov
                    new.setdefault("why_this_medium", "repaired: prefer stock for hook")
                else:
                    new["chosen_medium"] = "generated_card_last_resort"
                    new.setdefault("hard_reject_conditions", []).append("no_stock_for_hook")
            elif beat in ("shock", "proof", "tension") or any(k in sid for k in ("shock","receipt","cost","price","money","math","calculator","proof","receipt")) or any(k in text for k in ("receipt","price","cost","math","calculator","proof","total")):
                stock, prov = choose_stock()
                if stock:
                    new["chosen_medium"] = stock
                    new["chosen_provider"] = prov
                    # add overlay hint
                    new.setdefault("required_visual_objects",[]).append("receipt_or_calculator_overlay")
                    new.setdefault("why_this_medium", "repaired: stock+overlay for proof/shock")
                else:
                    new.setdefault("hard_reject_conditions",[]).append("no_stock_for_shock")
            elif "prompt" in text or "prompt" in sid:
                if play:
                    new["chosen_medium"] = "playwright_browser_capture"
                    new["chosen_provider"] = "playwright"
                    new.setdefault("why_this_medium", "repaired: browser capture for prompt")
                else:
                    new["chosen_medium"] = "local_ai_prompt_capture"
                    new.setdefault("why_this_medium", "repaired: local AI prompt capture for prompt scene")
            elif beat in ("comparison","reveal") or "reveal" in sid or "compare" in sid:
                new["chosen_medium"] = "comparison_card"
                new.setdefault("required_visual_objects",[]).append("icon_pair")
                new.setdefault("why_this_medium", "repaired: comparison card for reveal/comparison")
            elif beat == "payoff":
                new["chosen_medium"] = "payoff_card"
            elif "payoff" in sid:
                new["chosen_medium"] = "payoff_card"
            elif beat == "cta":
                stock, prov = choose_stock()
                if stock:
                    new["chosen_medium"] = stock
                    new["chosen_provider"] = prov
                    new.setdefault("why_this_medium", "repaired: stock for CTA with visual callback")
                else:
                    new.setdefault("why_this_medium", "cta allowed generated only if visual callback; none available")
        out.append(new)
    return out


def analyze_and_save(original_path: Path, prefix: str, providers: Dict):
    plan = load_plan(original_path)
    # compute before stats
    before_generated = sum(1 for s in plan if s.get("chosen_medium")=="generated_card_last_resort")
    before_pct = before_generated / max(1, len(plan))

    repaired = repair_plan(plan, providers)
    repaired_path = OUT / f"scene_selection_plan_{prefix}_repaired.json"
    save_plan(repaired, repaired_path)

    # run critic
    critic = scene_critic.run_critic(repaired)
    critic_path = OUT / f"critic_report_{prefix}_repaired.json"
    critic_path.write_text(json.dumps(critic, indent=2), encoding="utf-8")

    after_generated = critic.get("generated_card_count")
    after_pct = critic.get("generated_card_pct")

    return {
        "original": str(original_path),
        "repaired": str(repaired_path),
        "critic": str(critic_path),
        "before_pct": before_pct,
        "after_pct": after_pct,
        "critic_passed": critic.get("passed"),
        "critic_details": critic,
    }


def run():
    prov = provider_availability.check_providers()
    day6 = Path(__file__).resolve().parents[1] / "generated_videos" / "storyboard_review" / "scene_selection_plan_day6.json"
    day7 = Path(__file__).resolve().parents[1] / "generated_videos" / "storyboard_review" / "scene_selection_plan_day7.json"

    out6 = analyze_and_save(day6, "day6", prov)
    out7 = analyze_and_save(day7, "day7", prov)

    manifest = {
        "providers": prov,
        "day6": out6,
        "day7": out7,
    }
    manifest_path = OUT / "ssp8_repair_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print("Repair manifest written:", manifest_path)
    return manifest_path


if __name__ == "__main__":
    run()
