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

RUN_ID = "day5_subscription_audit_faceless_v2"
FINAL_PATH = ASSETS_DIR / f"{RUN_ID}.mp4"
SILENT_PATH = RAW_DIR / f"{RUN_ID}_silent.mp4"
WORK_DIR = TEMP_DIR / RUN_ID
REVIEW_DIR = ASSETS_DIR / "review" / RUN_ID
LOG_PATH = TEMP_DIR / f"{RUN_ID}_render.log"
ASS_PATH = TEMP_DIR / f"{RUN_ID}.ass"

WIDTH = 1080
HEIGHT = 1920
FPS = 30
DURATIONS = [3.0, 4.0, 5.0, 9.0, 4.0, 6.0]
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
    img = Image.new("RGB", (WIDTH, HEIGHT), (246, 248, 251))
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, WIDTH, 122), fill=(255, 255, 255))
    draw.text((52, 36), "Statement review", font=font(42, True), fill=(15, 23, 42))
    draw.text((742, 44), "Demo data", font=font(28), fill=(100, 116, 139))

    rounded(draw, (48, 170, 1032, 1545), 18, (255, 255, 255), (220, 226, 235), 2)
    draw.rectangle((50, 171, 1030, 250), fill=(241, 245, 249))
    cols = [(72, "Date"), (215, "Merchant"), (610, "Type"), (830, "Amount")]
    for x, label in cols:
        draw.text((x, 198), label, font=font(26, True), fill=(71, 85, 105))
    for x in [185, 580, 805]:
        draw.line((x, 170, x, 1545), fill=(226, 232, 240), width=2)

    overlay_y = 276
    rounded(draw, (84, overlay_y, 996, overlay_y + 94), 12, (15, 23, 42))
    text_center(draw, (94, overlay_y + 12, 986, overlay_y + 82), VISUAL_TEXTS["scene1"], font(46, True), (255, 255, 255))

    rows = [
        ("Mar 01", "Payroll Deposit", "Income", "+$2,850.00", (22, 101, 52)),
        ("Mar 03", "Streamly Premium", "Recurring", "-$18.00", (220, 38, 38)),
        ("Mar 05", "Grocery Market", "Card", "-$84.22", (15, 23, 42)),
        ("Mar 07", "Mobile Plan", "Autopay", "-$92.10", (220, 38, 38)),
        ("Mar 10", "CloudBox Storage", "Monthly", "-$5.00", (220, 38, 38)),
        ("Mar 12", "Gym Trial", "Renewed", "-$30.00", (15, 23, 42)),
        ("Mar 13", "Coffee House", "Card", "-$6.25", (15, 23, 42)),
        ("Mar 14", "Transit Pass", "Card", "-$3.00", (15, 23, 42)),
    ]
    scroll = min(1.0, max(0.0, (t - 0.45) / 2.1)) * 150
    y0 = 425 - int(scroll)
    for i, (date, merchant, kind, amount, color) in enumerate(rows):
        y = y0 + i * 112
        if 250 < y < 1520:
            fill = (255, 255, 255) if i % 2 else (248, 250, 252)
            draw.rectangle((50, y, 1030, y + 102), fill=fill)
            if kind in {"Recurring", "Autopay", "Monthly"}:
                draw.rectangle((52, y, 62, y + 102), fill=(52, 211, 153))
            draw.text((72, y + 34), date, font=font(26), fill=(71, 85, 105))
            draw.text((215, y + 30), merchant, font=font(32, True), fill=(15, 23, 42))
            draw.text((610, y + 34), kind, font=font(26), fill=(100, 116, 139))
            draw.text((830, y + 30), amount, font=font(30, True), fill=color)
            draw.line((50, y + 102, 1030, y + 102), fill=(226, 232, 240), width=1)
            if t > 1.1 and kind in {"Recurring", "Autopay", "Monthly"}:
                pulse = int(3 + 2 * math.sin(t * 8))
                draw.rectangle((206 - pulse, y + 5 - pulse, 1004 + pulse, y + 97 + pulse), outline=(52, 211, 153), width=4)
    return img


