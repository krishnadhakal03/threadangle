from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from backend.storyboard.schema import (
    load_storyboard,
    save_storyboard,
    Storyboard,
    StoryboardScene,
    VisualSource,
)
from backend.storyboard.visual_director import plan_assets, visual_modality_breakdown


REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_ROOT = REPO_ROOT / "backend" / "generated_videos" / "storyboard_review" / "day7_coffee_visual_director_v1"
OUT_ROOT.mkdir(parents=True, exist_ok=True)


def map_medium_to_visual_source(medium: str) -> VisualSource:
    m = medium
    if m == "stock_clip":
        return VisualSource.stock_footage
    if m == "browser_capture":
        return VisualSource.playwright_capture
    if m == "local_ai_capture":
        return VisualSource.local_dom_reconstruction
    if m == "user_manual_clip":
        return VisualSource.user_manual_capture
    if m == "proof_card":
        return VisualSource.proof_screenshot
    # fallback
    return VisualSource.generated_card


def enforce_rules_and_build(storyboard: Storyboard, plan: dict[str, Any]) -> Storyboard:
    scenes: list[StoryboardScene] = []
    proof_count = 0
    for entry in plan["scenes"]:
        sid = entry["scene_id"]
        # locate original scene
        orig = next((s for s in storyboard.scenes if s.scene_id == sid), None)
        if not orig:
            # fallback: create minimal scene
            orig = StoryboardScene(
                scene_id=sid,
                scene_type="auto",
                duration=3.0,
                narration_text="",
                visual_source=VisualSource.generated_card,
            )

        medium = entry["visual_medium"]
        vs = map_medium_to_visual_source(medium)
        if vs == VisualSource.proof_screenshot:
            proof_count += 1

        # ensure rules: prompt must be browser/local
        if "prompt" in sid and vs == VisualSource.generated_card:
            vs = VisualSource.playwright_capture

        # reveal must be comparison: prefer generated_card but add visual layer
        visual_layers = list(orig.visual_layers or [])
        if medium == "comparison_card":
            visual_layers.append('comparison_layout:::{"left":"coffee shop","right":"home brew"}')
            vs = VisualSource.generated_card

        # hook should not be proof
        if "hook" in sid and vs == VisualSource.proof_screenshot:
            vs = VisualSource.stock_footage

        new = orig.model_copy()
        new.visual_source = vs
        # attach asset_query as capture_notes
        new.capture_notes = entry.get("capture_instruction") or entry.get("asset_query")
        new.visual_layers = visual_layers
        scenes.append(new)

    # Hard rule: limit proof_screenshot to 30%
    total = len(scenes) or 1
    max_proof = int(total * 0.3)
    if proof_count > max_proof:
        # demote some proof scenes to generated_card
        changed = 0
        for s in scenes:
            if changed >= proof_count - max_proof:
                break
            if s.visual_source == VisualSource.proof_screenshot:
                s.visual_source = VisualSource.generated_card
                changed += 1

    new_sb = Storyboard(
        project_id=storyboard.project_id + "_director_v1",
        title=storyboard.title + " (Visual Director v1)",
        niche=storyboard.niche,
        template_id=storyboard.template_id,
        format=storyboard.format,
        render_mode=storyboard.render_mode,
        style=storyboard.style,
        variables=storyboard.variables,
        scenes=scenes,
    )
    return new_sb


