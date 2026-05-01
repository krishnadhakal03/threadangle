"""UI-facing HMR review package and platform export workflow metadata."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

try:
    from .create_hmr_review_package import create_review_package
    from .hmr_artifact_manifest import assert_not_frozen_output
    from .hmr_platform_exports import PRESETS, build_ffmpeg_command, default_output_path
    from .hybrid_motion_qa import run_hybrid_motion_qa
    from .hybrid_motion_renderer import save_render_report
except ImportError:  # pragma: no cover - direct script execution fallback
    from create_hmr_review_package import create_review_package
    from hmr_artifact_manifest import assert_not_frozen_output
    from hmr_platform_exports import PRESETS, build_ffmpeg_command, default_output_path
    from hybrid_motion_qa import run_hybrid_motion_qa
    from hybrid_motion_renderer import save_render_report


STANDARD_PLATFORM_EXPORT_PRESETS = ("instagram_reels", "tiktok", "youtube_shorts")


def hmr_ui_run_dir(generated_root: str | Path, run_id: str) -> Path:
    return Path(generated_root).expanduser().resolve() / "hmr_ui_runs" / str(run_id)


def build_hmr_ui_artifact_paths(
    *,
    generated_root: str | Path,
    run_id: str,
    video_path: str | Path,
) -> dict[str, str]:
    """Return safe, predictable UI HMR artifact paths without writing files."""
    run_dir = hmr_ui_run_dir(generated_root, run_id)
    review_dir = run_dir / "review_package"
    export_dir = review_dir / "platform_exports"
    for path in (run_dir, review_dir, export_dir):
        assert_not_frozen_output(path)
    video = Path(video_path).expanduser().resolve()
    return {
        "run_dir": str(run_dir),
        "video": str(video),
        "render_report": str(run_dir / "render_report.json"),
        "qa_report": str(run_dir / "qa_report.json"),
        "story_candidate": str(run_dir / "story_candidate.json"),
        "review_package": str(review_dir),
        "manifest": str(review_dir / "manifest.json"),
        "platform_export_dir": str(export_dir),
    }


def build_hmr_platform_export_plan(
    *,
    video_path: str | Path,
    export_dir: str | Path,
    presets: tuple[str, ...] = STANDARD_PLATFORM_EXPORT_PRESETS,
) -> dict[str, dict[str, Any]]:
    """Build planned platform export paths and FFmpeg commands without transcoding."""
    plan: dict[str, dict[str, Any]] = {}
    for preset in presets:
        if preset not in PRESETS:
            raise ValueError(f"Unknown platform export preset: {preset}")
        output_path = default_output_path(video_path, preset, output_dir=export_dir)
        assert_not_frozen_output(output_path)
        plan[preset] = {
            "output": str(output_path),
            "command": build_ffmpeg_command(video_path, output_path, preset),
            "generated": False,
        }
    return plan


def build_hmr_ui_productization_metadata(
    *,
    generated_root: str | Path,
    run_id: str,
    video_path: str | Path,
) -> dict[str, Any]:
    """Build the UI HMR review/export workflow metadata without generating artifacts."""
    paths = build_hmr_ui_artifact_paths(
        generated_root=generated_root,
        run_id=run_id,
        video_path=video_path,
    )
    export_plan = build_hmr_platform_export_plan(
        video_path=video_path,
        export_dir=paths["platform_export_dir"],
    )
    return {
        "artifact_paths": paths,
        "platform_exports": export_plan,
        "review_package_status": "planned",
        "platform_export_status": "planned",
        "full_render_required": False,
    }


def materialize_hmr_ui_review_workflow(
    *,
    generated_root: str | Path,
    run_id: str,
    video_path: str | Path,
    render_result: dict[str, Any],
    script_text: str,
    scenes: list[dict[str, Any]],
) -> dict[str, Any]:
    """Persist render/QA artifacts and create a flat review package after UI HMR render."""
    metadata = build_hmr_ui_productization_metadata(
        generated_root=generated_root,
        run_id=run_id,
        video_path=video_path,
    )
    paths = metadata["artifact_paths"]
    run_dir = Path(paths["run_dir"])
    review_dir = Path(paths["review_package"])
    run_dir.mkdir(parents=True, exist_ok=True)
    assert_not_frozen_output(run_dir)
    assert_not_frozen_output(review_dir)

    qa_report = run_hybrid_motion_qa(render_result)
    render_result["qa"] = qa_report
    render_result["technical_status"] = qa_report["technical_status"]
    render_result["postability_status"] = qa_report["postability_status"]
    render_result["postability_score"] = qa_report["postability_score"]
    render_result["human_posting_gate"] = qa_report.get("human_posting_gate")

    save_render_report(render_result, paths["render_report"])
    Path(paths["qa_report"]).write_text(json.dumps(qa_report, indent=2) + "\n", encoding="utf-8")
    Path(paths["story_candidate"]).write_text(
        json.dumps({"script": script_text, "scenes": scenes}, indent=2) + "\n",
        encoding="utf-8",
    )

    package = create_review_package(str(run_dir), video=str(video_path), review_root=str(run_dir / "_timestamped_review_packages"))
    source_review_dir = Path(package["review_dir"])
    if review_dir.exists():
        shutil.rmtree(review_dir)
    shutil.copytree(source_review_dir, review_dir)
    metadata["artifact_paths"].update(
        {
            "review_package": str(review_dir),
            "manifest": str(review_dir / "manifest.json"),
            "summary": str(review_dir / "review_summary.md"),
            "contact_sheet": str(review_dir / "contact_sheet.jpg"),
        }
    )
    metadata["review_package_status"] = "created"
    metadata["platform_exports"] = build_hmr_platform_export_plan(
        video_path=video_path,
        export_dir=paths["platform_export_dir"],
    )
    return metadata
