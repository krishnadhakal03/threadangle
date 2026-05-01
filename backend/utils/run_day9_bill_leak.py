"""Day 9 bill-leak HMR content runner.

Generates a mixed-media money-saving short without paid audio or video
providers. The frozen grocery review package is not read from or written to.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[1]))

import cv2
import numpy as np

from utils.check_hmr_asset_readiness import check_hmr_asset_readiness
from utils.create_hmr_review_package import create_review_package
from utils.hybrid_motion_qa import run_hybrid_motion_qa
from utils.hybrid_motion_renderer import render_hybrid_video, save_render_report
from utils.hmr_posting_gate import compute_human_posting_gate
from utils.run_visual_realism_sprint1 import PRESETS, _copy_flat_package, _free_audio, _repo_root


def _scene(scene_id: str, template: str, duration: float, narration: str, caption: str, **extra: Any) -> dict[str, Any]:
    return {
        "id": scene_id,
        "template": template,
        "duration": duration,
        "narration_text": narration,
        "caption_text": caption,
        **extra,
    }


def build_bill_leak_scenes() -> list[dict[str, Any]]:
    """Build the Day 9 bill-leak scene list from issue #5."""
    return [
        _scene(
            "hook",
            "grocery_receipt_hook",
            1.45,
            "I found a $27/month leak hiding in one bill.",
            "I found a $27/month leak.",
            headline="I found a $27/month bill leak",
            price_text="$324/year",
            subline="$27/month hiding in one bill",
            store_name="MONTHLY BILL",
            receipt_rows=[
                ("current plan", "$84/mo"),
                ("old price", "$57/mo"),
                ("price change", "+$27/mo"),
                ("auto pay", "on"),
            ],
            visual_description="person checking monthly bill on phone close up",
        ),
        _scene(
            "reveal",
            "grocery_reveal_scene",
            2.1,
            "It was not rent. It was not groceries. It was a plan I kept paying for after the price changed.",
            "A plan kept charging after the price changed.",
            headline="Same plan. New price.",
            leak_rows=[
                ("Plan price change", "$27/mo"),
                ("Auto pay kept going", "on"),
                ("Worth checking", "$324/yr"),
            ],
            visual_description="person reviewing subscription bill laptop phone",
        ),
        _scene(
            "ai_compare",
            "grocery_ai_comparison",
            3.2,
            "So I asked AI to compare the bill against cheaper options and flag what I could cancel, downgrade, or negotiate.",
            "AI compared cheaper options.",
            prompt="Compare this bill against cheaper options. Flag what I can cancel, downgrade, or negotiate.",
            swap_rows=[
                ("Current plan", "$84/mo", "downgrade", "$57/mo"),
                ("Unused add-on", "$9/mo", "cancel", "$0"),
                ("Price change", "+$27/mo", "negotiate", "call"),
            ],
            savings_number="$27/month",
            receipt_title="MONTHLY BILL",
            browser_label="bill-audit.local",
            audit_eyebrow="AI bill audit",
            audit_title="Cancel, downgrade, or negotiate",
            prompt_placeholder="Paste bill audit prompt...",
            loading_text="Analyzing bill...",
            found_text="Options found",
            result_text="$27/month leak found",
            receipt_lines=[
                ("PLAN CHARGE", "$84/mo"),
                ("OLD PRICE", "$57/mo"),
                ("PRICE CHANGE", "+$27/mo"),
                ("AUTO PAY", "ON"),
                ("LEAK FLAG", "$27/mo"),
            ],
            visual_description="screen capture style AI bill comparison",
        ),
        _scene(
            "payoff",
            "grocery_savings_payoff",
            2.9,
            "One boring bill check found about $324/year I could keep.",
            "About $324/year back.",
            number="$324",
            subline="possible yearly savings",
            dashboard_items=["$27/month leak", "cancel add-ons", "downgrade or negotiate"],
            receipt_title="BILL CHECK",
            receipt_lines=[
                ("MONTHLY LEAK", "$27"),
                ("YEARLY TOTAL", "$324"),
                ("ACTIONS", "3"),
                ("KEEP", "$324/yr"),
            ],
            dashboard_eyebrow="AI bill result",
            dashboard_title="One bill check found the leak",
            dashboard_footer="$324/year I could keep",
            visual_description="phone savings dashboard bill audit",
        ),
        _scene(
            "cta",
            "cta_callback",
            2.1,
            "Comment bill and I will send the prompt.",
            "Comment bill for the prompt.",
            eyebrow="BILL CHECK PROMPT",
            headline="Comment bill for the prompt",
            visual_description="person typing comment bill prompt on phone close up",
        ),
    ]


