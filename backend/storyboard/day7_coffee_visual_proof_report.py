"""
Generate comparison artifacts for Day7 Coffee baseline vs Fireship50 render.
"""

import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / 'backend'))

from PIL import Image, ImageDraw, ImageFont
from storyboard.schema import load_storyboard
from storyboard.editorial_density import EditorialDensityEngine
from storyboard.pattern_interrupts import InterruptType


BASELINE_ID = "day7_coffee_baseline_static"
FIRESHIP_ID = "day7_coffee_fireship50_proof"
BASELINE_DIR = REPO_ROOT / "backend" / "generated_videos" / "storyboard_review" / BASELINE_ID / "review"
FIRESHIP_DIR = REPO_ROOT / "backend" / "generated_videos" / "storyboard_review" / FIRESHIP_ID / "review"
OUTPUT_DIR = REPO_ROOT / "backend" / "generated_videos" / "storyboard_review" / "day7_coffee_proof_comparison"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_storyboard_json(path: Path):
    return load_storyboard(path)


def combine_images(images: list[Path], label: str, out_path: Path) -> None:
    loaded = [Image.open(img).convert("RGB") for img in images]
    widths, heights = zip(*(img.size for img in loaded))
    total_width = sum(widths)
    max_height = max(heights) + 60
    canvas = Image.new("RGB", (total_width, max_height), (30, 34, 41))
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()

    x = 0
    for img in loaded:
        canvas.paste(img, (x, 40))
        x += img.width
    draw.text((16, 12), label, fill=(255, 255, 255), font=font)
    canvas.save(out_path, quality=90)


def make_side_by_side(primary: Path, secondary: Path, label: str, out_path: Path) -> None:
    a = Image.open(primary).convert("RGB")
    b = Image.open(secondary).convert("RGB")
    height = max(a.height, b.height) + 60
    width = a.width + b.width
    canvas = Image.new("RGB", (width, height), (30, 34, 41))
    font = ImageFont.load_default()
    draw = ImageDraw.Draw(canvas)
    canvas.paste(a, (0, 40))
    canvas.paste(b, (a.width, 40))
    draw.text((16, 12), label, fill=(255, 255, 255), font=font)
    draw.text((a.width + 16, 12), "Fireship50", fill=(255, 255, 255), font=font)
    canvas.save(out_path, quality=90)


def metrics_for_storyboard(storyboard_path: Path) -> dict[str, Any]:
    storyboard = load_storyboard_json(storyboard_path)
    density_engine = EditorialDensityEngine()
    scenes = []
    interrupt_values = {value for value in InterruptType.__members__.values()}

    for scene in storyboard.scenes:
        scene_interrupts = [beat for beat in scene.micro_beats if beat in interrupt_values]
        score = density_engine.calculate_density_score(scene)
        scenes.append({
            "scene_id": scene.scene_id,
            "beat_role": scene.beat_role.value,
            "layers": len(scene.visual_layers or []),
            "micro_beats": len(scene.micro_beats or []),
            "interrupt_count": len(scene_interrupts),
            "static_proof_risk": any(issue["code"] == "static_proof_risk" for issue in density_engine.check_scene(scene)),
            "density_score": score,
        })

    return {
        "project_id": storyboard.project_id,
        "title": storyboard.title,
        "scene_count": len(storyboard.scenes),
        "scenes": scenes,
        "totals": {
            "layers": sum(s["layers"] for s in scenes),
            "micro_beats": sum(s["micro_beats"] for s in scenes),
            "interrupt_count": sum(s["interrupt_count"] for s in scenes),
            "mean_density_score": round(sum(s["density_score"] for s in scenes) / len(scenes), 3),
        },
    }


def main() -> None:
    baseline_contact = BASELINE_DIR / "contact_sheet.jpg"
    fireship_contact = FIRESHIP_DIR / "contact_sheet.jpg"
    combined_contact = OUTPUT_DIR / "day7_coffee_baseline_vs_fireship50_contact.jpg"
    make_side_by_side(baseline_contact, fireship_contact, "Baseline vs Fireship50", combined_contact)

    baseline_frames = [BASELINE_DIR / f"{idx:02d}_{name}_preview.jpg" for idx, name in enumerate(["hook", "shock", "turn"], start=1)]
    fireship_frames = [FIRESHIP_DIR / f"{idx:02d}_{name}_preview.jpg" for idx, name in enumerate(["hook", "shock", "turn"], start=1)]
    combine_images(baseline_frames, "Baseline review frames", OUTPUT_DIR / "day7_coffee_baseline_review_frames.jpg")
    combine_images(fireship_frames, "Fireship50 review frames", OUTPUT_DIR / "day7_coffee_fireship50_review_frames.jpg")

    baseline_metrics = metrics_for_storyboard(REPO_ROOT / "backend" / "day7_coffee_baseline_static_storyboard.json")
    fireship_metrics = metrics_for_storyboard(REPO_ROOT / "backend" / "day7_coffee_fireship50_storyboard.json")

    report = {
        "baseline": baseline_metrics,
        "fireship50": fireship_metrics,
        "baseline_qa_report": str(BASELINE_DIR / "qa_report.json"),
        "fireship50_qa_report": str(FIRESHIP_DIR / "qa_report.json"),
        "comparison_images": {
            "contact_sheet": str(combined_contact),
            "baseline_review_frames": str(OUTPUT_DIR / "day7_coffee_baseline_review_frames.jpg"),
            "fireship50_review_frames": str(OUTPUT_DIR / "day7_coffee_fireship50_review_frames.jpg"),
        },
    }
    report_path = OUTPUT_DIR / "day7_coffee_density_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(f"Created comparison assets under: {OUTPUT_DIR}")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
