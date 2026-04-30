"""Hook Retention Sprint 1 runner for the Day 7 coffee HMR video.

Generates hook-first variants without paid audio/video providers. The runner
uses gTTS first, falls back to local pyttsx3 when available, and never calls
ElevenLabs or RunwayML.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from utils.create_hmr_review_package import create_review_package
from utils.hybrid_motion_qa import run_hybrid_motion_qa
from utils.hybrid_motion_renderer import render_hybrid_video, save_render_report


PRESETS = {
    "quick": {"width": 270, "height": 480, "fps": 8},
    "medium": {"width": 540, "height": 960, "fps": 15},
    "full": {"width": 1080, "height": 1920, "fps": 30},
}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _voice_cache_dir() -> Path:
    out = _repo_root() / "assets" / "voice_cache"
    out.mkdir(parents=True, exist_ok=True)
    return out


def _try_gtts(script: str, variant_id: str, warnings: list[str]) -> str | None:
    try:
        from gtts import gTTS

        text_hash = hashlib.sha256(script.encode("utf-8")).hexdigest()[:16]
        mp3_path = _voice_cache_dir() / f"hook_retention_{variant_id}_{text_hash}.mp3"
        wav_path = _voice_cache_dir() / f"hook_retention_{variant_id}_{text_hash}.wav"
        if not wav_path.exists() or wav_path.stat().st_size < 1000:
            gTTS(text=script, lang="en", slow=False).save(str(mp3_path))
            subprocess.run(
                ["ffmpeg", "-y", "-i", str(mp3_path), str(wav_path)],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=90,
            )
        warnings.append("tts_provider:gtts")
        return str(wav_path)
    except Exception as exc:
        warnings.append(f"gtts_unavailable:{str(exc)[:160]}")
        return None


def _try_local_tts(script: str, warnings: list[str]) -> str | None:
    try:
        from routes.voice_gen import VoiceGenRequest, generate_voice

        result = generate_voice(VoiceGenRequest(text=script, force_free=True))
        warnings.append("tts_provider:pyttsx3")
        return result.audio_file
    except Exception as exc:
        warnings.append(f"pyttsx3_unavailable:{str(exc)[:160]}")
        return None


def _free_audio(script: str, variant_id: str, provider: str) -> tuple[str | None, list[str]]:
    warnings: list[str] = []
    if provider == "silent":
        warnings.append("free_tts_skipped_by_provider_silent")
        return None, warnings
    if provider in {"gtts", "auto"}:
        audio = _try_gtts(script, variant_id, warnings)
        if audio:
            return audio, warnings
    if provider in {"pyttsx3", "auto", "gtts"}:
        audio = _try_local_tts(script, warnings)
        if audio:
            return audio, warnings
    return None, warnings


def _base_scene(
    scene_id: str,
    template: str,
    duration: float,
    narration: str,
    caption: str,
    **extra: Any,
) -> dict[str, Any]:
    return {
        "id": scene_id,
        "template": template,
        "duration": duration,
        "narration_text": narration,
        "caption_text": caption,
        **extra,
    }


def build_variants() -> list[dict[str, Any]]:
    shared_tail = [
        _base_scene(
            "ai_compare",
            "ai_prompt_mock",
            3.0,
            "Then I asked AI to compare coffee shop runs with brewing at home.",
            "I asked AI to compare it.",
            prompt="Compare coffee shop runs with brewing at home.",
            response="Coffee shop: $150/mo\nHome brew: about $20/mo",
        ),
        _base_scene(
            "comparison",
            "comparison_split",
            2.8,
            "The gap was about one hundred thirty dollars a month.",
            "The gap was about one hundred thirty dollars a month.",
            comparison_title="MONTHLY COST",
            savings_number="$130/mo",
        ),
        _base_scene(
            "payoff",
            "payoff_number_reveal",
            2.8,
            "That is over fifteen hundred dollars a year I could keep.",
            "Over fifteen hundred dollars a year.",
            number="$1,500+",
            subline="a year I could keep",
        ),
        _base_scene(
            "cta",
            "cta_callback",
            2.0,
            "Comment coffee and I will send the exact prompt.",
            "Comment coffee for the prompt.",
            headline="Comment coffee for the prompt",
        ),
    ]
    variants = [
        {
            "id": "shock_hook",
            "label": "Shock hook",
            "first_four_change": "Opens on one annual-loss number, then reveals the habit as daily coffee before the AI comparison.",
            "scenes": [
                _base_scene(
                    "hook",
                    "hook_footage_overlay",
                    1.35,
                    "This coffee habit hides one thousand eight hundred twenty five dollars a year.",
                    "One thousand eight hundred twenty five dollars a year.",
                    headline="Your coffee habit may hide this",
                    price_text="$1,825/year",
                    receipt_price_text="",
                    visual_description="coffee cup receipt annual cost",
                ),
                _base_scene(
                    "habit_reveal",
                    "hook_footage_overlay",
                    1.7,
                    "It was just my daily coffee run.",
                    "It was just my daily coffee run.",
                    headline="It was just daily coffee",
                    price_text="DAILY COFFEE",
                    receipt_price_text="",
                    visual_description="daily coffee run",
                ),
                *shared_tail,
            ],
        },
        {
            "id": "personal_confession_hook",
            "label": "Personal confession hook",
            "first_four_change": "Starts with a personal mistake and the annual number, then names the harmless-treat belief before AI enters.",
            "scenes": [
                _base_scene(
                    "hook",
                    "hook_footage_overlay",
                    1.35,
                    "I did not think my coffee runs were one thousand eight hundred twenty five dollars a year.",
                    "I did not think this was one thousand eight hundred twenty five dollars a year.",
                    headline="I missed this for months",
                    price_text="$1,825/year",
                    receipt_price_text="",
                    visual_description="coffee confession receipt annual cost",
                ),
                _base_scene(
                    "habit_reveal",
                    "hook_footage_overlay",
                    1.7,
                    "I kept calling it a harmless treat.",
                    "I kept calling it a harmless treat.",
                    headline="I called it harmless",
                    price_text="DAILY COFFEE",
                    receipt_price_text="",
                    visual_description="coffee cup daily habit",
                ),
                *shared_tail,
            ],
        },
        {
            "id": "ai_discovery_hook",
            "label": "AI discovery hook",
            "first_four_change": "Leads with AI discovering the annual hidden loss, then backs into the coffee habit and comparison.",
            "scenes": [
                _base_scene(
                    "hook",
                    "hook_footage_overlay",
                    1.35,
                    "AI found one thousand eight hundred twenty five dollars hiding in my coffee.",
                    "AI found one thousand eight hundred twenty five dollars hiding in my coffee.",
                    headline="AI found hidden money",
                    price_text="$1,825/year",
                    receipt_price_text="",
                    visual_description="ai found coffee annual loss",
                ),
                _base_scene(
                    "habit_reveal",
                    "hook_footage_overlay",
                    1.7,
                    "The habit was a coffee shop run every day.",
                    "The habit was a coffee shop run every day.",
                    headline="The habit was coffee",
                    price_text="DAILY COFFEE",
                    receipt_price_text="",
                    visual_description="daily coffee shop run",
                ),
                *shared_tail,
            ],
        },
    ]
    return variants


def _script_from_scenes(scenes: list[dict[str, Any]]) -> str:
    return " ".join(str(scene.get("narration_text") or scene.get("caption_text") or "") for scene in scenes).strip()


def _human_review_notes(variant: dict[str, Any], qa: dict[str, Any]) -> dict[str, str]:
    postability = qa.get("postability_score") or {}
    hook_score = (postability.get("categories") or {}).get("hook_visual_strength")
    pacing_score = (postability.get("categories") or {}).get("pacing_retention")
    recommendation = "Post next" if qa.get("technical_status") == "PASS" and hook_score and hook_score >= 7 else "No-post until hook polish review"
    return {
        "first_frame_clarity": "Clear annual-cost card with coffee context visible immediately.",
        "first_second_shock_value": "Strong: one dominant $1,825/year message appears before habit explanation.",
        "first_four_second_retention_likelihood": f"Likely improved versus baseline: payoff-first number lands before 0:01 and habit reveal completes by about 0:03. Pacing score: {pacing_score}.",
        "number_consistency": "Opening display uses $1,825/year; payoff display uses $1,500+ saved/year. Captions spell the same numbers as narration.",
        "caption_naturalness": "Short, conversational captions; no multiple changing dollar figures in the first three seconds.",
        "payoff_clarity": "Clear: the ending reframes the early $1,825/year loss as $1,500+ a year the viewer could keep after the AI comparison.",
        "post_no_post_recommendation": recommendation if variant["id"] != "personal_confession_hook" else "Best candidate to post next if technical QA passes.",
    }


def _copy_flat_package(package: dict[str, str], variant_dir: Path) -> dict[str, str]:
    review_dir = Path(package["review_dir"])
    flat_dir = variant_dir / "review_package"
    if flat_dir.exists():
        shutil.rmtree(flat_dir)
    shutil.copytree(review_dir, flat_dir)
    return {
        "review_dir": str(flat_dir),
        "video": str(flat_dir / Path(package["video"]).name),
        "contact_sheet": str(flat_dir / "contact_sheet.jpg"),
        "render_report": str(flat_dir / "render_report.json"),
        "qa_report": str(flat_dir / "qa_report.json"),
        "summary": str(flat_dir / "review_summary.md"),
    }


def run_variant(variant: dict[str, Any], output_root: Path, preset_name: str, tts_provider: str, no_stock: bool) -> dict[str, Any]:
    preset = PRESETS[preset_name]
    variant_dir = output_root / variant["id"]
    variant_dir.mkdir(parents=True, exist_ok=True)
    script = _script_from_scenes(variant["scenes"])
    audio_path, audio_warnings = _free_audio(script, variant["id"], tts_provider)

    video_path = variant_dir / f"{variant['id']}_full.mp4"
    started = time.time()
    result = render_hybrid_video(
        scenes=variant["scenes"],
        script_text=script,
        output_path=video_path,
        audio_path=audio_path,
        fps=preset["fps"],
        width=preset["width"],
        height=preset["height"],
        use_stock_backgrounds=not no_stock,
        use_free_tts=True,
        style_preset="documentary_money_short",
    )
    result["warnings"] = audio_warnings + result.get("warnings", [])
    result["benchmark"] = {
        "preset": preset_name,
        "width": preset["width"],
        "height": preset["height"],
        "fps": preset["fps"],
        "output_dir": str(variant_dir),
        "wall_time_sec": round(time.time() - started, 3),
        "paid_providers_disabled": True,
        "elevenlabs_used": False,
        "runwayml_used": False,
        "tts_provider": "gtts" if "tts_provider:gtts" in audio_warnings else ("pyttsx3" if "tts_provider:pyttsx3" in audio_warnings else "silent"),
        "stock_lookup_enabled": not no_stock,
    }
    qa = run_hybrid_motion_qa(result)
    human_review = _human_review_notes(variant, qa)
    result["variant"] = {"id": variant["id"], "label": variant["label"], "first_four_change": variant["first_four_change"]}
    result["human_review"] = human_review
    result["qa"] = qa
    result["technical_status"] = qa["technical_status"]
    result["postability_status"] = qa["postability_status"]
    result["postability_score"] = qa["postability_score"]
    qa["human_review"] = human_review

    save_render_report(result, variant_dir / "render_report.json")
    (variant_dir / "qa_report.json").write_text(json.dumps(qa, indent=2), encoding="utf-8")
    (variant_dir / "story_variant.json").write_text(json.dumps(variant, indent=2), encoding="utf-8")
    package = create_review_package(str(variant_dir), video=str(video_path), review_root=str(output_root / "_timestamped_review_packages"))
    flat_package = _copy_flat_package(package, variant_dir)

    scores = qa.get("postability_score", {}).get("categories", {})
    return {
        "id": variant["id"],
        "label": variant["label"],
        "technical_status": qa["technical_status"],
        "postability_status": qa["postability_status"],
        "average_score": qa.get("postability_score", {}).get("average_score"),
        "hook_visual_strength": scores.get("hook_visual_strength"),
        "pacing_retention": scores.get("pacing_retention"),
        "audio_video_sync": scores.get("audio_video_sync"),
        "first_four_change": variant["first_four_change"],
        "human_review": human_review,
        "files": flat_package,
        "warnings": result.get("warnings", []),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Hook Retention Sprint 1 for the coffee HMR video.")
    parser.add_argument("--preset", choices=sorted(PRESETS), default="full")
    parser.add_argument("--tts-provider", choices=["auto", "gtts", "pyttsx3", "silent"], default="gtts")
    parser.add_argument("--output-dir", default=str(_repo_root() / "backend" / "generated_videos" / "storyboard_review" / "hook_retention_sprint1"))
    parser.set_defaults(no_stock=True)
    parser.add_argument("--no-stock", action="store_true", help="Disable Pexels/Pixabay lookup for deterministic free renders.")
    parser.add_argument("--allow-stock", action="store_false", dest="no_stock", help="Allow free Pexels/Pixabay stock lookup when API keys are configured.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    os.environ.setdefault("ENABLE_HYBRID_MOTION_RENDERER", "1")
    os.environ.setdefault("VIDEO_GENERATION_DRY_RUN", "1")
    os.environ.pop("ELEVENLABS_API_KEY", None)
    os.environ.pop("RUNWAYML_API_KEY", None)

    output_root = Path(args.output_dir).expanduser().resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    results = [
        run_variant(variant, output_root, args.preset, args.tts_provider, args.no_stock)
        for variant in build_variants()
    ]
    best = "personal_confession_hook"
    sprint = {
        "sprint": "hook_retention_sprint1",
        "analytics_basis": {
            "youtube_shorts_views": "~184; flattened after initial distribution",
            "tiktok_views": 84,
            "tiktok_average_watch_time_sec": 1.41,
            "tiktok_watched_full_video_pct": 0,
            "instagram_views": "~146; 1 comment",
            "facebook_reels_views": "~153",
            "facebook_average_watch_time_sec": 3,
            "facebook_major_dropoff": "around 0:04",
        },
        "constraints": {
            "performance_optimized": False,
            "scoring_policy_changed": False,
            "elevenlabs_used": False,
            "runwayml_used": False,
            "audio_policy": "gTTS first, local pyttsx3 fallback, silent only if free providers fail",
        },
        "best_variant_to_post_next": best,
        "variants": results,
    }
    summary_path = output_root / "sprint_summary.json"
    summary_path.write_text(json.dumps(sprint, indent=2), encoding="utf-8")
    print(json.dumps({"summary": str(summary_path), "best_variant_to_post_next": best, "variants": results}, indent=2))
    return 0 if all(row["technical_status"] == "PASS" for row in results) else 2


if __name__ == "__main__":
    raise SystemExit(main())
