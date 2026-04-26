#!/usr/bin/env python3
"""Generate Day5 subscription/bill audit faceless review video.

Free/local review build only:
- no ElevenLabs
- no RunwayML
- no paid APIs
- fake/demo charges only
- local DOM AI assistant fallback via Playwright
"""

from __future__ import annotations

import json
import math
import shutil
import subprocess
from pathlib import Path

import pyttsx3
from PIL import Image, ImageDraw, ImageFont


BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "generated_videos"
RAW_DIR = ASSETS_DIR / "raw"
TEMP_DIR = ASSETS_DIR / "temp"

RUN_ID = "day5_subscription_audit_faceless_v1"
FINAL_PATH = ASSETS_DIR / f"{RUN_ID}.mp4"
SILENT_PATH = RAW_DIR / f"{RUN_ID}_silent.mp4"
WORK_DIR = TEMP_DIR / RUN_ID
REVIEW_DIR = ASSETS_DIR / "review" / RUN_ID
LOG_PATH = TEMP_DIR / f"{RUN_ID}_render.log"
ASS_PATH = TEMP_DIR / f"{RUN_ID}.ass"

WIDTH = 1080
HEIGHT = 1920
FPS = 30
DURATIONS = [3.0, 3.0, 4.0, 8.0, 4.0, 8.0]
FINAL_DURATION = sum(DURATIONS)

SOURCE_TEXTS = [
    "I checked my bank statement and found three things I forgot I was paying for.",
    "Most people think they spend about eighty six dollars a month. The real number is closer to two hundred nineteen.",
    "So I pasted everything in and typed one thing.",
    "That's fifty three dollars a month I was just leaving there.",
    "Six hundred thirty six dollars. Every year.",
    "Comment AUDIT and I'll send you exactly what I typed before your next billing cycle.",
]

VISUAL_TEXTS = {
    "prompt": "Which of these should I cancel, downgrade, or call about?",
    "scene1": "3 CHARGES I FORGOT",
    "think": "THINK: $86/mo",
    "reality": "REALITY: $219/mo",
    "total": "$636 A YEAR",
}


def run(cmd: list[str], label: str) -> subprocess.CompletedProcess:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"{label} failed:\n{result.stderr[-4000:]}")
    return result


def ffmpeg_path(path: Path) -> str:
    return str(path.resolve()).replace("\\", "/")


def ass_path(path: Path) -> str:
    return ffmpeg_path(path).replace(":", "\\:")


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def text_center(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], text: str, fnt, fill, spacing: int = 8) -> None:
    bbox = draw.multiline_textbbox((0, 0), text, font=fnt, spacing=spacing, align="center")
    x = box[0] + ((box[2] - box[0]) - (bbox[2] - bbox[0])) // 2
    y = box[1] + ((box[3] - box[1]) - (bbox[3] - bbox[1])) // 2
    draw.multiline_text((x, y), text, font=fnt, fill=fill, spacing=spacing, align="center")


def rounded(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], radius: int, fill, outline=None, width: int = 1) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def draw_scene1(t: float) -> Image.Image:
    img = Image.new("RGB", (WIDTH, HEIGHT), (245, 247, 250))
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, WIDTH, 150), fill=(255, 255, 255))
    draw.text((64, 54), "Checking", font=font(46, True), fill=(18, 25, 38))
    draw.text((64, 125), "Demo statement", font=font(28), fill=(101, 116, 139))
    rounded(draw, (68, 210, 1012, 420), 22, (13, 23, 39))
    draw.text((112, 258), "Available balance", font=font(30), fill=(196, 204, 216))
    draw.text((112, 305), "$4,280.12", font=font(72, True), fill=(255, 255, 255))

    overlay_y = 470
    rounded(draw, (70, overlay_y, 1010, overlay_y + 120), 18, (255, 255, 255), (222, 228, 236), 2)
    text_center(draw, (80, overlay_y + 22, 1000, overlay_y + 102), VISUAL_TEXTS["scene1"], font(58, True), (13, 23, 39))

    rows = [
        ("Streamly Premium", "Recurring", "-$18.00", (239, 68, 68)),
        ("Mobile Plan", "Autopay", "-$92.10", (15, 23, 42)),
        ("CloudBox Storage", "Monthly", "-$5.00", (239, 68, 68)),
        ("Gym Trial", "Renewed", "-$30.00", (15, 23, 42)),
        ("Coffee House", "Card", "-$6.25", (15, 23, 42)),
    ]
    scroll = min(1.0, max(0.0, (t - 0.35) / 2.2)) * 115
    y0 = 690 - int(scroll)
    for i, (name, meta, amount, color) in enumerate(rows):
        y = y0 + i * 176
        if -90 < y < HEIGHT:
            rounded(draw, (70, y, 1010, y + 136), 18, (255, 255, 255), (226, 232, 240), 2)
            draw.text((112, y + 32), name, font=font(40, True), fill=(15, 23, 42))
            draw.text((112, y + 82), meta, font=font(28), fill=(100, 116, 139))
            draw.text((790, y + 43), amount, font=font(42, True), fill=color)
    return img


