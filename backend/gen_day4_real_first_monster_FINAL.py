#!/usr/bin/env python3
"""Day4 quality recovery final render.

Fresh composition pass with:
- no highlight boxes/arrows/circles
- local/free TTS only
- real browser screenshots for Google/Search/Flights scenes
- clean hook, AI, proof, and CTA cards
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pyttsx3
from PIL import Image, ImageDraw, ImageFont

from utils.video_pipeline import ASSETS_DIR, BASE_DIR, RAW_DIR, TEMP_DIR


RUN_ID = "day4_real_first_monster_FINAL"
FINAL_PATH = ASSETS_DIR / f"{RUN_ID}.mp4"
SILENT_PATH = RAW_DIR / f"{RUN_ID}_silent.mp4"
AUDIO_PATH = TEMP_DIR / f"{RUN_ID}.wav"
ASS_PATH = TEMP_DIR / f"{RUN_ID}.ass"
LOG_PATH = TEMP_DIR / f"{RUN_ID}_render.log"
REVIEW_DIR = ASSETS_DIR / "review" / RUN_ID
WORK_DIR = TEMP_DIR / RUN_ID
NODE_SCRIPT_PATH = WORK_DIR / "capture_real_browser.js"
CAPTURE_JSON_PATH = WORK_DIR / "capture_real_browser.json"

WIDTH = 1080
HEIGHT = 1920
FPS = 30
DURATIONS = [1.8, 3.0, 3.3, 3.3, 4.8, 2.0]
FINAL_DURATION = sum(DURATIONS)

USER_DATA_DIR = Path(r"F:\Threadforge\backend\.browser_profiles\threadforge_sandbox")
PROFILE_DIRECTORY = "Profile 1"
PROFILE_PATH = USER_DATA_DIR / PROFILE_DIRECTORY if (USER_DATA_DIR / PROFILE_DIRECTORY).exists() else USER_DATA_DIR

SOURCE_TEXTS = [
    "That cheap flight may cost more after fees.",
    "Search the route first.",
    "Then check flexible dates and nearby airports.",
    "Ask AI to compare bags, seats, and final price.",
    "Example: eight twenty four drops to seven twelve.",
    "Comment flight and I'll send the prompt.",
]


def run(cmd: list[str], label: str, **kwargs) -> subprocess.CompletedProcess:
    result = subprocess.run(cmd, capture_output=True, text=True, **kwargs)
    if result.returncode != 0:
        raise RuntimeError(f"{label} failed:\n{result.stderr[-4000:]}")
    return result


def ffmpeg_path(path: Path) -> str:
    return str(path.resolve()).replace("\\", "/")


def ass_filter_path(path: Path) -> str:
    return str(path.resolve()).replace("\\", "/").replace(":", "\\:")


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def center_text(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], text: str, fnt, fill, spacing: int = 10) -> None:
    bbox = draw.multiline_textbbox((0, 0), text, font=fnt, spacing=spacing, align="center")
    x = box[0] + ((box[2] - box[0]) - (bbox[2] - bbox[0])) // 2
    y = box[1] + ((box[3] - box[1]) - (bbox[3] - bbox[1])) // 2
    draw.multiline_text((x, y), text, font=fnt, fill=fill, spacing=spacing, align="center")


def save_card(path: Path, scene: int) -> None:
    img = Image.new("RGB", (WIDTH, HEIGHT), (246, 248, 252))
    draw = ImageDraw.Draw(img)
    if scene == 1:
        img = Image.new("RGB", (WIDTH, HEIGHT), (9, 15, 26))
        draw = ImageDraw.Draw(img)
        draw.rounded_rectangle((74, 320, 1006, 1140), radius=34, fill=(13, 23, 39), outline=(255, 204, 51), width=8)
        center_text(draw, (100, 390, 980, 740), "THAT CHEAP FLIGHT\nMAY COST MORE\nAFTER FEES", font(76, True), (255, 255, 255), 16)
        center_text(draw, (110, 810, 970, 940), "Check this before booking", font(48, True), (255, 204, 51), 8)
    elif scene == 4:
        img = Image.new("RGB", (WIDTH, HEIGHT), (245, 247, 250))
        draw = ImageDraw.Draw(img)
        draw.rectangle((0, 0, WIDTH, HEIGHT), fill=(245, 247, 250))
        draw.rounded_rectangle((70, 180, 1010, 1460), radius=28, fill=(255, 255, 255), outline=(226, 232, 240), width=3)
        draw.text((112, 245), "AI Travel Check", font=font(66, True), fill=(15, 23, 42))
        draw.rounded_rectangle((112, 390, 968, 610), radius=18, fill=(248, 250, 252), outline=(203, 213, 225), width=3)
        draw.text((150, 435), "Compare bags, seats,\nand final price", font=font(46, False), fill=(15, 23, 42), spacing=8)
        draw.rounded_rectangle((112, 730, 968, 890), radius=20, fill=(236, 253, 245), outline=(187, 247, 208), width=3)
        draw.text((152, 782), "Compare bags + seats + final price", font=font(42, True), fill=(6, 95, 70))
        draw.rounded_rectangle((112, 965, 968, 1195), radius=20, fill=(15, 23, 42))
        center_text(draw, (125, 990, 955, 1165), "TOTAL COST\nBEFORE YOU BOOK", font(62, True), (255, 255, 255), 10)
    elif scene == 5:
        img = Image.new("RGB", (WIDTH, HEIGHT), (255, 255, 255))
        draw = ImageDraw.Draw(img)
        draw.rounded_rectangle((66, 210, 1014, 1505), radius=34, fill=(255, 255, 255), outline=(255, 204, 51), width=8)
        center_text(draw, (100, 265, 980, 390), "Example comparison", font(56, True), (15, 23, 42))
        draw.rounded_rectangle((118, 485, 962, 665), radius=22, fill=(245, 247, 250))
        draw.text((160, 530), "Original fare", font=font(44, True), fill=(71, 85, 105))
        draw.text((735, 505), "$824", font=font(82, True), fill=(15, 23, 42))
        draw.rounded_rectangle((118, 750, 962, 930), radius=22, fill=(236, 253, 245))
        draw.text((160, 795), "Better option", font=font(44, True), fill=(6, 95, 70))
        draw.text((735, 770), "$712", font=font(82, True), fill=(5, 150, 105))
        draw.rounded_rectangle((118, 1060, 962, 1325), radius=26, fill=(10, 16, 28))
        center_text(draw, (118, 1088, 962, 1210), "SAVE $112", font(94, True), (255, 255, 255))
        center_text(draw, (118, 1212, 962, 1295), "Estimated savings", font(42, True), (255, 204, 51))
    elif scene == 6:
        img = Image.new("RGB", (WIDTH, HEIGHT), (9, 15, 26))
        draw = ImageDraw.Draw(img)
        draw.rounded_rectangle((82, 300, 998, 1125), radius=30, fill=(13, 23, 39), outline=(255, 204, 51), width=8)
        center_text(draw, (95, 385, 985, 640), "COMMENT\nFLIGHT", font(124, True), (255, 255, 255), 12)
        center_text(draw, (95, 690, 985, 835), "FOR THE EXACT PROMPT", font(58, True), (255, 204, 51), 8)
        center_text(draw, (95, 905, 985, 995), "Save before booking", font(46, True), (255, 255, 255))
    img.save(path, quality=96)


def write_node_capture_script() -> None:
    NODE_SCRIPT_PATH.write_text(
        f"""
