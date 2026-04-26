from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw

from .asset_resolver import resolve_assets
from .formatting import cover, font, format_spec
from .proof_inserts import render_generated_card, render_proof_image
from .schema import Storyboard, VisualSource


def run(cmd: list[str], label: str) -> subprocess.CompletedProcess:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"{label} failed:\n{result.stderr[-3000:]}")
    return result


def _scene_frame(storyboard: Storyboard, resolved, t: float = 0.75) -> Image.Image:
    spec = format_spec(storyboard.format)
    width, height = spec["width"], spec["height"]
    scene = resolved.scene
    asset = resolved.decision.asset_path
    if scene.visual_source in {VisualSource.user_image, VisualSource.proof_screenshot} and asset and asset.exists():
        img = render_proof_image(scene, asset, width, height, t, scene.duration)
    elif scene.visual_source == VisualSource.generated_card:
        img = render_generated_card(scene, width, height)
    elif asset and asset.exists() and asset.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}:
        img = cover(Image.open(asset).convert("RGB"), width, height)
    else:
        img = render_generated_card(scene, width, height)
        draw = ImageDraw.Draw(img)
        draw.text((70, height - 180), f"Provider: {resolved.decision.provider}", font=font(34, True), fill=(16, 185, 129))
    return img


def generate_scene_previews(storyboard: Storyboard, repo_root: Path, review_dir: Path) -> dict:
    if review_dir.exists():
        shutil.rmtree(review_dir)
    review_dir.mkdir(parents=True, exist_ok=True)
    resolved_assets = resolve_assets(storyboard, repo_root)
    manifest = {"project_id": storyboard.project_id, "scenes": []}
    previews: list[Path] = []
    for idx, resolved in enumerate(resolved_assets, start=1):
        scene = resolved.scene
        preview = review_dir / f"{idx:02d}_{scene.scene_id}_preview.jpg"
        _scene_frame(storyboard, resolved).save(preview, quality=92)
        previews.append(preview)
        manifest["scenes"].append(
            {
                "scene_id": scene.scene_id,
                "narration_text": scene.narration_text,
                "caption_text": scene.caption_text or scene.narration_text,
                "visual_source": scene.visual_source.value,
                "asset_path": str(resolved.decision.asset_path) if resolved.decision.asset_path else None,
                "locked": scene.lock_visual,
                "duration": scene.duration,
                "preview_path": str(preview),
                "provider": resolved.decision.provider,
                "provider_status": resolved.decision.status.value,
                "provider_reason": resolved.decision.reason,
                "privacy_warning": (scene.visual_source.value in {"user_image", "user_video", "proof_screenshot"} and not scene.privacy_reviewed),
            }
        )
    contact_sheet = review_dir / "contact_sheet.jpg"
    make_contact_sheet(previews, contact_sheet, storyboard.format.value)
    manifest["contact_sheet"] = str(contact_sheet)
    manifest_path = review_dir / "review_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    manifest["manifest_path"] = str(manifest_path)
    return manifest


def make_contact_sheet(previews: list[Path], out: Path, label: str) -> Path:
    thumbs = [Image.open(path).convert("RGB").resize((270, 480)) for path in previews]
    sheet = Image.new("RGB", (270 * len(thumbs), 540), (245, 247, 250))
    draw = ImageDraw.Draw(sheet)
    for idx, thumb in enumerate(thumbs):
        x = idx * 270
        sheet.paste(thumb, (x, 0))
        draw.text((x + 16, 496), f"{idx + 1}", font=font(28, True), fill=(15, 23, 42))
    draw.text((18, 18), label, font=font(22, True), fill=(15, 23, 42))
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out, quality=92)
    return out