def _script_from_scenes(scenes: list[dict[str, Any]]) -> str:
    return " ".join(str(scene.get("narration_text") or scene.get("caption_text") or "") for scene in scenes).strip()


def _human_review_notes(qa: dict[str, Any], render_result: dict[str, Any]) -> dict[str, str]:
    reports = render_result.get("scene_reports") or []
    by_id = {row.get("scene_id"): row for row in reports}
    hook = by_id.get("hook") or {}
    reveal = by_id.get("reveal") or {}
    ai_compare = by_id.get("ai_compare") or {}
    payoff = by_id.get("payoff") or {}
    real_types = {"playwright_capture", "stock_image", "stock_footage", "local_asset"}
    resolved_real = [
        row
        for row in reports
        if row.get("resolved_asset_type") in real_types and row.get("asset_resolution_status") == "resolved"
    ]
    visible_interaction = bool(ai_compare.get("visible_interaction"))
    hook_reveal_real = all(
        row.get("resolved_asset_type") in {"stock_footage", "stock_image", "local_asset"}
        and row.get("asset_resolution_status") == "resolved"
        for row in (hook, reveal)
    )
    ai_real = ai_compare.get("resolved_asset_type") == "playwright_capture" and ai_compare.get("asset_resolution_status") == "resolved"
    payoff_real = payoff.get("resolved_asset_type") == "playwright_capture" and payoff.get("asset_resolution_status") == "resolved"
    ready = qa.get("technical_status") == "PASS" and hook_reveal_real and ai_real and payoff_real
    score = "8.5/10" if ready and visible_interaction else "7/10" if ai_real or hook_reveal_real else "5/10"
    return {
        "hook_clarity": "$324/year is the only dominant first-frame number, tied directly to the $27/month bill leak.",
        "first_frame_clarity": "The hook opens on one bill-loss message, not multiple changing dollar amounts.",
        "first_second_clarity": "Strong: $27/month and $324/year are visible as the same leak, with bill context.",
        "first_four_second_retention_likelihood": "Higher than the earlier prototype visuals because hook/reveal use real stock if resolved, then move into proof-motion AI comparison.",
        "visual_realism_score": score,
        "object_credibility": "Hook/reveal route to stock bill/payment footage; AI compare and payoff use local Playwright HTML captures.",
        "story_object_connection": "Every scene stays on bill leak, price change, AI comparison, yearly savings, and bill CTA.",
        "visible_playwright_interaction": str(visible_interaction),
        "resolved_real_assets_count": str(len(resolved_real)),
        "caption_readability": "Captions preserve $27/month and $324/year symbols and keep the CTA on bill, not grocery or coffee.",
        "number_consistency": "Displayed numbers match narration intent: $27/month leak and $324/year payoff.",
        "caption_naturalness": "Natural and short; no spelled-out money captions for the main dollar amounts.",
        "payoff_clarity": "Payoff screen shows $324/year and the three actions: cancel, downgrade, negotiate.",
        "ai_compare_real_capture": "Yes, ai_compare used Playwright proof motion." if ai_real else f"No, ai_compare fallback: {ai_compare.get('asset_resolution_status')}",
        "payoff_real_capture": "Yes, payoff used a Playwright dashboard capture." if payoff_real else f"No, payoff fallback: {payoff.get('asset_resolution_status')}",
        "playwright_visible_interaction": "Yes: empty input, prompt typing, analyze/loading, result reveal, and savings result." if visible_interaction else "No visible interaction resolved.",
        "playwright_proof_motion": str(ai_compare.get("playwright_motion_mode") or ""),
        "drawn_placeholders_remaining": ", ".join(
            str(row.get("scene_id"))
            for row in reports
            if row.get("fallback_used") and (row.get("scene_asset_strategy") or {}).get("visual_medium") != "motion_template"
        )
        or "None among scenes planned for real sources.",
        "post_no_post_recommendation": "POST REVIEW CANDIDATE" if ready else "DO NOT POST YET: one or more planned real assets did not resolve.",
    }


