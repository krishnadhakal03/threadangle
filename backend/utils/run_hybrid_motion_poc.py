"""Day8 Hybrid Motion Renderer POC CLI.

No ElevenLabs, no RunwayML, no paid image/audio APIs. Output is written under
backend/generated_videos/storyboard_review/hybrid_motion_poc/ (gitignored).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from utils.hybrid_motion_qa import run_hybrid_motion_qa
from utils.hybrid_motion_renderer import render_hybrid_video, save_render_report


SCRIPT = (
    "I was spending five dollars a day on coffee and calling it a small treat. "
    "That small habit was one hundred fifty dollars a month. "
    "So I asked AI to compare coffee shop runs with brewing at home. "
    "Coffee shop was one hundred fifty. Home brew was about twenty. "
    "That is over fifteen hundred dollars a year from one small habit. "
    "Comment coffee and I will send the prompt."
)


def _try_free_tts(script: str, out_dir: Path) -> tuple[str | None, list[str]]:
    warnings: list[str] = []
    try:
        from routes.voice_gen import VoiceGenRequest, generate_voice

        result = generate_voice(VoiceGenRequest(text=script, force_free=True))
        return result.audio_file, warnings
    except Exception as exc:
        warnings.append(f"free_tts_unavailable:{str(exc)[:120]}")
        return None, warnings


def build_day8_scenes() -> list[dict]:
    return [
        {
            "id": "hook",
            "template": "hook_footage_overlay",
            "scene_type": "hook",
            "duration": 2.6,
            "headline": "I called $5 coffee a small treat",
            "caption_text": "I was spending five dollars a day on coffee",
            "visual_description": "vertical coffee cup cafe counter payment",
        },
        {
            "id": "shock_math",
            "template": "money_shock_math",
            "scene_type": "shock",
            "duration": 2.7,
            "monthly_number": "$150/mo",
            "formula": "$5 x 30 = $150/mo",
            "caption_text": "That small habit was one hundred fifty dollars a month",
            "visual_description": "receipt payment coffee math",
        },
        {
            "id": "ai_prompt",
            "template": "ai_prompt_mock",
            "scene_type": "prompt",
            "duration": 3.2,
            "prompt": "Compare coffee shop runs with brewing at home.",
            "response": "Coffee shop: $150/mo\nHome brew: about $20/mo",
            "caption_text": "So I asked AI to compare the habit",
        },
        {
            "id": "comparison",
            "template": "comparison_split",
            "scene_type": "comparison",
            "duration": 2.8,
            "comparison_title": "MONTHLY COST",
            "savings_number": "$130/mo",
            "caption_text": "Coffee shop was one fifty home brew about twenty",
        },
        {
            "id": "payoff",
            "template": "payoff_number_reveal",
            "scene_type": "payoff",
            "duration": 2.8,
            "number": "$1,500+",
            "subline": "a year from one small habit",
            "caption_text": "Over fifteen hundred dollars a year",
        },
        {
            "id": "cta",
            "template": "cta_callback",
            "scene_type": "cta",
            "duration": 2.4,
            "headline": "Comment coffee for the prompt",
            "caption_text": "Comment coffee and I will send the prompt",
        },
    ]


def main() -> int:
    os.environ.setdefault("ENABLE_HYBRID_MOTION_RENDERER", "1")
    os.environ.setdefault("VIDEO_GENERATION_DRY_RUN", "1")

    repo_root = Path(__file__).resolve().parents[2]
    out_dir = repo_root / "backend" / "generated_videos" / "storyboard_review" / "hybrid_motion_poc"
    out_dir.mkdir(parents=True, exist_ok=True)
    video_path = out_dir / "day8_hybrid_motion_poc_v1.mp4"

    audio_path, audio_warnings = _try_free_tts(SCRIPT, out_dir)
    result = render_hybrid_video(
        scenes=build_day8_scenes(),
        script_text=SCRIPT,
        output_path=video_path,
        audio_path=audio_path,
        fps=int(os.getenv("HMR_POC_FPS", "6")),
        width=int(os.getenv("HMR_POC_WIDTH", "270")),
        height=int(os.getenv("HMR_POC_HEIGHT", "480")),
        use_stock_backgrounds=True,
        use_free_tts=True,
        style_preset="documentary_money_short",
    )
    result["warnings"] = audio_warnings + result.get("warnings", [])
    qa = run_hybrid_motion_qa(result)
    result["qa"] = qa
    result["technical_status"] = qa["technical_status"]
    result["postability_status"] = qa["postability_status"]
    result["postability_score"] = qa["postability_score"]

    save_render_report(result, out_dir / "day8_hybrid_motion_poc_v1_report.json")
    (out_dir / "day8_hybrid_motion_poc_v1_qa.json").write_text(json.dumps(qa, indent=2), encoding="utf-8")

    print(json.dumps({
        "video_path": result["video_path"],
        "qa_status": qa["technical_status"],
        "technical_status": qa["technical_status"],
        "postability_status": qa["postability_status"],
        "postability_score": qa["postability_score"],
        "media_mix": result["media_mix"],
        "warnings": result["warnings"],
    }, indent=2))
    return 0 if qa["technical_status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
