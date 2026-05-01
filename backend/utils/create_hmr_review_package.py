"""Create a human-review package for a Hybrid Motion Renderer output."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from .hmr_artifact_manifest import assert_not_frozen_output, build_manifest, write_manifest
    from .hmr_posting_gate import compute_human_posting_gate
except ImportError:  # pragma: no cover - direct script execution fallback
    from hmr_artifact_manifest import assert_not_frozen_output, build_manifest, write_manifest
    from hmr_posting_gate import compute_human_posting_gate


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _find_video(output_dir: Path, explicit: str | None) -> Path:
    if explicit:
        path = Path(explicit).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"Video not found: {path}")
        return path
    candidates = sorted(output_dir.glob("hmr_benchmark_*_full.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        candidates = sorted(output_dir.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        raise FileNotFoundError(f"No MP4 found under {output_dir}")
    return candidates[0]


def _run_ffmpeg_contact_sheet(video_path: Path, out_path: Path) -> None:
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_path),
        "-vf",
        "fps=1/4,scale=270:480,tile=4x2",
        "-frames:v",
        "1",
        "-update",
        "1",
        str(out_path),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=90)


def _format_scores(scores: dict[str, Any]) -> str:
    lines = []
    for key, value in scores.items():
        lines.append(f"- `{key}`: {value}")
    return "\n".join(lines)


def _write_summary(
    review_dir: Path,
    video_path: Path,
    contact_sheet: Path,
    render_report: dict[str, Any],
    qa_report: dict[str, Any],
) -> Path:
    postability = qa_report.get("postability_score") or {}
    scores = postability.get("categories") or {}
    benchmark = render_report.get("benchmark") or {}
    profile = render_report.get("render_profile") or {}
    profile_rows = profile.get("per_template") or []
    top_templates = "\n".join(
        f"- `{row.get('template')}`: {row.get('total_sec')}s total, {row.get('sec_per_frame')}s/frame"
        for row in profile_rows[:4]
    ) or "- Not available"
    recommendations = postability.get("recommendations") or []
    recommendation_lines = "\n".join(f"- {item}" for item in recommendations) if recommendations else "- None"
    human_review = render_report.get("human_review") or qa_report.get("human_review") or render_report.get("visual_realism_human_gate") or {}
    human_posting_gate = compute_human_posting_gate(
        render_report=render_report,
        qa_report=qa_report,
        human_review=human_review,
    )
    final_recommendation = human_review.get("post_no_post_recommendation") or (
        "Post" if qa_report.get("postability_status") in {"PASS", "STRONG_PASS"} else "Manual review before posting"
    )
    human_review_lines = "\n".join(
        f"- {label}: {human_review.get(key, '')}"
        for key, label in (
            ("visual_realism_score", "Visual realism score"),
            ("object_credibility", "Object credibility"),
            ("story_object_connection", "Story-object connection"),
            ("scene_asset_strategy_used", "Scene asset strategy used"),
            ("planned_real_sources", "Planned real sources"),
            ("resolved_real_assets", "Resolved real assets"),
            ("drawn_placeholder_risk", "Drawn placeholder risk"),
            ("ai_compare_real_capture", "AI compare real capture"),
            ("payoff_real_capture", "Payoff real capture"),
            ("visual_realism_vs_previous", "Visual realism versus previous"),
            ("first_four_second_realism", "First-four-second realism"),
            ("drawn_placeholders_remaining", "Drawn placeholders remaining"),
            ("playwright_adapter_recommendation", "Playwright adapter recommendation"),
            ("playwright_visible_interaction", "Playwright visible interaction"),
            ("playwright_proof_motion", "Playwright proof motion"),
            ("playwright_visual_credibility_delta", "Playwright visual credibility delta"),
            ("hook_clarity", "Hook clarity"),
            ("visible_playwright_interaction", "Visible Playwright interaction"),
            ("resolved_real_assets_count", "Resolved real assets count"),
            ("caption_readability", "Caption readability"),
            ("first_frame_clarity", "First-frame clarity"),
            ("first_second_clarity", "First-second clarity"),
            ("first_second_shock_value", "First-second shock value"),
            ("first_frame_style", "First-frame style"),
            ("first_three_seconds_strategy", "First-three-second strategy"),
            ("first_four_second_retention_likelihood", "First-four-second retention likelihood"),
            ("number_consistency", "Number consistency"),
            ("caption_naturalness", "Caption naturalness"),
            ("payoff_clarity", "Payoff clarity"),
            ("post_no_post_recommendation", "Post/no-post recommendation"),
        )
        if human_review.get(key)
    ) or "- Pending human review"
    strategy_rows = render_report.get("scene_asset_strategy") or [
        row.get("scene_asset_strategy")
        for row in (render_report.get("scene_reports") or [])
        if row.get("scene_asset_strategy")
    ]
    strategy_lines = "\n".join(
        "- `{scene_id}`: `{medium}` / `{role}`; queries: {queries}; fallback: {fallback}".format(
            scene_id=row.get("scene_id"),
            medium=row.get("visual_medium"),
            role=row.get("asset_role"),
            queries=", ".join(f"`{query}`" for query in (row.get("query_candidates") or [])[:2]) or "`none`",
            fallback=" -> ".join(str(item) for item in (row.get("fallback_order") or [])),
        )
        for row in strategy_rows
    ) or "- No scene asset strategy attached"
    scene_reports = render_report.get("scene_reports") or []
    pattern_plan = render_report.get("pattern_interrupt_plan") or {}
    pattern_debug = pattern_plan.get("debug") or {}
    pattern_lines = (
        f"- Planned interrupts: `{pattern_debug.get('interrupt_count', 0)}` across `{pattern_debug.get('scene_count', 0)}` scenes"
        if pattern_plan
        else "- No pattern interrupt plan attached"
    )
    resolution_lines = "\n".join(
        "- `{scene_id}`: `{asset_type}` via `{provider}`; status: `{status}`; fallback: `{fallback}`; query: `{query}`; path: `{path}`; motion: `{motion}`; steps: {steps}; visible interaction: `{visible}`".format(
            scene_id=row.get("scene_id"),
            asset_type=row.get("resolved_asset_type"),
            provider=row.get("resolved_asset_provider"),
            status=row.get("asset_resolution_status"),
            fallback=row.get("fallback_used"),
            query=row.get("query_used"),
            path=Path(str(row.get("resolved_asset_path"))).name if row.get("resolved_asset_path") else "",
            motion=row.get("playwright_motion_mode") or "",
            steps=", ".join(f"`{step}`" for step in (row.get("capture_steps") or [])) or "`none`",
            visible=row.get("visible_interaction"),
        )
        for row in scene_reports
    ) or "- No scene asset resolution metadata attached"

    summary = f"""# HMR Human Review Package