def draw_scene2(t: float) -> Image.Image:
    img = Image.new("RGB", (WIDTH, HEIGHT), (248, 250, 252))
    draw = ImageDraw.Draw(img)
    text_center(draw, (80, 235, 1000, 360), "What it feels like", font(48, True), (71, 85, 105))
    rounded(draw, (78, 470, 1002, 790), 26, (255, 255, 255), (226, 232, 240), 3)
    text_center(draw, (98, 520, 982, 635), "THINK", font(54, True), (100, 116, 139))
    text_center(draw, (98, 625, 982, 745), "$86/mo", font(82, True), (15, 23, 42))
    scale = 1.0 + 0.06 * math.sin(min(t, 2.5) * math.pi)
    rounded(draw, (54, 905, 1026, 1325), 30, (13, 23, 39))
    text_center(draw, (74, 965, 1006, 1070), "REALITY", font(58, True), (255, 255, 255))
    f = font(int(124 * scale), True)
    text_center(draw, (74, 1070, 1006, 1260), "$219/mo", f, (52, 211, 153))
    return img


def draw_scene5(_: float) -> Image.Image:
    img = Image.new("RGB", (WIDTH, HEIGHT), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    text_center(draw, (55, 595, 1025, 825), "$636 A YEAR", font(118, True), (5, 15, 30))
    text_center(draw, (90, 855, 990, 970), "From a 15-minute\nbank statement", font(50, True), (71, 85, 105), 8)
    return img


def draw_scene6(_: float) -> Image.Image:
    img = Image.new("RGB", (WIDTH, HEIGHT), (13, 23, 39))
    draw = ImageDraw.Draw(img)
    text_center(draw, (65, 430, 1015, 650), "COMMENT AUDIT", font(100, True), (255, 255, 255))
    text_center(draw, (65, 665, 1015, 800), "FOR THE PROMPT", font(68, True), (52, 211, 153))
    text_center(draw, (95, 920, 985, 1035), "Before your next\nbilling cycle", font(48, True), (226, 232, 240), 8)
    text_center(draw, (95, 1430, 985, 1495), "Fake demo data shown", font(30), (148, 163, 184))
    return img


def make_frame_scene(scene_id: int, duration: float, drawer) -> Path:
    frame_dir = WORK_DIR / f"frames_scene{scene_id:02d}"
    if frame_dir.exists():
        shutil.rmtree(frame_dir)
    frame_dir.mkdir(parents=True)
    frame_count = int(round(duration * FPS))
    for frame in range(frame_count):
        t = frame / FPS
        drawer(t).save(frame_dir / f"frame_{frame:04d}.png")
    out = RAW_DIR / f"{RUN_ID}_scene{scene_id:02d}.mp4"
    run(
        [
            "ffmpeg", "-y", "-framerate", str(FPS), "-i", str(frame_dir / "frame_%04d.png"),
            "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS), str(out),
        ],
        f"render scene {scene_id}",
    )
    return out


def write_ai_dom() -> tuple[Path, Path]:
    html = WORK_DIR / "day5_local_ai.html"
    js = WORK_DIR / "day5_local_ai_capture.js"
    html.write_text(
        f"""<!doctype html>
<html><head><meta charset="utf-8"><style>
html,body{{margin:0;width:{WIDTH}px;height:{HEIGHT}px;background:#f8fafc;font-family:Arial,Helvetica,sans-serif;color:#0f172a;overflow:hidden}}
.wrap{{padding:110px 68px}} .top{{font-size:38px;font-weight:800;margin-bottom:26px}}
.panel{{background:white;border:2px solid #e2e8f0;border-radius:24px;padding:34px;box-shadow:0 18px 50px rgba(15,23,42,.10)}}
.line{{font-size:34px;margin:16px 0;color:#334155}} .muted{{color:#64748b}}
.prompt{{margin-top:34px;background:#0f172a;color:white;border-radius:22px;padding:28px;font-size:42px;line-height:1.18;min-height:210px}}
.cursor{{display:inline-block;width:4px;height:44px;background:#34d399;vertical-align:-8px;animation:blink .7s steps(1) infinite}}
.results{{margin-top:34px}} .result{{opacity:0;transform:translateY(18px);background:#ecfdf5;border:2px solid #bbf7d0;border-radius:20px;padding:24px 28px;margin:18px 0;font-size:40px;font-weight:800;color:#065f46}}
.total{{opacity:0;margin-top:28px;text-align:center;background:#0f172a;color:white;border-radius:22px;padding:34px;font-size:62px;font-weight:900}}
@keyframes blink{{50%{{opacity:0}}}}
</style></head><body><div class="wrap">
<div class="top">AI bill audit</div>
<div class="panel">
<div class="line">Streamly Premium <span class="muted">-$18/mo</span></div>
<div class="line">Mobile Plan <span class="muted">-$92/mo</span></div>
<div class="line">CloudBox Storage <span class="muted">-$5/mo</span></div>
<div class="prompt"><span id="typed"></span><span class="cursor"></span></div>
<div class="results">
<div class="result" id="r1">Cancel overlap -> save $18</div>
<div class="result" id="r2">Lower phone bill -> save $30</div>
<div class="result" id="r3">Downgrade storage -> save $5</div>
<div class="total" id="total">$53/month found</div>
</div></div></div>
<script>
const text = {json.dumps(VISUAL_TEXTS["prompt"])};
const typed = document.getElementById('typed');
let i = 0;
function typeNext(){{
  if(i <= text.length){{ typed.textContent = text.slice(0, i++); setTimeout(typeNext, 42); }}
}}
setTimeout(typeNext, 650);
function show(id, delay){{ setTimeout(() => {{ const el=document.getElementById(id); el.style.opacity=1; el.style.transform='translateY(0)'; el.style.transition='all .28s ease-out'; }}, delay); }}
show('r1', 4300); show('r2', 5200); show('r3', 6100); show('total', 7350);
</script></body></html>""",
        encoding="utf-8",
    )
    js_source = """const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
(async () => {{
  const work = __WORK__;
  const browser = await chromium.launch({{ channel:'chrome', headless:true, args:['--no-first-run','--no-default-browser-check','--window-size=__WIDTH__,__HEIGHT__'] }});
  const context = await browser.newContext({{ viewport:{{width:__WIDTH__,height:__HEIGHT__}}, recordVideo:{{dir:work,size:{{width:__WIDTH__,height:__HEIGHT__}}}} }});
  const page = await context.newPage();
  await page.goto('file:///' + path.resolve(work, 'day5_local_ai.html').replace(/\\\\/g, '/'));
  await page.waitForTimeout(12300);
  const video = page.video();
  await page.close();
  const raw = await video.path();
  await context.close();
  await browser.close();
  fs.copyFileSync(raw, path.join(work, 'day5_local_ai.webm'));
}})().catch(err => {{ console.error(err); process.exit(1); }});"""
    js_source = (
        js_source.replace("__WORK__", json.dumps(str(WORK_DIR)))
        .replace("__WIDTH__", str(WIDTH))
        .replace("__HEIGHT__", str(HEIGHT))
        .replace("{{", "{")
        .replace("}}", "}")
    )
    js.write_text(
        js_source,
        encoding="utf-8",
    )
    return html, js


def make_ai_scenes() -> tuple[Path, Path]:
    _, js = write_ai_dom()
    run(["node", str(js)], "record local DOM AI assistant")
    webm = WORK_DIR / "day5_local_ai.webm"
    scene3 = RAW_DIR / f"{RUN_ID}_scene03.mp4"
    scene4 = RAW_DIR / f"{RUN_ID}_scene04.mp4"
    for out, start, dur in [(scene3, 0.0, 4.0), (scene4, 4.0, 8.0)]:
        run(
            [
                "ffmpeg", "-y", "-ss", f"{start:.2f}", "-i", str(webm), "-t", f"{dur:.2f}",
                "-vf", "scale=1080:1920,fps=30", "-an", "-c:v", "libx264", "-preset", "fast",
                "-crf", "18", "-pix_fmt", "yuv420p", str(out),
            ],
            f"split AI scene {out.name}",
        )
    return scene3, scene4


def concat_scenes(paths: list[Path]) -> None:
    concat_path = TEMP_DIR / f"{RUN_ID}_concat.txt"
    concat_path.write_text("\n".join(f"file '{ffmpeg_path(path)}'" for path in paths), encoding="utf-8")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_path), "-c", "copy", str(SILENT_PATH)], "concat scenes")