def draw_scene2(t: float) -> Image.Image:
    img = Image.new("RGB", (WIDTH, HEIGHT), (248, 250, 252))
    draw = ImageDraw.Draw(img)
    text_center(draw, (80, 235, 1000, 360), "What people guess", font(48, True), (71, 85, 105))
    rounded(draw, (118, 500, 962, 760), 24, (255, 255, 255), (226, 232, 240), 3)
    text_center(draw, (98, 520, 982, 635), "THINK", font(54, True), (100, 116, 139))
    text_center(draw, (98, 625, 982, 735), "$86/mo", font(72, True), (100, 116, 139))
    scale = 1.0 + 0.06 * math.sin(min(t, 2.5) * math.pi)
    rounded(draw, (50, 890, 1030, 1365), 30, (13, 23, 39))
    text_center(draw, (74, 965, 1006, 1070), "REALITY", font(58, True), (255, 255, 255))
    f = font(int(124 * scale), True)
    text_center(draw, (74, 1060, 1006, 1285), "$219/mo", f, (52, 211, 153))
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
html,body{{margin:0;width:{WIDTH}px;height:{HEIGHT}px;background:#f6f8fb;font-family:Arial,Helvetica,sans-serif;color:#0f172a;overflow:hidden}}
.screen{{position:absolute;inset:0;padding:76px 56px;box-sizing:border-box}}
.sheet{{background:white;border:1px solid #d9e1ea;box-shadow:0 18px 45px rgba(15,23,42,.10)}}
.bar{{height:72px;background:#f1f5f9;border-bottom:1px solid #d9e1ea;display:flex;align-items:center;padding:0 22px;font-weight:800;font-size:28px;color:#334155}}
.tabs{{margin-left:auto;font-size:20px;color:#64748b;font-weight:600}}
table{{border-collapse:collapse;width:100%;font-size:26px}} th{{background:#f8fafc;text-align:left;color:#64748b;padding:18px 16px;border:1px solid #e2e8f0}}
td{{padding:18px 16px;border:1px solid #e2e8f0}} .money{{text-align:right;font-weight:800}} .rec{{background:#ecfdf5}} .sel{{outline:5px solid #22c55e;outline-offset:-5px;background:#dcfce7}}
.cursorDot{{position:absolute;width:30px;height:30px;border-radius:50%;background:#0f172a;box-shadow:0 0 0 8px rgba(15,23,42,.15);left:820px;top:690px;transition:all .45s ease}}
.toast{{position:absolute;left:312px;top:1215px;background:#0f172a;color:white;border-radius:12px;padding:18px 26px;font-size:26px;font-weight:800;opacity:0}}
.chat{{position:absolute;left:56px;right:56px;top:76px;background:white;border:1px solid #d9e1ea;box-shadow:0 18px 45px rgba(15,23,42,.10);min-height:1370px;padding:34px;box-sizing:border-box;opacity:0;transition:opacity .2s linear}}
.chatTop{{font-size:34px;font-weight:900;margin-bottom:22px}} .paste{{background:#f8fafc;border:1px solid #e2e8f0;border-radius:14px;padding:20px;font-size:24px;line-height:1.35;color:#475569;white-space:pre-line;min-height:170px;opacity:0}}
.prompt{{margin-top:26px;background:#0f172a;color:white;border-radius:18px;padding:28px;font-size:40px;line-height:1.18;min-height:205px}}
.cursor{{display:inline-block;width:4px;height:42px;background:#34d399;vertical-align:-8px;animation:blink .7s steps(1) infinite}}
.result{{opacity:0;transform:translateY(14px);background:#ecfdf5;border:1px solid #bbf7d0;border-radius:16px;padding:23px 26px;margin:16px 0;font-size:38px;font-weight:900;color:#065f46;transition:all .24s ease-out}}
.total{{opacity:0;background:#0f172a;color:white;border-radius:18px;text-align:center;font-size:58px;font-weight:900;margin-top:24px;padding:30px;transition:opacity .2s ease-out}}
@keyframes blink{{50%{{opacity:0}}}}
</style></head><body>
<div class="screen sheet" id="sheet"><div class="bar">recurring_charges_demo.csv <span class="tabs">Fake data only</span></div>
<table><thead><tr><th>Date</th><th>Merchant</th><th>Category</th><th class="money">Monthly</th></tr></thead><tbody>
<tr><td>03/03</td><td>Streamly Premium</td><td>Streaming</td><td class="money">$18</td></tr>
<tr class="rec" id="s1"><td>03/07</td><td>Mobile Plan</td><td>Phone</td><td class="money">$92</td></tr>
<tr><td>03/10</td><td>CloudBox Storage</td><td>Storage</td><td class="money">$5</td></tr>
<tr><td>03/12</td><td>Gym Trial</td><td>Fitness</td><td class="money">$30</td></tr>
<tr><td>03/15</td><td>MealBox</td><td>Food</td><td class="money">$74</td></tr>
</tbody></table><div class="cursorDot" id="dot"></div><div class="toast" id="toast">Copied 5 rows</div></div>
<div class="chat" id="chat"><div class="chatTop">AI bill audit</div>
<div class="paste" id="paste">Streamly Premium, Streaming, $18/month
Mobile Plan, Phone, $92/month
CloudBox Storage, Storage, $5/month
Gym Trial, Fitness, $30/month
MealBox, Food, $74/month</div>
<div class="prompt"><span id="typed"></span><span class="cursor"></span></div>
<div class="result" id="r1">Cancel overlap -> save $18</div>
<div class="result" id="r2">Lower phone bill -> save $30</div>
<div class="result" id="r3">Downgrade storage -> save $5</div>
<div class="total" id="total">$53/month found</div></div>
<script>
const promptText = {json.dumps(VISUAL_TEXTS["prompt"])};
const typed = document.getElementById('typed');
setTimeout(() => {{ document.getElementById('dot').style.left='905px'; document.getElementById('dot').style.top='445px'; }}, 500);
setTimeout(() => {{ ['s1'].forEach(id => document.getElementById(id).classList.add('sel')); document.getElementById('dot').style.left='910px'; document.getElementById('dot').style.top='780px'; }}, 1150);
setTimeout(() => {{ document.getElementById('toast').style.opacity=1; }}, 1900);
setTimeout(() => {{ document.getElementById('sheet').style.opacity=0; document.getElementById('chat').style.opacity=1; }}, 2500);
setTimeout(() => {{ document.getElementById('paste').style.opacity=1; }}, 2720);
let i = 0;
function typeNext(){{ if(i <= promptText.length){{ typed.textContent = promptText.slice(0, i++); setTimeout(typeNext, 19); }} }}
setTimeout(typeNext, 2860);
function show(id, delay){{ setTimeout(() => {{ const el=document.getElementById(id); el.style.opacity=1; el.style.transform='translateY(0)'; }}, delay); }}
show('r1', 6200); show('r2', 7350); show('r3', 8500); show('total', 10000);
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
  await page.waitForTimeout(14500);
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
    for out, start, dur in [(scene3, 0.0, 5.0), (scene4, 5.0, 9.0)]:
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
    engine.setProperty("rate", 184)
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
    return final_audio, "pyttsx3_offline_windows_sapi_rate184"


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
    offsets = [1.45, 2.10, 4.25, 4.80, 1.80, 2.80]
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
        "tool_mode_used=local sheet plus local DOM fallback via Playwright; no real ChatGPT/browser account used",
        "scene1_duration=3.00 seconds exact for future face-hook replacement",
        "transitions=hard cuts only",
        json.dumps(probe, indent=2),
    ]
    LOG_PATH.write_text("\n".join(log_lines), encoding="utf-8")
    print(LOG_PATH)
    print(json.dumps(probe, indent=2))


if __name__ == "__main__":
    main()