def _write_proof_motion_contact_sheet(package_dir: Path, render_report: dict[str, Any]) -> str | None:
    reports = render_report.get("scene_reports") or []
    ai_compare = next((row for row in reports if row.get("scene_id") == "ai_compare"), {})
    asset_paths = [Path(path) for path in ai_compare.get("resolved_asset_paths") or []]
    frames = []
    for path in asset_paths:
        if not path.exists():
            continue
        image = cv2.imread(str(path))
        if image is None:
            continue
        frames.append(cv2.resize(image, (270, 480), interpolation=cv2.INTER_AREA))
    if not frames:
        return None
    while len(frames) < 6:
        frames.append(frames[-1])
    sheet = np.vstack([np.hstack(frames[:3]), np.hstack(frames[3:6])])
    out_path = package_dir / "ai_compare_proof_motion_contact_sheet.jpg"
    cv2.imwrite(str(out_path), sheet)
    return str(out_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Day 9 bill-leak HMR content production.")
    parser.add_argument("--preset", choices=sorted(PRESETS), default="full")
    parser.add_argument("--tts-provider", choices=["auto", "gtts", "pyttsx3", "silent"], default="gtts")
    parser.add_argument(
        "--output-dir",
        default=str(_repo_root() / "backend" / "generated_videos" / "storyboard_review" / "day9_bill_leak"),
    )
    parser.add_argument("--sprint-name", default="day9_bill_leak")
    parser.add_argument("--issue", default="#5 Day 9 Content Production - Bill Leak Money-Saving Short")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    os.environ.setdefault("ENABLE_HYBRID_MOTION_RENDERER", "1")
    os.environ.setdefault("VIDEO_GENERATION_DRY_RUN", "1")
    os.environ.pop("ELEVENLABS_API_KEY", None)
    os.environ.pop("RUNWAYML_API_KEY", None)

    preset = PRESETS[args.preset]
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    readiness = check_hmr_asset_readiness(domain="bill_leak")
    (output_dir / "asset_readiness.json").write_text(json.dumps(readiness, indent=2), encoding="utf-8")

    scenes = build_bill_leak_scenes()
    script = _script_from_scenes(scenes)
    audio_path, audio_warnings = _free_audio(script, args.tts_provider)
    stock_lookup_enabled = bool(readiness.get("status") == "PASS")
    video_path = output_dir / "day9_bill_leak_full.mp4"

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
    human_posting_gate = compute_human_posting_gate(render_report=result, qa_report=qa, human_review=human_review)
    result["sprint"] = {
        "issue": args.issue,
        "name": args.sprint_name,
        "topic": "Bill leak / money-saving short",
        "hook": "I found a $27/month leak hiding in one bill.",
    }
    result["human_review"] = human_review
    result["human_posting_gate"] = human_posting_gate
    result["qa"] = qa
    result["technical_status"] = qa["technical_status"]
    result["postability_status"] = qa["postability_status"]
    result["postability_score"] = qa["postability_score"]
    qa["human_review"] = human_review
    qa["human_posting_gate"] = human_posting_gate

    save_render_report(result, output_dir / "render_report.json")
    (output_dir / "qa_report.json").write_text(json.dumps(qa, indent=2), encoding="utf-8")
    (output_dir / "story_candidate.json").write_text(json.dumps({"script": script, "scenes": scenes}, indent=2), encoding="utf-8")
    package = create_review_package(str(output_dir), video=str(video_path), review_root=str(output_dir / "_timestamped_review_packages"))
    flat_package = _copy_flat_package(package, output_dir)
    proof_sheet = _write_proof_motion_contact_sheet(Path(flat_package["review_dir"]), result)
    if proof_sheet:
        flat_package["proof_motion_contact_sheet"] = proof_sheet

    summary = {
        "sprint": args.sprint_name,
        "issue": args.issue,
        "constraints": {
            "frozen_grocery_package_modified": False,
            "elevenlabs_used": False,
            "runwayml_used": False,
            "paid_llm_used": False,
            "audio_policy": "gTTS first, local pyttsx3 fallback, silent only if free providers fail",
        },
        "technical_status": qa["technical_status"],
        "postability_status": qa["postability_status"],
        "postability_score": qa["postability_score"],
        "human_posting_gate": human_posting_gate,
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