def make_audio() -> tuple[Path, str]:
    engine = pyttsx3.init()
    engine.setProperty("rate", 171)
    engine.setProperty("volume", 1.0)
    for voice in engine.getProperty("voices") or []:
        name = (getattr(voice, "name", "") or "").lower()
        if "zira" in name or "david" in name or "mark" in name:
            engine.setProperty("voice", voice.id)
            break

    parts: list[Path] = []
    for idx, text in enumerate(SOURCE_TEXTS, start=1):
        raw = WORK_DIR / f"voice_scene{idx}.wav"
        engine.save_to_file(text, str(raw))
        parts.append(raw)
    engine.runAndWait()

    fitted: list[Path] = []
    for idx, (raw, dur) in enumerate(zip(parts, DURATIONS), start=1):
        out = WORK_DIR / f"voice_scene{idx}_fit.wav"
        run(
            [
                "ffmpeg", "-y", "-i", str(raw), "-af",
                f"apad,atrim=0:{dur:.2f},afade=t=out:st={max(0.1, dur - 0.08):.2f}:d=0.08",
                "-ar", "48000", "-ac", "2", str(out),
            ],
            f"fit audio scene {idx}",
        )
        fitted.append(out)

    concat = WORK_DIR / "audio_concat.txt"
    concat.write_text("\n".join(f"file '{ffmpeg_path(path)}'" for path in fitted), encoding="utf-8")
    final_audio = TEMP_DIR / f"{RUN_ID}.wav"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat), "-c", "pcm_s16le", str(final_audio)], "concat audio")
    return final_audio, "pyttsx3_offline_windows_sapi_rate171"