Generated: {datetime.now().isoformat(timespec="seconds")}

## Files

- Video: `{video_path.name}`
- Contact sheet: `{contact_sheet.name}`
- Render report: `render_report.json`
- QA report: `qa_report.json`

## QA

- Technical status: `{qa_report.get("technical_status")}`
- Postability status: `{qa_report.get("postability_status")}`
- Human posting gate: `{human_posting_gate}`
- Average score: `{postability.get("average_score")}`
- Preset: `{benchmark.get("preset")}`
- Resolution/FPS: `{benchmark.get("width")}x{benchmark.get("height")} @ {benchmark.get("fps")}fps`
- Render time: `{benchmark.get("wall_time_sec")}s`

## Scores

{_format_scores(scores)}

## Recommendations

{recommendation_lines}

## Visual Strategy

{strategy_lines}

## Pattern Interrupts

{pattern_lines}

## Asset Resolution

{resolution_lines}

## Profiling

- Total profile wall time: `{profile.get("total_wall_sec")}s`
- Frame count: `{profile.get("frame_count")}`
- Template composition: `{profile.get("frame_template_composition_sec")}s`
- Caption composition: `{profile.get("caption_composition_sec")}s`
- Writer writes: `{profile.get("writer_write_sec")}s`
- Audio muxing: `{profile.get("mux_audio_sec")}s`