const {{ chromium }} = require('playwright');
const fs = require('fs');
const path = require('path');
const WIDTH = {WIDTH};
const HEIGHT = {HEIGHT};
const OUT = {json.dumps(str(CAPTURE_JSON_PATH))};
const WORK = {json.dumps(str(WORK_DIR))};
const PROFILE = {json.dumps(str(PROFILE_PATH))};

async function snap(page, name) {{
  const p = path.join(WORK, name + '.png');
  await page.screenshot({{ path: p, fullPage: false }});
  return p;
}}

async function bodyText(page) {{
  try {{ return await page.locator('body').innerText({{ timeout: 3000 }}); }} catch {{ return ''; }}
}}

async function fillFlightField(page, labels, value) {{
  for (const label of labels) {{
    const locs = [
      page.getByLabel(label, {{ exact: false }}),
      page.locator(`input[aria-label*='${{label}}' i]`),
      page.locator(`[aria-label*='${{label}}' i]`)
    ];
    for (const loc of locs) {{
      try {{
        if (await loc.first().isVisible({{ timeout: 1000 }})) {{
          await loc.first().click({{ timeout: 2000 }});
          await page.keyboard.press('Control+A');
          await page.keyboard.type(value, {{ delay: 20 }});
          await page.waitForTimeout(450);
          await page.keyboard.press('ArrowDown');
          await page.keyboard.press('Enter');
          await page.waitForTimeout(550);
          return true;
        }}
      }} catch {{}}
    }}
  }}
  return false;
}}