def write_captions() -> int:
    def ts(seconds: float) -> str:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = seconds % 60
        return f"{h}:{m:02d}:{s:05.2f}"

    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {WIDTH}
PlayResY: {HEIGHT}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Arial,54,&H00FFFFFF,&H000000FF,&H00000000,&HA0000000,-1,0,0,0,100,100,0,0,1,7,2,2,54,54,40,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    y_positions = [1510, 1470, 1500, 1500, 1535, 1490]
    cursor = 0.0
    events: list[str] = []
    for idx, (text, dur) in enumerate(zip(SOURCE_TEXTS, DURATIONS)):
        words = text.split()
        chunks = [" ".join(words[i : i + 5]) for i in range(0, len(words), 5)]
        usable_start = cursor + 0.12
        usable_end = cursor + dur - 0.12
        step = (usable_end - usable_start) / max(1, len(chunks))
        for cidx, chunk in enumerate(chunks):
            start = usable_start + cidx * step
            end = usable_start + (cidx + 1) * step
            safe = chunk.replace("{", "").replace("}", "")
            events.append(f"Dialogue: 0,{ts(start)},{ts(end)},Cap,,0,0,0,,{{\\an2\\pos(540,{y_positions[idx]})}}{safe}")
        cursor += dur
    ASS_PATH.write_text(header + "\n".join(events) + "\n", encoding="utf-8")
    return len(events)


