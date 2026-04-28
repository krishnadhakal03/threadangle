"""Apply fireship_reference_50 preset to Day7 Coffee (REF3)

This runner loads the Day7 storyboard, applies the reference preset to
creative planning decisions, enforces some hard requirements, runs QA,
and writes a draft report + contact sheet. It does NOT render premium
voice or final video — this is a review draft.
"""
import json
from pathlib import Path
import os
from backend.storyboard import creative_director as cd
from backend.storyboard.style_presets import fireship_reference_50 as preset_mod

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "day7_coffee_storyboard.json"
OUT_DIR = ROOT / "generated_videos" / "storyboard_review"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def load_storyboard(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(obj, path: Path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)


def apply_preset_to_plan(plan: cd.CreativePlan, preset: dict):
    # enforce shot duration target in motion profile
    plan.motion_profile["shot_target_s"] = preset.get("default_shot_duration_target")
    plan.motion_profile["punch_prob"] = preset.get("zoom_rules", {}).get("punch_prob_per_cut")
    # annotate why with preset name
    plan.why_this_visual += f" | preset={preset.get('name')}"
    return plan


def run():
    sb = load_storyboard(INPUT)
    scenes = sb.get("scenes") or sb.get("shots") or []
    plans = []
    for i, s in enumerate(scenes):
        p = cd.generate_creative_plan(s, i, len(scenes))
        p = apply_preset_to_plan(p, preset_mod.preset)
        # enforce first-second rule: if scene 0, ensure motion + object + hook text
        if i == 0:
            if "motion" not in p.motion_profile:
                p.motion_profile["motion"] = "punch_zoom"
            if "object" not in p.required_assets:
                p.required_assets.append("strong_object_visual")
            p.why_this_visual += " | enforced:first_second_hook"
        plans.append(p)

    qa = cd.run_qa_on_plans(plans)

    report = {
        "preset": preset_mod.preset.get("name"),
        "qa_passed": qa.passed,
        "failures": qa.failures,
        "visual_medium_breakdown": {m: sum(1 for p in plans if p.visual_medium==m) for m in set(p.visual_medium for p in plans)},
        "generated_card_percentage": sum(1 for p in plans if p.visual_medium=="generated_card_last_resort") / max(1,len(plans)),
        "provider_usage": {
            "playwright": 0,
            "pexels": 1 if (os.getenv("PEXELS_API_KEY") or os.getenv("PEXELS_KEY")) else 0,
            "pixabay": 1 if (os.getenv("PIXABAY_API_KEY") or os.getenv("PIXABAY_KEY")) else 0,
        }
    }

    report_path = OUT_DIR / "day7_reference_style_report.json"
    write_json(report, report_path)

    # contact sheet
    contact_html = OUT_DIR / "day7_reference_contact_sheet.html"
    rows = []
    for p in plans:
        rows.append(f"<div class=scene><div class=swatch>{p.visual_medium}</div><div class=meta>Scene {p.scene_index} - {p.beat_role}</div></div>")
    html = f"""
    <html><head><meta charset='utf-8'><style>
    body{{font-family:Arial}}
    .scene{{display:inline-block;width:180px;height:120px;border:1px solid #ddd;margin:6px;padding:6px}}
    .swatch{{font-size:12px;padding:6px;background:#f7f7f7;border-radius:4px}}
    .meta{{font-size:12px;color:#333;margin-top:6px}}
    </style></head><body>
    <h3>Day7 Coffee - Reference Style Draft Contact Sheet</h3>
    {''.join(rows)}
    </body></html>
    """
    contact_html.write_text(html, encoding="utf-8")

    mp4_path = OUT_DIR / "day7_coffee_reference_style_v1.mp4"

    print("Report:", report_path)
    print("Contact sheet:", contact_html)
    print("Draft MP4 path (not generated):", mp4_path)


if __name__ == "__main__":
    run()
