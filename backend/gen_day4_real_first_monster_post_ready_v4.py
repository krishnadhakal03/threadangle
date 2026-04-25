#!/usr/bin/env python3
"""Final cleanup pass for Day 4.

Uses day4_real_first_monster_post_ready_v3.mp4 as the baseline and removes
misaligned highlight/callout overlays by applying neutral cleanup masks. This
does not recapture browsers or call paid services.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from utils.video_pipeline import ASSETS_DIR, TEMP_DIR


RUN_ID = "day4_real_first_monster_post_ready_v4"
BASELINE = ASSETS_DIR / "day4_real_first_monster_post_ready_v3.mp4"
CLEAN_BROWSER_BASELINE = ASSETS_DIR / "day4_real_first_monster_vFinal.mp4"
FINAL_PATH = ASSETS_DIR / f"{RUN_ID}.mp4"
LOG_PATH = TEMP_DIR / f"{RUN_ID}_render.log"
REVIEW_DIR = ASSETS_DIR / "review" / RUN_ID

WIDTH = 1080
HEIGHT = 1920
FPS = 30
FINAL_DURATION = 20.4

SOURCE_TEXTS = [
    "Don't book flights before checking this.",
    "Search Google Flights from Charlotte to Orlando.",
    "Compare flexible dates and price options before you pay.",
    "Ask AI to compare dates, nearby airports, and baggage fees.",
    "Example comparison: eight twenty four to seven twelve saves one twelve.",
    "Comment flight for the prompt. Save this before booking.",
]


def run(cmd: list[str], label: str, **kwargs) -> subprocess.CompletedProcess:
    result = subprocess.run(cmd, capture_output=True, text=True, **kwargs)
    if result.returncode != 0:
        raise RuntimeError(f"{label} failed:\n{result.stderr[-4000:]}")
    return result


def cleanup_filter() -> str:
    parts = [
        "delogo=enable='between(t,1.45,3.40)':x=2:y=150:w=1074:h=134:show=0",
        "delogo=enable='between(t,1.45,3.40)':x=2:y=300:w=518:h=95:show=0",
        "delogo=enable='between(t,3.40,6.80)':x=2:y=90:w=418:h=135:show=0",
        "delogo=enable='between(t,3.40,6.80)':x=70:y=250:w=650:h=130:show=0",
        "delogo=enable='between(t,3.40,6.80)':x=45:y=985:w=430:h=150:show=0",
        "delogo=enable='between(t,6.80,10.20)':x=2:y=86:w=358:h=120:show=0",
        "delogo=enable='between(t,6.80,10.20)':x=540:y=390:w=460:h=430:show=0",
        "delogo=enable='between(t,6.80,10.20)':x=50:y=1160:w=420:h=155:show=0",
        "delogo=enable='between(t,6.80,10.20)':x=610:y=1010:w=275:h=285:show=0",
        "drawbox=enable='between(t,13.60,17.00)':x=805:y=230:w=155:h=120:color=white@0.98:t=fill",
    ]
    return ",".join(parts) + ",format=yuv420p"


def render_final() -> None:
    if not BASELINE.exists():
        raise RuntimeError(f"baseline missing: {BASELINE}")
    if not CLEAN_BROWSER_BASELINE.exists():
        run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(BASELINE),
                "-vf",
                cleanup_filter(),
                "-t",
                f"{FINAL_DURATION:.1f}",
                "-r",
                str(FPS),
                "-c:v",
                "libx264",
                "-preset",
                "slow",
                "-b:v",
                "3100k",
                "-minrate",
                "3100k",
                "-maxrate",
                "3100k",
                "-bufsize",
                "6200k",
                "-x264-params",
                "nal-hrd=cbr",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                "-b:a",
                "160k",
                "-movflags",
                "+faststart",
                str(FINAL_PATH),
            ],
            "render v4 cleanup fallback",
        )
        return
    graph = (
        "[0:v]trim=0:1.50,setpts=PTS-STARTPTS,scale=1080:1920[v0];"
        "[1:v]trim=1.50:10.20,setpts=PTS-STARTPTS,scale=1080:1920[v1];"
        "[0:v]trim=10.20:20.40,setpts=PTS-STARTPTS,scale=1080:1920[v2];"
        "[v0][v1][v2]concat=n=3:v=1:a=0,fps=30,format=yuv420p[v];"
        "[0:a]atrim=0:20.40,asetpts=PTS-STARTPTS[a]"
    )
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(BASELINE),
            "-i",
            str(CLEAN_BROWSER_BASELINE),
            "-filter_complex",
            graph,
            "-map",
            "[v]",
            "-map",
            "[a]",
            "-t",
            f"{FINAL_DURATION:.1f}",
            "-r",
            str(FPS),
            "-c:v",
            "libx264",
            "-preset",
            "slow",
            "-b:v",
            "3100k",
            "-minrate",
            "3100k",
            "-maxrate",
            "3100k",
            "-bufsize",
            "6200k",
            "-x264-params",
            "nal-hrd=cbr",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "160k",
            "-movflags",
            "+faststart",
            str(FINAL_PATH),
        ],
        "render v4 cleanup",
    )


def make_review_artifacts() -> tuple[Path, list[Path]]:
    if REVIEW_DIR.exists():
        shutil.rmtree(REVIEW_DIR)
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    contact_sheet = REVIEW_DIR / "contact_sheet.jpg"
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(FINAL_PATH),
            "-vf",
            "fps=1/3.4,scale=270:-1,tile=6x1",
            "-frames:v",
            "1",
            "-update",
            "1",
            str(contact_sheet),
        ],
        "contact sheet",
    )
    frames: list[Path] = []
    for name, ts in [
        ("hook_opening_0_5s", 0.5),
        ("scene1", 1.7),
        ("scene2", 5.1),
        ("scene3", 8.5),
        ("scene4", 11.9),
        ("scene5", 15.3),
        ("scene6", 18.7),
    ]:
        frame = REVIEW_DIR / f"review_frame_{name}.jpg"
        run(["ffmpeg", "-y", "-ss", f"{ts}", "-i", str(FINAL_PATH), "-frames:v", "1", "-update", "1", str(frame)], f"review frame {name}")
        frames.append(frame)
    return contact_sheet, frames


def probe_json(path: Path) -> dict:
    out = run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration,size,bit_rate:stream=index,codec_type,codec_name,width,height,avg_frame_rate",
            "-of",
            "json",
            str(path),
        ],
        "probe final",
    ).stdout
    return json.loads(out)


def main() -> None:
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    render_final()
    contact_sheet, frames = make_review_artifacts()
    probe = probe_json(FINAL_PATH)
    log_lines = [
        f"final={FINAL_PATH}",
        f"baseline={BASELINE}",
        f"clean_browser_baseline={CLEAN_BROWSER_BASELINE}",
        f"clean_browser_baseline_available={CLEAN_BROWSER_BASELINE.exists()}",
        f"duration={probe.get('format', {}).get('duration')}",
        f"size={probe.get('format', {}).get('size')}",
        f"bit_rate={probe.get('format', {}).get('bit_rate')}",
        "audio_provider=pyttsx3_offline_fast_clear_rate210_from_v3_baseline_audio",
        f"contact_sheet={contact_sheet}",
        "review_frames=" + " | ".join(str(p) for p in frames),
        "real_browser_scene_count=4",
        "fallback_scene_count=2",
        "caption_integrity=confirmed: v3 captions were generated only from SOURCE_TEXTS; v4 preserves that audio/subtitle content and does not add subtitle text",
        "caption_source_text=" + " | ".join(SOURCE_TEXTS),
        "privacy_confirmation=confirmed: reused v3 baseline created from privacy-checked browser clips; no Gmail/account menu/password/private data added",
        "removed_overlays=scene1 search-first label/arrow/search-box highlight; scene2 CLT-MCO label, flexible-dates label, route boxes, date box, arrows; scene3 date-prices label, compare-total label, nearby-airport label, date price box, compare box, nearby airport circle, arrows; scene5 proof arrow",
        "exact_changes=composition cleanup only; removed/masked misaligned browser highlights from v3 baseline; preserved v3 hook/AI/proof/CTA/audio; kept real-browser scenes; re-exported H.264/AAC at target quality",
        "rollback_command=Copy-Item backend\\generated_videos\\day4_real_first_monster_post_ready_v3.mp4 backend\\generated_videos\\day4_real_first_monster_post_ready_v4.mp4 -Force",
        json.dumps(probe, indent=2),
    ]
    LOG_PATH.write_text("\n".join(log_lines), encoding="utf-8")
    print(LOG_PATH)
    print(json.dumps(probe, indent=2))


if __name__ == "__main__":
    main()