def mux_final(audio_path: Path) -> None:
    run(
        [
            "ffmpeg", "-y", "-i", str(SILENT_PATH), "-i", str(audio_path),
            "-filter_complex", f"[0:v]ass='{ass_path(ASS_PATH)}'[v];[1:a]apad,atrim=0:{FINAL_DURATION:.2f}[a]",
            "-map", "[v]", "-map", "[a]", "-t", f"{FINAL_DURATION:.2f}", "-r", str(FPS),
            "-c:v", "libx264", "-preset", "slow", "-b:v", "4200k", "-minrate", "4200k",
            "-maxrate", "4200k", "-bufsize", "8400k", "-x264-params", "nal-hrd=cbr",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart",
            str(FINAL_PATH),
        ],
        "mux final",
    )


def make_review_artifacts() -> tuple[Path, list[Path]]:
    if REVIEW_DIR.exists():
        shutil.rmtree(REVIEW_DIR)
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    frames: list[Path] = []
    cursor = 0.0
    offsets = [1.45, 1.50, 3.62, 4.75, 1.80, 3.60]
    for idx, dur in enumerate(DURATIONS, start=1):
        frame = REVIEW_DIR / f"review_frame_scene{idx}.jpg"
        ts = cursor + min(offsets[idx - 1], dur - 0.20)
        run(["ffmpeg", "-y", "-ss", f"{ts:.2f}", "-i", str(FINAL_PATH), "-frames:v", "1", "-update", "1", str(frame)], f"review frame {idx}")
        frames.append(frame)
        cursor += dur
    contact = REVIEW_DIR / "contact_sheet.jpg"
    thumbs = [Image.open(frame).resize((270, 480), Image.Resampling.LANCZOS).convert("RGB") for frame in frames]
    sheet = Image.new("RGB", (270 * len(thumbs), 480), (255, 255, 255))
    for idx, thumb in enumerate(thumbs):
        sheet.paste(thumb, (idx * 270, 0))
    sheet.save(contact, quality=92)
    return contact, frames


def probe_json(path: Path) -> dict:
    out = run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration,size,bit_rate:stream=index,codec_type,codec_name,width,height,avg_frame_rate",
            "-of", "json", str(path),
        ],
        "probe final",
    ).stdout
    return json.loads(out)


def main() -> None:
    for directory in [ASSETS_DIR, RAW_DIR, TEMP_DIR, WORK_DIR, REVIEW_DIR]:
        directory.mkdir(parents=True, exist_ok=True)

    scene1 = make_frame_scene(1, DURATIONS[0], draw_scene1)
    scene2 = make_frame_scene(2, DURATIONS[1], draw_scene2)
    scene3, scene4 = make_ai_scenes()
    scene5 = make_frame_scene(5, DURATIONS[4], draw_scene5)
    scene6 = make_frame_scene(6, DURATIONS[5], draw_scene6)
    concat_scenes([scene1, scene2, scene3, scene4, scene5, scene6])
    audio_path, audio_provider = make_audio()
    caption_count = write_captions()
    mux_final(audio_path)
    contact, frames = make_review_artifacts()
    probe = probe_json(FINAL_PATH)

    log_lines = [
        f"final={FINAL_PATH}",
        f"duration={probe.get('format', {}).get('duration')}",
        f"size={probe.get('format', {}).get('size')}",
        "fps=30",
        f"dimensions={WIDTH}x{HEIGHT}",
        f"audio_provider={audio_provider}",
        f"contact_sheet={contact}",
        "review_frames=" + " | ".join(str(p) for p in frames),
        "caption_count=" + str(caption_count),
        "caption_sync_confirmation=confirmed: captions regenerated after final audio creation from SOURCE_TEXTS; max five words per event; scene windows match locked audio/video durations",
        "privacy_confirmation=confirmed: fake/demo charges only; no real bills, bank account data, Gmail, passwords, or private documents",
        "no_paid_credits_confirmation=confirmed: no ElevenLabs, no RunwayML, no paid API calls",
        "ai_browser_mode=local DOM fallback via Playwright; no real ChatGPT/browser account used",
        "scene1_duration=3.00 seconds exact for future face-hook replacement",
        "transitions=hard cuts only",
        json.dumps(probe, indent=2),
    ]
    LOG_PATH.write_text("\n".join(log_lines), encoding="utf-8")
    print(LOG_PATH)
    print(json.dumps(probe, indent=2))


if __name__ == "__main__":
    main()