Top templates:

{top_templates}

## Human Review Checklist

- [ ] First 2 seconds hook is clear, thumb-stopping, and understandable without context.
- [ ] Captions are readable on mobile and do not cover important numbers.
- [ ] Caption phrasing does not feel semantically awkward or misleading.
- [ ] Payoff visual density feels exciting rather than cluttered.
- [ ] Overall motion and layout feel platform-native, not like a benchmark render.
- [ ] Audio cadence feels aligned with scene changes and captions.
- [ ] Post/no-post recommendation: `{final_recommendation}`

## Human Review Notes

{human_review_lines}

## Reviewer Notes

- First 2 seconds hook:
- Caption readability:
- Caption semantic awkwardness:
- Payoff visual density:
- Platform-native feel:
- Final post/no-post decision:
"""
    path = review_dir / "review_summary.md"
    path.write_text(summary, encoding="utf-8")
    return path


def create_review_package(output_dir: str, video: str | None = None, review_root: str | None = None) -> dict[str, str]:
    source_dir = Path(output_dir).expanduser().resolve()
    assert_not_frozen_output(source_dir)
    render_report_path = source_dir / "render_report.json"
    qa_report_path = source_dir / "qa_report.json"
    if not render_report_path.exists():
        raise FileNotFoundError(f"Missing render report: {render_report_path}")
    if not qa_report_path.exists():
        raise FileNotFoundError(f"Missing QA report: {qa_report_path}")

    video_path = _find_video(source_dir, video)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    root = Path(review_root).expanduser().resolve() if review_root else source_dir / "review_packages"
    assert_not_frozen_output(root)
    review_dir = root / f"{video_path.stem}_{stamp}"
    assert_not_frozen_output(review_dir)
    review_dir.mkdir(parents=True, exist_ok=True)

    copied_render = review_dir / "render_report.json"
    copied_qa = review_dir / "qa_report.json"
    shutil.copy2(render_report_path, copied_render)
    shutil.copy2(qa_report_path, copied_qa)
    copied_video = review_dir / video_path.name
    shutil.copy2(video_path, copied_video)

    contact_sheet = review_dir / "contact_sheet.jpg"
    _run_ffmpeg_contact_sheet(copied_video, contact_sheet)
    render_report = _load_json(copied_render)
    qa_report = _load_json(copied_qa)
    summary = _write_summary(
        review_dir,
        copied_video,
        contact_sheet,
        render_report,
        qa_report,
    )
    scenes = render_report.get("scene_reports") or []
    first_scene = scenes[0] if scenes else {}
    manifest = write_manifest(
        review_dir,
        build_manifest(
            topic=str(render_report.get("topic") or source_dir.name),
            hook=str(first_scene.get("headline") or first_scene.get("caption_text") or ""),
            video_path=copied_video,
            review_package_path=review_dir,
            render_report=render_report,
            qa_report=qa_report,
            human_posting_gate=compute_human_posting_gate(render_report=render_report, qa_report=qa_report),
            frozen=False,
        ),
    )

    return {
        "review_dir": str(review_dir),
        "video": str(copied_video),
        "contact_sheet": str(contact_sheet),
        "render_report": str(copied_render),
        "qa_report": str(copied_qa),
        "summary": str(summary),
        "manifest": str(manifest),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a human-review package for an HMR render.")
    parser.add_argument("--output-dir", required=True, help="Directory containing render_report.json and qa_report.json.")
    parser.add_argument("--video", default=None, help="Optional explicit video path. Defaults to newest MP4 in output-dir.")
    parser.add_argument("--review-root", default=None, help="Optional directory for review packages.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    print(json.dumps(create_review_package(args.output_dir, video=args.video, review_root=args.review_root), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
