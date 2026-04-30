"""Visual Realism Sprint 1 runner for HMR money-saving content.

Creates one full-resolution grocery receipt / inflation savings candidate
without paid audio or video providers. Uses gTTS first, local/free fallback
when available, and never calls ElevenLabs or RunwayML.
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
from utils.check_hmr_asset_readiness import check_hmr_asset_readiness
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


def _try_gtts(script: str, warnings: list[str]) -> str | None:
    try:
        from gtts import gTTS

        text_hash = hashlib.sha256(script.encode("utf-8")).hexdigest()[:16]
        mp3_path = _voice_cache_dir() / f"visual_realism_grocery_{text_hash}.mp3"
        wav_path = _voice_cache_dir() / f"visual_realism_grocery_{text_hash}.wav"
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


def _free_audio(script: str, provider: str) -> tuple[str | None, list[str]]:
    warnings: list[str] = []
    if provider == "silent":
        warnings.append("free_tts_skipped_by_provider_silent")
        return None, warnings
    if provider in {"gtts", "auto"}:
        audio = _try_gtts(script, warnings)
        if audio:
            return audio, warnings
    if provider in {"pyttsx3", "auto", "gtts"}:
        audio = _try_local_tts(script, warnings)
        if audio:
            return audio, warnings
    return None, warnings


def _scene(scene_id: str, template: str, duration: float, narration: str, caption: str, **extra: Any) -> dict[str, Any]:
    return {
        "id": scene_id,
        "template": template,
        "duration": duration,
        "narration_text": narration,
        "caption_text": caption,
        **extra,
    }


def build_grocery_scenes() -> list[dict[str, Any]]:
    return [
        _scene(
            "hook",
            "grocery_receipt_hook",
            1.45,
            "I found a forty dollar a week leak in my grocery receipt.",
            "I found a forty dollar a week leak.",
            headline="I found a $40/week grocery leak",
            price_text="$2,080/year",
            subline="$40/week hiding in receipts",
            store_name="FRESH MART RECEIPT",
            receipt_rows=[
                ("snack packs", "$11.80"),
                ("brand cereal", "$8.49"),
                ("drinks", "$13.20"),
                ("checkout extras", "$6.51"),
            ],
            visual_description="realistic grocery receipt bag cart annual savings leak",
        ),
        _scene(
            "reveal",
            "grocery_reveal_scene",
            2.1,
            "It came from the same repeat items, impulse extras, and brand swaps every week.",
            "Repeat items and impulse extras.",
            headline="Same cart. Quiet leak.",
            leak_rows=[
                ("Impulse extras", "$18"),
                ("Brand swaps", "$13"),
                ("Repeat snacks", "$9"),
            ],
            visual_description="grocery bag cart phone weekly cart breakdown",
        ),
        _scene(
            "ai_compare",
            "grocery_ai_comparison",
            3.2,
            "So I asked AI to scan the receipt and find cheaper swaps I would actually buy.",
            "AI scanned the receipt.",
            prompt="Find cheaper swaps for these repeat grocery items.",
            swap_rows=[
                ("Brand cereal", "$8.49", "store brand", "$4.19"),
                ("Snack packs", "$11.80", "bulk bag", "$6.40"),
                ("Drinks", "$13.20", "home pack", "$7.10"),
            ],
            savings_number="$40/week",
            visual_description="screen capture style AI grocery receipt comparison",
        ),
        _scene(
            "payoff",
            "grocery_savings_payoff",
            2.9,
            "That is about two thousand eighty dollars a year back from one boring receipt audit.",
            "About two thousand eighty dollars a year.",
            number="$2,080",
            subline="possible yearly savings",
            visual_description="realistic phone savings estimate grocery receipt",
        ),
        _scene(
            "cta",
            "cta_callback",
            2.1,
            "Comment grocery and I will send the prompt.",
            "Comment grocery for the prompt.",
            headline="Comment grocery for the prompt",
        ),
    ]


def _script_from_scenes(scenes: list[dict[str, Any]]) -> str:
    return " ".join(str(scene.get("narration_text") or scene.get("caption_text") or "") for scene in scenes).strip()


def _human_review_notes(qa: dict[str, Any], render_result: dict[str, Any]) -> dict[str, str]:
    postability = qa.get("postability_score") or {}
    scores = postability.get("categories") or {}
    ready = qa.get("technical_status") == "PASS" and qa.get("postability_status") in {"PASS", "STRONG_PASS"}
    gate = render_result.get("visual_realism_human_gate") or {}
    reports = render_result.get("scene_reports") or []
    ai_compare = next((row for row in reports if row.get("scene_id") == "ai_compare"), {})
    payoff = next((row for row in reports if row.get("scene_id") == "payoff"), {})
    hook = next((row for row in reports if row.get("scene_id") == "hook"), {})
    reveal = next((row for row in reports if row.get("scene_id") == "reveal"), {})
    ai_capture_used = ai_compare.get("resolved_asset_type") == "playwright_capture" and ai_compare.get("asset_resolution_status") == "resolved"
    payoff_capture_used = payoff.get("resolved_asset_type") == "playwright_capture" and payoff.get("asset_resolution_status") == "resolved"
    hook_reveal_resolved = all(
        row.get("resolved_asset_type") in {"stock_footage", "stock_image", "local_asset"}
        and row.get("asset_resolution_status") == "resolved"
        for row in (hook, reveal)
    )
    drawn_placeholders = [
        str(row.get("scene_id"))
        for row in reports
        if not row.get("resolved_asset_type") and ((row.get("scene_asset_strategy") or {}).get("visual_medium") != "motion_template")
    ]
    human_ready = ready and hook_reveal_resolved
    return {
        "visual_realism_score": "8/10" if hook_reveal_resolved else "6/10",
        "object_credibility": "Hook/reveal use stock footage when available; AI comparison and payoff use local HTML/Playwright captures when available. CTA may remain a template fallback until a later slice.",
        "story_object_connection": "Every major object is tied to the script: receipt leak, repeat cart items, AI swap panel, yearly savings phone estimate, and grocery CTA.",
        "scene_asset_strategy_used": "Yes. Slice A attaches HMR scene asset strategy rows so review can see which scenes should move to stock, capture, local assets, or templates.",
        "planned_real_sources": str(gate.get("planned_real_sources")),
        "resolved_real_assets": str(gate.get("resolved_real_assets")),
        "drawn_placeholder_risk": str(gate.get("drawn_placeholder_risk")),
        "ai_compare_real_capture": "Yes, ai_compare used a real local Playwright HTML screenshot." if ai_capture_used else f"No, ai_compare fell back to the drawn template: {ai_compare.get('asset_resolution_status')}",
        "payoff_real_capture": "Yes, payoff used a local Playwright savings-dashboard screenshot." if payoff_capture_used else f"No, payoff fell back to the template: {payoff.get('asset_resolution_status')}",
        "visual_realism_vs_previous": (
            "Improved versus Slice C: payoff now uses a Playwright savings-dashboard capture instead of the PIL phone/card template."
            if payoff_capture_used
            else "Improved versus Slice B for the first four seconds if hook/reveal resolve, but payoff still uses the PIL/template version."
            if hook_reveal_resolved
            else "Not improved versus Slice B for the first four seconds: hook/reveal still fall back to motion templates because stock providers or local assets did not resolve."
        ),
        "playwright_adapter_recommendation": "Promote Playwright as a standard adapter for UI/proof scenes if human review accepts the payoff dashboard; it should remain separate from real-world footage scenes.",
        "first_four_second_realism": (
            "Credible enough for posting review: hook and reveal use real resolved assets with minimal overlays."
            if hook_reveal_resolved
            else f"Blocked for visual-realism breakout: hook={hook.get('asset_resolution_status')}; reveal={reveal.get('asset_resolution_status')}."
        ),
        "drawn_placeholders_remaining": ", ".join(drawn_placeholders) if drawn_placeholders else "None among scenes planned for real sources.",
        "first_frame_clarity": "The first frame shows one grocery receipt loss number and a grocery-bag/cart context.",
        "first_second_clarity": "Strong: $2,080/year appears immediately as the yearly version of the $40/week leak.",
        "first_four_second_retention_likelihood": f"Likely stronger than coffee visuals: one loss number lands first, then repeat grocery items reveal before the AI panel. Hook score: {scores.get('hook_visual_strength')}; pacing score: {scores.get('pacing_retention')}.",
        "post_no_post_recommendation": "Ready for today's post" if human_ready else "Do not post yet: first-four-second real assets are unresolved",
    }


def _copy_flat_package(package: dict[str, str], output_dir: Path) -> dict[str, str]:
    review_dir = Path(package["review_dir"])
    flat_dir = output_dir / "review_package"
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Visual Realism Sprint 1 for HMR grocery content.")
    parser.add_argument("--preset", choices=sorted(PRESETS), default="full")
    parser.add_argument("--tts-provider", choices=["auto", "gtts", "pyttsx3", "silent"], default="gtts")
    parser.add_argument("--output-dir", default=str(_repo_root() / "backend" / "generated_videos" / "storyboard_review" / "visual_realism_sprint1_grocery"))
    parser.add_argument("--sprint-name", default="visual_realism_sprint1")
    parser.add_argument("--issue", default="#2 Visual Realism Sprint 1")
    parser.add_argument("--skip-asset-readiness", action="store_true", help="Allow full render even when first-four-second real assets are missing.")
    return parser.parse_args()


def _requires_asset_readiness(args: argparse.Namespace) -> bool:
    issue = str(args.issue or "").lower()
    sprint = str(args.sprint_name or "").lower()
    return args.preset == "full" and ("#3" in issue or "scene_intelligence" in sprint)


def _write_blocked_readiness_summary(output_dir: Path, args: argparse.Namespace, readiness: dict[str, Any]) -> Path:
    summary = {
        "sprint": args.sprint_name,
        "issue": args.issue,
        "status": "BLOCKED",
        "reason": "Posting blocked by missing first-four-second real assets.",
        "next_steps": [
            "Add Pexels/Pixabay keys, or",
            "Add local hook/reveal files under assets/hmr_local/grocery/.",
        ],
        "readiness": readiness,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "asset_readiness_blocked.json"
    path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return path


def main() -> int:
    args = parse_args()
    os.environ.setdefault("ENABLE_HYBRID_MOTION_RENDERER", "1")
    os.environ.setdefault("VIDEO_GENERATION_DRY_RUN", "1")
    os.environ.pop("ELEVENLABS_API_KEY", None)
    os.environ.pop("RUNWAYML_API_KEY", None)

    preset = PRESETS[args.preset]
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    readiness = check_hmr_asset_readiness()
    readiness_path = output_dir / "asset_readiness.json"
    readiness_path.write_text(json.dumps(readiness, indent=2), encoding="utf-8")
    if _requires_asset_readiness(args) and not args.skip_asset_readiness and readiness.get("status") != "PASS":
        _write_blocked_readiness_summary(output_dir, args, readiness)
        return 3
    scenes = build_grocery_scenes()
    script = _script_from_scenes(scenes)
    audio_path, audio_warnings = _free_audio(script, args.tts_provider)
    stock_lookup_enabled = bool(readiness.get("status") == "PASS" and _requires_asset_readiness(args))

    video_path = output_dir / "visual_realism_sprint1_grocery_full.mp4"
    started = time.time()
    result = render_hybrid_video(
        scenes=scenes,
        script_text=script,
        output_path=video_path,
        audio_path=audio_path,
        fps=preset["fps"],
        width=preset["width"],
        height=preset["height"],
        use_stock_backgrounds=stock_lookup_enabled,
        use_free_tts=True,
        style_preset="documentary_money_short",
    )
    result["warnings"] = audio_warnings + result.get("warnings", [])
    result["benchmark"] = {
        "preset": args.preset,
        "width": preset["width"],
        "height": preset["height"],
        "fps": preset["fps"],
        "output_dir": str(output_dir),
        "wall_time_sec": round(time.time() - started, 3),
        "paid_providers_disabled": True,
        "elevenlabs_used": False,
        "runwayml_used": False,
        "tts_provider": "gtts" if "tts_provider:gtts" in audio_warnings else ("pyttsx3" if "tts_provider:pyttsx3" in audio_warnings else "silent"),
        "stock_lookup_enabled": stock_lookup_enabled,
        "asset_readiness": readiness,
    }
    qa = run_hybrid_motion_qa(result)
    human_review = _human_review_notes(qa, result)
    result["sprint"] = {
        "issue": args.issue,
        "name": args.sprint_name,
        "topic": "Grocery receipt / inflation savings leak",
        "hook": "I found a $40/week leak in my grocery receipt.",
    }
    result["human_review"] = human_review
    result["qa"] = qa
    result["technical_status"] = qa["technical_status"]
    result["postability_status"] = qa["postability_status"]
    result["postability_score"] = qa["postability_score"]
    qa["human_review"] = human_review

    save_render_report(result, output_dir / "render_report.json")
    (output_dir / "qa_report.json").write_text(json.dumps(qa, indent=2), encoding="utf-8")
    (output_dir / "story_candidate.json").write_text(json.dumps({"script": script, "scenes": scenes}, indent=2), encoding="utf-8")
    package = create_review_package(str(output_dir), video=str(video_path), review_root=str(output_dir / "_timestamped_review_packages"))
    flat_package = _copy_flat_package(package, output_dir)

    summary = {
        "sprint": args.sprint_name,
        "issue": args.issue,
        "constraints": {
            "performance_optimized": False,
            "scoring_policy_changed": False,
            "elevenlabs_used": False,
            "runwayml_used": False,
            "audio_policy": "gTTS first, local pyttsx3 fallback, silent only if free providers fail",
        },
        "technical_status": qa["technical_status"],
        "postability_status": qa["postability_status"],
        "postability_score": qa["postability_score"],
        "human_review": human_review,
        "files": flat_package,
        "warnings": result.get("warnings", []),
    }
    summary_path = output_dir / "sprint_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({"summary": str(summary_path), **summary}, indent=2))
    return 0 if qa["technical_status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