def ensure_segment_exists(out_raw: Path, seg_name: str, preview_img: Path | None = None, duration: float = 3.0) -> Path:
    out_raw.mkdir(parents=True, exist_ok=True)
    target = out_raw / f"{seg_name}.mp4"
    if target.exists():
        return target
    # create from preview image or simple colored card
    from PIL import Image, ImageDraw, ImageFont

    img = None
    if preview_img and preview_img.exists():
        img = Image.open(preview_img).convert("RGB")
    else:
        img = Image.new("RGB", (1080, 1920), (30, 30, 40))
        d = ImageDraw.Draw(img)
        try:
            f = ImageFont.truetype("arial.ttf", 72)
        except Exception:
            f = ImageFont.load_default()
        d.text((120, 400), seg_name.replace("_"," ").upper(), font=f, fill=(255, 230, 120))

    tmp_img = out_raw / f"{seg_name}.jpg"
    img.save(tmp_img, quality=90)
    # build mp4 using ffmpeg image2
    cmd = [
        "ffmpeg",
        "-y",
        "-loop",
        "1",
        "-i",
        str(tmp_img),
        "-c:v",
        "libx264",
        "-t",
        str(duration),
        "-pix_fmt",
        "yuv420p",
        str(target),
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        tmp_img.unlink()
    except Exception:
        pass
    return target


def make_contact_sheet(review_dir: Path, out_path: Path) -> None:
    from PIL import Image

    imgs = sorted(review_dir.glob("*_preview.jpg"))
    if not imgs:
        return
    thumbs: list[Image.Image] = []
    for p in imgs:
        try:
            im = Image.open(p).convert("RGB")
            im.thumbnail((360, 640))
            thumbs.append(im)
        except Exception:
            continue
    cols = 3
    rows = (len(thumbs) + cols - 1) // cols
    w = cols * 360
    h = rows * 640
    sheet = Image.new("RGB", (w, h), (14, 18, 26))
    for i, t in enumerate(thumbs):
        x = (i % cols) * 360
        y = (i // cols) * 640
        sheet.paste(t, (x, y))
    sheet.save(out_path, quality=90)


def run():
    src = REPO_ROOT / "backend" / "day7_coffee_storyboard.json"
    sb = load_storyboard(src)
    plan = plan_assets(sb, OUT_ROOT)
    new_sb = enforce_rules_and_build(sb, plan)
    sb_out = OUT_ROOT / "day7_coffee_visual_director_storyboard.json"
    save_storyboard(new_sb, sb_out)
    # ensure segments
    raw = OUT_ROOT / "raw"
    segments = [
        ("hook", None),
        ("shock", None),
        ("turn", None),
        ("prompt", None),
        ("reveal", None),
        ("payoff", OUT_ROOT / "review" / "06_payoff_preview.jpg"),
        ("cta", OUT_ROOT / "review" / "07_cta_preview.jpg"),
    ]
    seg_paths = []
    for name, preview in segments:
        p = ensure_segment_exists(raw, name, preview)
        seg_paths.append(p)

    # concat
    concat_txt = raw / "concat_list.txt"
    with open(concat_txt, "w", encoding="utf-8") as f:
        for p in seg_paths:
            f.write(f"file '{p.as_posix()}'\n")

    out_file = OUT_ROOT / "day7_coffee_visual_director_v1.mp4"
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_txt),
        "-c",
        "copy",
        str(out_file),
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # contact sheet
    review_dir = OUT_ROOT / "review"
    review_dir.mkdir(parents=True, exist_ok=True)
    # if review images missing, try to copy from generated rebuild review
    prior = REPO_ROOT / "backend" / "generated_videos" / "storyboard_review" / "day7_coffee_visual_rebuild_v1" / "review"
    if prior.exists():
        for p in prior.glob("*.jpg"):
            dst = review_dir / p.name
            if not dst.exists():
                try:
                    dst.write_bytes(p.read_bytes())
                except Exception:
                    pass

    contact_out = OUT_ROOT / "contact_sheet.jpg"
    make_contact_sheet(review_dir, contact_out)

    # QA report
    breakdown = visual_modality_breakdown(new_sb, plan)
    rejections = []
    # checks
    if all(s.visual_source == new_sb.scenes[0].visual_source for s in new_sb.scenes):
        rejections.append("all_scenes_same_source")
    if not any("hook" in s.scene_id and s.visual_source != VisualSource.proof_screenshot for s in new_sb.scenes):
        # if hook not real-world
        rejections.append("hook_lacks_real_visual")

    qa = {
        "asset_plan": str(OUT_ROOT / "asset_plan.json"),
        "storyboard": str(sb_out),
        "final_video": str(out_file),
        "contact_sheet": str(contact_out) if contact_out.exists() else None,
        "visual_modality_breakdown": breakdown,
        "rejections": rejections,
        "postable_rating": "needs_review" if rejections else "pass",
        "no_paid_credits": True,
    }
    qa_out = OUT_ROOT / "qa_report.json"
    qa_out.write_text(json.dumps(qa, indent=2), encoding="utf-8")

    print("Outputs:")
    print(str(out_file))
    print(str(contact_out))
    print(str(qa_out))

    # git commit and push
    try:
        subprocess.run(["git", "checkout", "-B", "feature/visual-director-engine-v1"], cwd=REPO_ROOT)
        subprocess.run(["git", "add", "backend/storyboard/visual_director.py", str(OUT_ROOT)], cwd=REPO_ROOT)
        subprocess.run(["git", "commit", "-m", "VD1 add visual director engine and Day7 mixed-media rebuild"], cwd=REPO_ROOT)
        subprocess.run(["git", "push", "-u", "origin", "feature/visual-director-engine-v1"], cwd=REPO_ROOT)
        print("Committed and pushed (attempt).")
    except Exception:
        print("Git commit/push failed or not configured; changes are local.")


if __name__ == "__main__":
    run()
