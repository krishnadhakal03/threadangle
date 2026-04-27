from __future__ import annotations

import argparse
import json
from pathlib import Path

from .render import regenerate_audio_captions_and_restitch, render_draft_video, render_locked_visuals
from .schema import ProviderStatus, VisualSource, load_storyboard, save_storyboard


REPO_ROOT = Path(__file__).resolve().parents[2]
GENERATED_ROOT = REPO_ROOT / "backend" / "generated_videos" / "storyboard_review"


def cmd_preview(args: argparse.Namespace) -> None:
    from .preview import generate_scene_previews
    from .qa import run_qa

    storyboard = load_storyboard(args.storyboard)
    out = GENERATED_ROOT / storyboard.project_id / "review"
    manifest = generate_scene_previews(storyboard, REPO_ROOT, out)
    report = run_qa(storyboard, REPO_ROOT, out / "qa_report.json", manifest)
    print(json.dumps({"manifest": manifest["manifest_path"], "contact_sheet": manifest["contact_sheet"], "qa_report": str(out / "qa_report.json"), "qa_issue_count": report["issue_count"]}, indent=2))


def cmd_render(args: argparse.Namespace) -> None:
    storyboard = load_storyboard(args.storyboard)
    result = render_draft_video(storyboard, REPO_ROOT, GENERATED_ROOT / storyboard.project_id)
    print(json.dumps(result, indent=2))


def cmd_replace(args: argparse.Namespace) -> None:
    storyboard = load_storyboard(args.storyboard)
    for scene in storyboard.scenes:
        if scene.scene_id == args.scene_id:
            scene.asset_path = args.asset_path
            if args.visual_source:
                scene.visual_source = VisualSource(args.visual_source)
            scene.provider_status = ProviderStatus.pending
            break
    else:
        raise SystemExit(f"scene not found: {args.scene_id}")
    save_storyboard(storyboard, args.out or args.storyboard)
    print(json.dumps({"scene_id": args.scene_id, "asset_path": args.asset_path, "storyboard": str(args.out or args.storyboard)}, indent=2))


def cmd_lock(args: argparse.Namespace) -> None:
    storyboard = load_storyboard(args.storyboard)
    for scene in storyboard.scenes:
        if scene.scene_id == args.scene_id:
            scene.lock_visual = True
            scene.privacy_reviewed = True
            break
    else:
        raise SystemExit(f"scene not found: {args.scene_id}")
    save_storyboard(storyboard, args.out or args.storyboard)
    print(json.dumps({"scene_id": args.scene_id, "lock_visual": True, "storyboard": str(args.out or args.storyboard)}, indent=2))


def cmd_unlock(args: argparse.Namespace) -> None:
    storyboard = load_storyboard(args.storyboard)
    for scene in storyboard.scenes:
        if scene.scene_id == args.scene_id:
            scene.lock_visual = False
            break
    else:
        raise SystemExit(f"scene not found: {args.scene_id}")
    save_storyboard(storyboard, args.out or args.storyboard)
    print(json.dumps({"scene_id": args.scene_id, "lock_visual": False, "storyboard": str(args.out or args.storyboard)}, indent=2))


def cmd_captions_regen(args: argparse.Namespace) -> None:
    # Placeholder - would regenerate captions only
    print("Captions regeneration not yet implemented")


def cmd_audio_regen(args: argparse.Namespace) -> None:
    storyboard = load_storyboard(args.storyboard)
    out_dir = GENERATED_ROOT / storyboard.project_id
    silent = Path(args.silent) if args.silent else render_locked_visuals(storyboard, REPO_ROOT, out_dir / "raw")
    result = regenerate_audio_captions_and_restitch(storyboard, silent, out_dir)
    print(json.dumps(result, indent=2))


def cmd_qa_report(args: argparse.Namespace) -> None:
    from .qa import run_qa
    storyboard = load_storyboard(args.storyboard)
    out = GENERATED_ROOT / storyboard.project_id / "qa"
    out.mkdir(parents=True, exist_ok=True)
    report = run_qa(storyboard, REPO_ROOT, out / "qa_report.json")
    print(json.dumps({"qa_report": str(out / "qa_report.json"), "issue_count": report["issue_count"]}, indent=2))


def cmd_generate_storyboard(args: argparse.Namespace) -> None:
    from .compiler import save_compiled_storyboard
    output_path = Path(args.output) if args.output else Path(f"generated_{args.topic.lower().replace(' ', '_')}.json")
    result_path = save_compiled_storyboard(
        topic=args.topic,
        output_path=output_path,
        niche=args.niche,
        proof_numbers=args.proof_numbers.split(',') if args.proof_numbers else None
    )
    print(json.dumps({"storyboard": str(result_path), "topic": args.topic}, indent=2))


def cmd_hook_preview(args: argparse.Namespace) -> None:
    from .hook_preview import preview_hooks_for_storyboard
    output_dir = Path(args.output) if args.output else Path("hook_previews")
    previews = preview_hooks_for_storyboard(Path(args.storyboard), output_dir)
    print(json.dumps({"previews": [str(p) for p in previews]}, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Storyboard-first video MVP CLI")
    sub = parser.add_subparsers(required=True)
    p = sub.add_parser("preview")
    p.add_argument("storyboard")
    p.set_defaults(func=cmd_preview)
    p = sub.add_parser("render")
    p.add_argument("storyboard")
    p.set_defaults(func=cmd_render)
    p = sub.add_parser("replace")
    p.add_argument("storyboard")
    p.add_argument("scene_id")
    p.add_argument("asset_path")
    p.add_argument("--visual-source")
    p.add_argument("--out")
    p.set_defaults(func=cmd_replace)
    p = sub.add_parser("lock")
    p.add_argument("storyboard")
    p.add_argument("scene_id")
    p.add_argument("--out")
    p.set_defaults(func=cmd_lock)
    p = sub.add_parser("unlock")
    p.add_argument("storyboard")
    p.add_argument("scene_id")
    p.add_argument("--out")
    p.set_defaults(func=cmd_unlock)
    p = sub.add_parser("audio-regen")
    p.add_argument("storyboard")
    p.add_argument("--silent")
    p.set_defaults(func=cmd_audio_regen)
    p = sub.add_parser("captions-regen")
    p.add_argument("storyboard")
    p.set_defaults(func=cmd_captions_regen)
    p = sub.add_parser("qa-report")
    p.add_argument("storyboard")
    p.set_defaults(func=cmd_qa_report)
    p = sub.add_parser("generate-storyboard")
    p.add_argument("topic")
    p.add_argument("--output")
    p.add_argument("--niche", default="personal finance")
    p.add_argument("--proof-numbers")
    p.set_defaults(func=cmd_generate_storyboard)
    p = sub.add_parser("hook-preview")
    p.add_argument("storyboard")
    p.add_argument("--output")
    p.set_defaults(func=cmd_hook_preview)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
