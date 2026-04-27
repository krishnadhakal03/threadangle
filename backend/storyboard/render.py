from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw

from .asset_resolver import resolve_assets
from .audio_caption import estimate_wpm, regenerate_audio_only, regenerate_captions_only, restitch_with_locked_visuals
from .editorial_motion import apply_motion, create_micro_beats
from .multi_layer import apply_multi_layer_composition
from .semantic_motion import enhance_scene_with_semantic_motion
from .formatting import cover, font, format_spec
from .preview import generate_scene_previews
from .proof_inserts import render_generated_card, render_proof_image
from .qa import run_qa
from .render_modes import assert_provider_allowed
from .schema import Storyboard, VisualSource


def run(cmd: list[str], label: str) -> subprocess.CompletedProcess:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"{label} failed:\n{result.stderr[-3000:]}")
    return result


def ffmpeg_path(path: Path) -> str:
    return str(path.resolve()).replace("\\", "/")


def render_scene_clip(storyboard: Storyboard, resolved, raw_dir: Path) -> Path:
    spec = format_spec(storyboard.format)
    width, height, fps = spec["width"], spec["height"], spec["fps"]
    scene = resolved.scene
    enhance_scene_with_semantic_motion(scene)
    micro_beats = create_micro_beats(scene.micro_beats, scene.duration)
    out = raw_dir / f"{scene.scene_id}.mp4"
    asset = resolved.decision.asset_path
    if scene.visual_source == VisualSource.user_video and asset and asset.exists():
        vf = f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}"
        run(["ffmpeg", "-y", "-i", str(asset), "-t", f"{scene.duration:.2f}", "-vf", vf, "-r", str(fps), "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)], "render user video")
        return out

    frame_dir = raw_dir / f"frames_{scene.scene_id}"
    if frame_dir.exists():
        shutil.rmtree(frame_dir)
    frame_dir.mkdir(parents=True)
    total_frames = int(round(scene.duration * fps))
    for frame in range(total_frames):
        t = frame / fps
        if scene.visual_source in {VisualSource.user_image, VisualSource.proof_screenshot} and asset and asset.exists():
            img = render_proof_image(scene, asset, width, height, t, scene.duration)
        elif scene.visual_source == VisualSource.generated_card:
            img = render_generated_card(scene, width, height, t, scene.duration)
        elif asset and asset.exists() and asset.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}:
            img = cover(Image.open(asset).convert("RGB"), width, height)
        else:
            img = render_generated_card(scene, width, height, t, scene.duration)
            draw = ImageDraw.Draw(img)
            draw.text((70, height - 170), f"{resolved.decision.provider}: {resolved.decision.reason or 'MVP fallback'}", font=font(34, True), fill=(16, 185, 129))
        img = apply_motion(img, t, scene.duration, micro_beats)
        img = apply_multi_layer_composition(scene, img, t)
        img.save(frame_dir / f"frame_{frame:04d}.jpg", quality=92)
    run(["ffmpeg", "-y", "-framerate", str(fps), "-i", str(frame_dir / "frame_%04d.jpg"), "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p", "-r", str(fps), str(out)], "render scene")
    return out


def render_locked_visuals(storyboard: Storyboard, repo_root: Path, raw_dir: Path) -> Path:
    assert_provider_allowed(storyboard, "local_tts", "draft render")
    if raw_dir.exists():
        shutil.rmtree(raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)
    clips = [render_scene_clip(storyboard, resolved, raw_dir) for resolved in resolve_assets(storyboard, repo_root)]
    concat = raw_dir / "concat.txt"
    concat.write_text("\n".join(f"file '{ffmpeg_path(path)}'" for path in clips), encoding="utf-8")
    silent = raw_dir / f"{storyboard.project_id}_silent.mp4"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat), "-c", "copy", str(silent)], "concat storyboard visuals")
    return silent


def render_draft_video(storyboard: Storyboard, repo_root: Path, output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    review_dir = output_dir / "review"
    raw_dir = output_dir / "raw"
    work_dir = output_dir / "audio"
    manifest = generate_scene_previews(storyboard, repo_root, review_dir)
    qa_report = run_qa(storyboard, repo_root, review_dir / "qa_report.json", manifest)
    silent = render_locked_visuals(storyboard, repo_root, raw_dir)
    audio, timings, provider = regenerate_audio_only(storyboard, work_dir)
    ass_file, caption_events = regenerate_captions_only(storyboard, timings, work_dir / f"{storyboard.project_id}.ass")
    final = output_dir / f"{storyboard.project_id}.mp4"
    restitch_with_locked_visuals(storyboard, silent, audio, ass_file, final)
    result = {
        "project_id": storyboard.project_id,
        "final_video": str(final),
        "silent_video": str(silent),
        "audio_provider": provider,
        "average_narration_wpm": round(estimate_wpm(storyboard, timings), 1),
        "caption_events": len(caption_events),
        "contact_sheet": manifest["contact_sheet"],
        "review_manifest": manifest["manifest_path"],
        "qa_report": str(review_dir / "qa_report.json"),
        "qa_issue_count": qa_report["issue_count"],
    }
    (output_dir / "render_result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def regenerate_audio_captions_and_restitch(storyboard: Storyboard, silent_video: Path, output_dir: Path) -> dict:
    work_dir = output_dir / "audio_regen"
    audio, timings, provider = regenerate_audio_only(storyboard, work_dir)
    ass_file, caption_events = regenerate_captions_only(storyboard, timings, work_dir / f"{storyboard.project_id}_regen.ass")
    final = output_dir / f"{storyboard.project_id}_audio_regen.mp4"
    restitch_with_locked_visuals(storyboard, silent_video, audio, ass_file, final)
    return {
        "final_video": str(final),
        "audio_provider": provider,
        "caption_events": len(caption_events),
        "average_narration_wpm": round(estimate_wpm(storyboard, timings), 1),
    }
