"""Colab-ready Hybrid Motion Renderer benchmark.

This runner intentionally avoids ElevenLabs, RunwayML, and paid image/audio
APIs. It uses offline/free TTS when available and otherwise renders a silent
MP4 with an explicit warning in the report.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from utils.hybrid_motion_qa import run_hybrid_motion_qa
from utils.hybrid_motion_renderer import render_hybrid_video, save_render_report
from utils.run_hybrid_motion_poc import SCRIPT, build_day8_scenes


PRESETS = {
    "quick": {"width": 270, "height": 480, "fps": 6},
    "medium": {"width": 540, "height": 960, "fps": 15},
    "full": {"width": 1080, "height": 1920, "fps": 30},
}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _default_output_dir() -> Path:
    return _repo_root() / "backend" / "generated_videos" / "storyboard_review" / "hybrid_motion_colab_benchmark"


def _try_free_tts(script: str) -> tuple[str | None, list[str]]:
    warnings: list[str] = []
    try:
        from routes.voice_gen import VoiceGenRequest, generate_voice

        result = generate_voice(VoiceGenRequest(text=script, force_free=True))
        return result.audio_file, warnings
    except Exception as exc:
        warnings.append(f"free_tts_unavailable:{str(exc)[:160]}")
        return None, warnings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Threadforge HMR Colab benchmark.")
    parser.add_argument("--preset", choices=sorted(PRESETS), default="quick", help="Benchmark size preset.")
    parser.add_argument("--width", type=int, default=None, help="Output width. Overrides preset.")
    parser.add_argument("--height", type=int, default=None, help="Output height. Overrides preset.")
    parser.add_argument("--fps", type=int, default=None, help="Frames per second. Overrides preset.")
    parser.add_argument("--output-dir", default=str(_default_output_dir()), help="Directory for MP4 and reports.")
    parser.add_argument("--no-stock", action="store_true", help="Disable Pexels/Pixabay stock lookup and force local animated fallbacks.")
    parser.add_argument("--silent", action="store_true", help="Skip free/local TTS and render with generated silent audio.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    preset = PRESETS[args.preset]
    width = int(args.width or preset["width"])
    height = int(args.height or preset["height"])
    fps = int(args.fps or preset["fps"])

    os.environ.setdefault("ENABLE_HYBRID_MOTION_RENDERER", "1")
    os.environ.setdefault("VIDEO_GENERATION_DRY_RUN", "1")

    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    stem = f"hmr_benchmark_{width}x{height}_{fps}fps_{args.preset}"
    video_path = output_dir / f"{stem}.mp4"
    report_path = output_dir / "render_report.json"
    qa_path = output_dir / "qa_report.json"
    media_mix_path = output_dir / "media_mix_report.json"

    audio_path = None
    audio_warnings: list[str] = []
    if args.silent:
        audio_warnings.append("free_tts_skipped_by_cli_silent_flag")
    else:
        audio_path, audio_warnings = _try_free_tts(SCRIPT)

    started = time.time()
    result = render_hybrid_video(
        scenes=build_day8_scenes(),
        script_text=SCRIPT,
        output_path=video_path,
        audio_path=audio_path,
        fps=fps,
        width=width,
        height=height,
        use_stock_backgrounds=not args.no_stock,
        use_free_tts=True,
        style_preset="documentary_money_short",
    )
    result["warnings"] = audio_warnings + result.get("warnings", [])
    result["benchmark"] = {
        "preset": args.preset,
        "width": width,
        "height": height,
        "fps": fps,
        "output_dir": str(output_dir),
        "wall_time_sec": round(time.time() - started, 3),
        "paid_providers_disabled": True,
        "elevenlabs_used": False,
        "runwayml_used": False,
        "stock_lookup_enabled": not args.no_stock,
    }

    qa = run_hybrid_motion_qa(result)
    result["qa"] = qa

    save_render_report(result, report_path)
    qa_path.write_text(json.dumps(qa, indent=2), encoding="utf-8")
    media_mix_path.write_text(json.dumps(result.get("media_mix") or {}, indent=2), encoding="utf-8")

    print(json.dumps({
        "video_path": str(video_path),
        "render_report": str(report_path),
        "qa_report": str(qa_path),
        "media_mix_report": str(media_mix_path),
        "qa_status": qa["status"],
        "media_mix": result.get("media_mix"),
        "warnings": result.get("warnings"),
        "benchmark": result["benchmark"],
    }, indent=2))
    return 0 if qa["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
