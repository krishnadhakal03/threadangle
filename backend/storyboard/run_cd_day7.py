"""Run Creative Director draft for Day7 Coffee Rescue test (CD3)

This script loads the existing `day7_coffee_storyboard.json`, produces
creative plans, asset plans, runs QA, and writes a review draft report
and a simple contact-sheet HTML. It does NOT create a final premium
render — this is a human-review draft.
"""
import json
import os
from pathlib import Path

from backend.storyboard import creative_director as cd

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


def make_contact_sheet_html(plans, out_path: Path):
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
    <h3>Day7 Coffee - Creative Director v1 Contact Sheet (Draft)</h3>
    {''.join(rows)}
    </body></html>
    """
    out_path.write_text(html, encoding="utf-8")


def run():
    sb = load_storyboard(INPUT)
    scenes = sb.get("scenes") or sb.get("shots") or sb.get("items") or []
    plans = []
    asset_plans = []
    for i, s in enumerate(scenes):
        p = cd.generate_creative_plan(s, i, len(scenes))
        plans.append(p)
        asset_plans.append(cd.plan_assets_for_scene(p, s))

    qa = cd.run_qa_on_plans(plans)

    report = {
        "qa_passed": qa.passed,
        "failures": qa.failures,
        "details": qa.details,
        "generated_card_percentage": sum(1 for p in plans if p.visual_medium=="generated_card_last_resort") / max(1,len(plans)),
        "visual_medium_breakdown": {m: sum(1 for p in plans if p.visual_medium==m) for m in set(p.visual_medium for p in plans)},
        "provider_usage": {
            "playwright": 0,
            "pexels": 1 if (os.getenv("PEXELS_API_KEY") or os.getenv("PEXELS_KEY")) else 0,
            "pixabay": 1 if (os.getenv("PIXABAY_API_KEY") or os.getenv("PIXABAY_KEY")) else 0,
            "local": 0,
            "fallback_generated": sum(1 for p in plans if p.visual_medium=="generated_card_last_resort"),
        },
    }

    report_path = OUT_DIR / "day7_creative_director_report.json"
    write_json(report, report_path)

    contact_path = OUT_DIR / "day7_contact_sheet.html"
    make_contact_sheet_html(plans, contact_path)

    # placeholder path for draft MP4 (not created)
    mp4_path = OUT_DIR / "day7_coffee_creative_director_v1.mp4"

    print("Report written:", report_path)
    print("Contact sheet:", contact_path)
    print("Draft MP4 path (not generated):", mp4_path)


if __name__ == "__main__":
    run()