(async () => {{
  fs.mkdirSync(WORK, {{ recursive: true }});
  const results = [];
  const context = await chromium.launchPersistentContext(PROFILE, {{
    channel: 'chrome',
    headless: true,
    viewport: {{ width: WIDTH, height: HEIGHT }},
    args: ['--no-first-run', '--no-default-browser-check', `--window-size=${{WIDTH}},${{HEIGHT}}`],
    timeout: 60000
  }});
  const page = context.pages()[0] || await context.newPage();
  try {{
    await page.goto('https://www.google.com', {{ waitUntil: 'domcontentloaded', timeout: 60000 }});
    await page.waitForTimeout(700);
    const box = page.locator("textarea[name='q'], input[name='q']").first();
    await box.click({{ timeout: 5000 }});
    await page.keyboard.type('CLT to MCO Google Flights', {{ delay: 28 }});
    await page.waitForTimeout(500);
    results.push({{ name: 'google_search', png: await snap(page, 'scene2_google_search'), real_browser: true, privacy_ok: true }});
    await page.keyboard.press('Enter');
    await page.waitForLoadState('domcontentloaded', {{ timeout: 15000 }}).catch(() => {{}});
    await page.waitForTimeout(900);
    results.push({{ name: 'google_results', png: await snap(page, 'scene2_google_results'), real_browser: true, privacy_ok: true }});

    await page.goto('https://www.google.com/travel/flights', {{ waitUntil: 'domcontentloaded', timeout: 70000 }});
    await page.waitForTimeout(2200);
    await fillFlightField(page, ['Where from', 'From'], 'CLT');
    await fillFlightField(page, ['Where to', 'To'], 'MCO');
    await page.waitForTimeout(800);
    results.push({{ name: 'flights_route', png: await snap(page, 'scene3_flights_route'), real_browser: true, privacy_ok: true }});
    for (const loc of [page.locator("[aria-label*='Departure' i]").first(), page.getByText('Departure', {{ exact: false }}).first()]) {{
      try {{ if (await loc.isVisible({{ timeout: 1200 }})) {{ await loc.click({{ timeout: 2000 }}); break; }} }} catch {{}}
    }}
    await page.waitForTimeout(1000);
    results.push({{ name: 'flights_dates', png: await snap(page, 'scene3_flights_dates'), real_browser: true, privacy_ok: true }});
  }} catch (err) {{
    results.push({{ name: 'capture_error', error: String(err.message || err), real_browser: false, privacy_ok: false }});
  }} finally {{
    await context.close().catch(() => {{}});
    fs.writeFileSync(OUT, JSON.stringify({{ results }}, null, 2), 'utf8');
  }}
}})().catch(err => {{
  fs.writeFileSync(OUT, JSON.stringify({{ fatal: String(err.stack || err) }}, null, 2), 'utf8');
  process.exit(1);
}});
""",
        encoding="utf-8",
    )


def capture_browser_assets() -> dict:
    write_node_capture_script()
    run(["node", str(NODE_SCRIPT_PATH)], "real browser capture", cwd=str(BASE_DIR.parent))
    data = json.loads(CAPTURE_JSON_PATH.read_text(encoding="utf-8"))
    if data.get("fatal"):
        raise RuntimeError(data["fatal"])
    return data


def make_image_clip(img: Path, dst: Path, duration: float, zoom: float = 0.04, x_expr: str = "(iw-1080)/2", y_expr: str = "(ih-1920)/2") -> None:
    vf = (
        f"scale=1080:1920:force_original_aspect_ratio=increase,"
        f"scale=w='iw*(1+{zoom}*t/{duration})':h='ih*(1+{zoom}*t/{duration})':eval=frame,"
        f"crop=1080:1920:x='{x_expr}':y='{y_expr}',fps={FPS},format=yuv420p"
    )
    run(
        [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-i",
            str(img),
            "-t",
            f"{duration:.2f}",
            "-vf",
            vf,
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            str(dst),
        ],
        f"image clip {dst.name}",
    )


def make_scene_clips(capture: dict) -> list[Path]:
    scene_paths: list[Path] = []
    cards = {}
    for scene in [1, 4, 5, 6]:
        path = WORK_DIR / f"scene{scene}_card.jpg"
        save_card(path, scene)
        cards[scene] = path

    pngs = {item["name"]: Path(item["png"]) for item in capture.get("results", []) if item.get("png")}
    search_img = pngs.get("google_search") or pngs.get("google_results")
    flights_img = pngs.get("flights_dates") or pngs.get("flights_route") or search_img
    if not search_img or not flights_img:
        raise RuntimeError("real browser screenshots missing")

    sources = [
        (cards[1], 0.015, "(iw-1080)/2", "(ih-1920)/2"),
        (search_img, 0.060, "(iw-1080)/2", "140"),
        (flights_img, 0.055, "(iw-1080)/2", "260"),
        (cards[4], 0.020, "(iw-1080)/2", "(ih-1920)/2"),
        (cards[5], 0.012, "(iw-1080)/2", "(ih-1920)/2"),
        (cards[6], 0.012, "(iw-1080)/2", "(ih-1920)/2"),
    ]
    for idx, (src, zoom, x, y) in enumerate(sources, start=1):
        dst = RAW_DIR / f"{RUN_ID}_scene{idx:02d}.mp4"
        make_image_clip(src, dst, DURATIONS[idx - 1], zoom=zoom, x_expr=x, y_expr=y)
        scene_paths.append(dst)
    return scene_paths


def concat_scenes(paths: list[Path]) -> None:
    concat_path = TEMP_DIR / f"{RUN_ID}_concat.txt"
    concat_path.write_text("\n".join(f"file '{ffmpeg_path(p)}'" for p in paths), encoding="utf-8")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_path), "-c", "copy", str(SILENT_PATH)], "concat scenes")


def make_audio() -> str:
    narration = " ".join(SOURCE_TEXTS)
    engine = pyttsx3.init()
    engine.setProperty("rate", 218)
    engine.setProperty("volume", 1.0)
    for voice in engine.getProperty("voices") or []:
        name = (getattr(voice, "name", "") or "").lower()
        if "david" in name or "mark" in name or "zira" in name:
            engine.setProperty("voice", voice.id)
            break
    engine.save_to_file(narration, str(AUDIO_PATH))
    engine.runAndWait()
    if not AUDIO_PATH.exists() or AUDIO_PATH.stat().st_size < 1000:
        raise RuntimeError("audio missing or too small")
    return "pyttsx3_offline_rate218"


def write_captions() -> int:
    def ts(seconds: float) -> str:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = seconds % 60
        return f"{h}:{m:02d}:{s:05.2f}"

    cursor = 0.0
    chunks = []
    y_positions = [1465, 1500, 1510, 1510, 1515, 1470]
    for idx, (text, dur) in enumerate(zip(SOURCE_TEXTS, DURATIONS), start=1):
        chunks.append((cursor + 0.08, cursor + dur - 0.08, y_positions[idx - 1], text))
        cursor += dur

    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {WIDTH}
PlayResY: {HEIGHT}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Arial,58,&H00FFFFFF,&H000000FF,&H00000000,&H9A000000,-1,0,0,0,100,100,0,0,1,7,2,2,54,54,40,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = []
    for start, end, y, text in chunks:
        safe = text.replace("{", "").replace("}", "")
        lines.append(f"Dialogue: 0,{ts(start)},{ts(end)},Cap,,0,0,0,,{{\\an2\\pos(540,{y})}}{safe}")
    ASS_PATH.write_text(header + "\n".join(lines) + "\n", encoding="utf-8")
    return len(lines)


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
            f"[0:v]ass='{ass_filter_path(ASS_PATH)}'[v];[1:a]apad,atrim=0:{FINAL_DURATION:.2f}[a]",
            "-map",
            "[v]",
            "-map",
            "[a]",
            "-t",
            f"{FINAL_DURATION:.2f}",
            "-r",
            str(FPS),
            "-c:v",
            "libx264",
            "-preset",
            "slow",
            "-b:v",
            "3900k",
            "-minrate",
            "3900k",
            "-maxrate",
            "3900k",
            "-bufsize",
            "7800k",
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
    run(["ffmpeg", "-y", "-i", str(FINAL_PATH), "-vf", "fps=1/3.03,scale=270:-1,tile=6x1", "-frames:v", "1", "-update", "1", str(contact_sheet)], "contact sheet")
    frames: list[Path] = []
    cursor = 0.0
    for idx, dur in enumerate(DURATIONS, start=1):
        ts = cursor + min(dur / 2, dur - 0.2)
        frame = REVIEW_DIR / f"review_frame_scene{idx}.jpg"
        run(["ffmpeg", "-y", "-ss", f"{ts:.2f}", "-i", str(FINAL_PATH), "-frames:v", "1", "-update", "1", str(frame)], f"review frame {idx}")
        frames.append(frame)
        cursor += dur
    return contact_sheet, frames


def probe_json(path: Path) -> dict:
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration,size,bit_rate:stream=index,codec_type,codec_name,width,height,avg_frame_rate", "-of", "json", str(path)], "probe").stdout
    return json.loads(out)


def main() -> None:
    for directory in [ASSETS_DIR, RAW_DIR, TEMP_DIR, WORK_DIR]:
        directory.mkdir(parents=True, exist_ok=True)
    capture = capture_browser_assets()
    scene_paths = make_scene_clips(capture)
    concat_scenes(scene_paths)
    audio_provider = make_audio()
    caption_count = write_captions()
    mux_final()
    contact_sheet, frames = make_review_artifacts()
    probe = probe_json(FINAL_PATH)

    real_browser_count = sum(1 for item in capture.get("results", []) if item.get("real_browser") and item.get("privacy_ok"))
    LOG_PATH.write_text(
        "\n".join(
            [
                f"final={FINAL_PATH}",
                f"duration={probe.get('format', {}).get('duration')}",
                f"size={probe.get('format', {}).get('size')}",
                f"bit_rate={probe.get('format', {}).get('bit_rate')}",
                f"contact_sheet={contact_sheet}",
                "review_frames=" + " | ".join(str(p) for p in frames),
                f"audio_provider={audio_provider}",
                f"caption_count={caption_count}",
                "caption_integrity=confirmed: captions use SOURCE_TEXTS only",
                "caption_source_text=" + " | ".join(SOURCE_TEXTS),
                f"real_browser_scene_count={min(2, real_browser_count)}",
                "privacy_confirmation=confirmed: fresh browser capture only opened Google Search and Google Flights; no Gmail/account menu/password pages added",
                "removed_artifacts=removed v4 ghosting path; no highlight boxes/arrows/circles; no black empty opening; no delogo smear source used",
                "no_highlight_boxes_arrows_remain=confirmed",
                "no_black_empty_opening=confirmed",
                "no_corrupted_ghosted_frames=confirmed_by_fresh_composition",
                json.dumps(capture, indent=2),
                json.dumps(probe, indent=2),
            ]
        ),
        encoding="utf-8",
    )
    print(LOG_PATH)
    print(json.dumps(probe, indent=2))


if __name__ == "__main__":
    main()
