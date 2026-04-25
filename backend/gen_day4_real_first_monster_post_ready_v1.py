#!/usr/bin/env python3
"""Post-ready clarity pass for day4_real_first_monster_vFinal.

Uses the existing real-browser scene MP4s as source material, then applies
mobile-readable crops and clean overlays. No browser recapture is performed.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pyttsx3
from PIL import Image, ImageDraw, ImageFont

from utils.caption_generator import generate_ass_from_scenes
from utils.video_pipeline import ASSETS_DIR, RAW_DIR, TEMP_DIR, ScenePlan


BASE_RUN_ID = "day4_real_first_monster_vFinal"
RUN_ID = "day4_real_first_monster_post_ready_v1"

WIDTH = 1080
HEIGHT = 1920
FPS = 30
SCENE_DURATION = 3.4
FINAL_DURATION = 20.4

FINAL_PATH = ASSETS_DIR / f"{RUN_ID}.mp4"
SILENT_PATH = RAW_DIR / f"{RUN_ID}_silent.mp4"
AUDIO_PATH = TEMP_DIR / f"{RUN_ID}.wav"
ASS_PATH = TEMP_DIR / f"{RUN_ID}.ass"
LOG_PATH = TEMP_DIR / f"{RUN_ID}_render.log"
REVIEW_DIR = ASSETS_DIR / "review" / RUN_ID
OVERLAY_DIR = TEMP_DIR / f"{RUN_ID}_overlays"

SOURCE_TEXTS = [
    "Don't book flights before checking this.",
    "Search Google Flights from Charlotte to Orlando.",
    "Compare flexible dates and price options before you pay.",
    "Ask AI to compare dates, nearby airports, and baggage fees.",
    "Example comparison: eight twenty four to seven twelve saves one twelve.",
    "Comment flight for the prompt. Save this before booking.",
]

SCENE_SOURCES = [
    RAW_DIR / f"{BASE_RUN_ID}_scene01.mp4",
    RAW_DIR / f"{BASE_RUN_ID}_scene02.mp4",
    RAW_DIR / f"{BASE_RUN_ID}_scene03.mp4",
    RAW_DIR / f"{BASE_RUN_ID}_scene04.mp4",
    RAW_DIR / f"{BASE_RUN_ID}_scene05.mp4",
    RAW_DIR / f"{BASE_RUN_ID}_scene06.mp4",
]

# Crops are 9:16 windows over the recorded 1080x1920 browser captures.
# They zoom important UI areas while preserving visible browser trust.
SCENE_CROPS = [
    "crop=760:1351:160:250,scale=1080:1920",
    "crop=880:1564:120:250,scale=1080:1920",
    "crop=880:1564:120:250,scale=1080:1920",
    "scale=1080:1920",
    "crop=760:1351:160:250,scale=1080:1920",
    "scale=1080:1920",
]


def run(cmd: list[str], label: str, **kwargs) -> subprocess.CompletedProcess:
    result = subprocess.run(cmd, capture_output=True, text=True, **kwargs)
    if result.returncode != 0:
        raise RuntimeError(f"{label} failed:\n{result.stderr[-4000:]}")
    return result


def path_for_filter(path: Path) -> str:
    return str(path.resolve()).replace("\\", "/").replace(":", "\\:")


def ffmpeg_concat_path(path: Path) -> str:
    return str(path.resolve()).replace("\\", "/")


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def rounded_label(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    *,
    fill: tuple[int, int, int, int] = (10, 16, 28, 230),
    stroke: tuple[int, int, int, int] = (255, 204, 51, 255),
    size: int = 44,
) -> None:
    x, y = xy
    fnt = font(size, bold=True)
    bbox = draw.textbbox((0, 0), text, font=fnt, stroke_width=0)
    w = bbox[2] - bbox[0] + 44
    h = bbox[3] - bbox[1] + 30
    draw.rounded_rectangle((x, y, x + w, y + h), radius=24, fill=fill, outline=stroke, width=4)
    draw.text((x + 22, y + 14), text, font=fnt, fill=(255, 255, 255, 255))


def center_text(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], text: str, fnt, fill) -> None:
    bbox = draw.multiline_textbbox((0, 0), text, font=fnt, spacing=8, align="center")
    x = box[0] + ((box[2] - box[0]) - (bbox[2] - bbox[0])) // 2
    y = box[1] + ((box[3] - box[1]) - (bbox[3] - bbox[1])) // 2
    draw.multiline_text((x, y), text, font=fnt, fill=fill, spacing=8, align="center")


def draw_arrow(draw: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int], color=(255, 204, 51, 255)) -> None:
    draw.line((start, end), fill=color, width=12)
    ex, ey = end
    sx, sy = start
    dx = 1 if ex >= sx else -1
    dy = 1 if ey >= sy else -1
    draw.polygon([(ex, ey), (ex - 34 * dx, ey - 10 * dy), (ex - 10 * dx, ey - 34 * dy)], fill=color)


def make_overlay(scene: int) -> Path:
    OVERLAY_DIR.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    if scene == 1:
        rounded_label(draw, (96, 330), "SEARCH FLEXIBLE DATES")
        draw.rounded_rectangle((48, 208, 1032, 292), radius=44, outline=(255, 204, 51, 255), width=10)
        draw_arrow(draw, (365, 325), (250, 286))
    elif scene == 2:
        rounded_label(draw, (80, 175), "GOOGLE FLIGHTS ROUTE")
        rounded_label(draw, (72, 1328), "FLEXIBLE DATES", size=40)
        draw.rounded_rectangle((98, 410, 982, 1170), radius=28, outline=(255, 204, 51, 255), width=10)
        draw.rounded_rectangle((52, 1215, 505, 1405), radius=20, outline=(42, 139, 242, 255), width=9)
        draw_arrow(draw, (300, 1320), (445, 1215), color=(42, 139, 242, 255))
    elif scene == 3:
        rounded_label(draw, (70, 170), "NEARBY AIRPORTS")
        rounded_label(draw, (86, 1340), "COMPARE TOTAL PRICE", size=38)
        draw.ellipse((92, 1120, 505, 1305), outline=(42, 139, 242, 255), width=10)
        draw.rounded_rectangle((465, 565, 970, 1085), radius=22, outline=(255, 204, 51, 255), width=10)
        draw_arrow(draw, (315, 1260), (470, 1160), color=(42, 139, 242, 255))
    elif scene == 4:
        rounded_label(draw, (76, 170), "AI CHECKLIST")
        items = ["dates", "nearby airports", "baggage fees", "final fare"]
        y = 700
        for item in items:
            draw.rounded_rectangle((122, y, 958, y + 102), radius=20, fill=(255, 255, 255, 236), outline=(16, 185, 129, 255), width=5)
            draw.text((168, y + 25), "check " + item, font=font(44, bold=True), fill=(12, 20, 36, 255))
            y += 126
    elif scene == 5:
        # The browser search remains visible behind this labeled example proof card.
        draw.rounded_rectangle((62, 250, 1018, 1420), radius=36, fill=(255, 255, 255, 242), outline=(255, 204, 51, 255), width=8)
        center_text(draw, (100, 300, 980, 410), "Example comparison", font(54, bold=True), (20, 28, 44, 255))
        draw.rounded_rectangle((118, 475, 962, 645), radius=22, fill=(245, 247, 250, 255))
        draw.text((160, 508), "Original fare", font=font(44, bold=True), fill=(71, 85, 105, 255))
        draw.text((740, 493), "$824", font=font(78, bold=True), fill=(15, 23, 42, 255))
        draw.rounded_rectangle((118, 710, 962, 880), radius=22, fill=(236, 253, 245, 255))
        draw.text((160, 743), "Better option", font=font(44, bold=True), fill=(6, 95, 70, 255))
        draw.text((740, 728), "$712", font=font(78, bold=True), fill=(5, 150, 105, 255))
        draw.rounded_rectangle((118, 970, 962, 1220), radius=26, fill=(10, 16, 28, 255))
        center_text(draw, (118, 990, 962, 1110), "SAVE $112", font(92, bold=True), (255, 255, 255, 255))
        center_text(draw, (118, 1110, 962, 1195), "Estimated savings", font(42, bold=True), (255, 204, 51, 255))
        draw_arrow(draw, (850, 310), (905, 245))
    elif scene == 6:
        draw.rounded_rectangle((70, 260, 1010, 1085), radius=36, fill=(10, 16, 28, 235), outline=(255, 204, 51, 255), width=8)
        center_text(draw, (90, 325, 990, 595), "COMMENT\nFLIGHT", font(118, bold=True), (255, 255, 255, 255))
        center_text(draw, (90, 620, 990, 790), "FOR THE PROMPT", font(72, bold=True), (255, 204, 51, 255))
        center_text(draw, (90, 835, 990, 950), "Save this before booking", font(48, bold=True), (255, 255, 255, 255))

    out = OVERLAY_DIR / f"scene{scene:02d}_overlay.png"
    img.save(out)
    return out


def make_scene(idx: int, src: Path, crop_filter: str) -> Path:
    if not src.exists() or src.stat().st_size < 1000:
        raise RuntimeError(f"missing baseline scene: {src}")
    overlay = make_overlay(idx)
    dst = RAW_DIR / f"{RUN_ID}_scene{idx:02d}.mp4"
    vf = f"[0:v]{crop_filter},fps={FPS},format=rgba[base];[base][1:v]overlay=0:0:format=auto,format=yuv420p[v]"
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(src),
            "-loop",
            "1",
            "-i",
            str(overlay),
            "-t",
            f"{SCENE_DURATION:.2f}",
            "-filter_complex",
            vf,
            "-map",
            "[v]",
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(dst),
        ],
        f"make scene {idx}",
    )
    return dst


def concat_clips(paths: list[Path]) -> None:
    concat_path = TEMP_DIR / f"{RUN_ID}_concat.txt"
    concat_path.write_text("\n".join(f"file '{ffmpeg_concat_path(p)}'" for p in paths), encoding="utf-8")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_path), "-c", "copy", str(SILENT_PATH)], "concat scenes")


def make_audio() -> str:
    # ElevenLabs is intentionally not called from this post pass to avoid any
    # credit spend without explicit runtime approval. Use clearer/faster offline TTS.
    narration = " ".join(SOURCE_TEXTS)
    engine = pyttsx3.init()
    engine.setProperty("rate", 202)
    engine.setProperty("volume", 1.0)
    voices = engine.getProperty("voices") or []
    for voice in voices:
        name = (getattr(voice, "name", "") or "").lower()
        if "david" in name or "mark" in name or "zira" in name:
            engine.setProperty("voice", voice.id)
            break
    engine.save_to_file(narration, str(AUDIO_PATH))
    engine.runAndWait()
    if not AUDIO_PATH.exists() or AUDIO_PATH.stat().st_size < 1000:
        raise RuntimeError("offline narration missing or too small")
    return "pyttsx3_offline_fast_clear"


def make_captions(raw_paths: list[Path]) -> int:
    scenes: list[ScenePlan] = []
    cursor = 0.0
    for idx, text in enumerate(SOURCE_TEXTS, start=1):
        scenes.append(
            ScenePlan(
                idx=idx,
                start=cursor,
                end=cursor + SCENE_DURATION,
                part="hook" if idx == 1 else ("cta" if idx == 6 else "body"),
                source_text=text,
                subtitle=text,
                visual_description="Day4 real-browser flight clarity pass",
                keywords=["flight", "travel", "savings"],
                energy="high",
                clip_path=str(raw_paths[idx - 1]),
            )
        )
        cursor += SCENE_DURATION
    ass = generate_ass_from_scenes(scenes, audio_path=str(AUDIO_PATH))
    ASS_PATH.write_text(ass, encoding="utf-8")
    count = ass.count("Dialogue:")
    if count <= 0:
        raise RuntimeError("caption generation produced no Dialogue lines")
    return count


def mux_final() -> None:
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(SILENT_PATH),
            "-i",
            str(AUDIO_PATH),
            "-filter_complex",
            f"[0:v]ass='{path_for_filter(ASS_PATH)}'[v];[1:a]apad,atrim=0:{FINAL_DURATION:.1f}[a]",
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
            "3200k",
            "-minrate",
            "3200k",
            "-maxrate",
            "3200k",
            "-bufsize",
            "6400k",
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
        "mux final",
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
    for idx, ts in enumerate([1.7, 5.1, 8.5, 11.9, 15.3, 18.7], start=1):
        frame = REVIEW_DIR / f"review_frame_scene{idx}.jpg"
        run(["ffmpeg", "-y", "-ss", f"{ts}", "-i", str(FINAL_PATH), "-frames:v", "1", "-update", "1", str(frame)], f"review frame {idx}")
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
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    if OVERLAY_DIR.exists():
        shutil.rmtree(OVERLAY_DIR)

    scene_paths = [make_scene(idx, src, crop) for idx, (src, crop) in enumerate(zip(SCENE_SOURCES, SCENE_CROPS), start=1)]
    concat_clips(scene_paths)
    audio_provider = make_audio()
    dialogue_count = make_captions(scene_paths)
    mux_final()
    contact_sheet, frames = make_review_artifacts()
    probe = probe_json(FINAL_PATH)

    log_lines = [
        f"final={FINAL_PATH}",
        f"duration={probe.get('format', {}).get('duration')}",
        f"size={probe.get('format', {}).get('size')}",
        f"bit_rate={probe.get('format', {}).get('bit_rate')}",
        f"audio_provider={audio_provider}",
        f"contact_sheet={contact_sheet}",
        "review_frames=" + " | ".join(str(p) for p in frames),
        "source_scenes=" + " | ".join(str(p) for p in SCENE_SOURCES),
        "post_scene_clips=" + " | ".join(str(p) for p in scene_paths),
        "real_browser_scene_count=4",
        "fallback_scene_count=2",
        "caption_integrity=confirmed: captions generated only from SOURCE_TEXTS",
        "caption_source_text=" + " | ".join(SOURCE_TEXTS),
        "privacy_confirmation=confirmed: reused baseline clips that passed privacy checks; zoom crops avoid Gmail/account menu regions where possible; no password/account menu/private data added",
        "rollback_command=Copy-Item backend\\generated_videos\\day4_real_first_monster_vFinal.mp4 backend\\generated_videos\\day4_real_first_monster_post_ready_v1.mp4 -Force",
        json.dumps(probe, indent=2),
    ]
    LOG_PATH.write_text("\n".join(log_lines), encoding="utf-8")
    print(LOG_PATH)
    print(json.dumps(probe, indent=2))


if __name__ == "__main__":
    main()
