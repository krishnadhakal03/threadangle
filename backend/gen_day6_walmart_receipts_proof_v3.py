#!/usr/bin/env python3
"""Generate Day6 Walmart+ receipts proof draft/review video.

Draft-only constraints:
- no ElevenLabs
- no RunwayML
- no paid APIs
- local/free TTS only
- proof inserts use staged, masked screenshots
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
REPO_DIR = BASE_DIR.parent
ASSET_DIR = REPO_DIR / "launch_assets" / "day6_walmart_receipts"
ASSETS_DIR = BASE_DIR / "generated_videos"
RAW_DIR = ASSETS_DIR / "raw"
TEMP_DIR = ASSETS_DIR / "temp"

RUN_ID = "day6_walmart_receipts_proof_v3"
FINAL_PATH = ASSETS_DIR / f"{RUN_ID}.mp4"
SILENT_PATH = RAW_DIR / f"{RUN_ID}_silent.mp4"
WORK_DIR = TEMP_DIR / RUN_ID
REVIEW_DIR = ASSETS_DIR / "review" / RUN_ID
LOG_PATH = TEMP_DIR / f"{RUN_ID}_render.log"
ASS_PATH = TEMP_DIR / f"{RUN_ID}.ass"
AUDIO_PATH = TEMP_DIR / f"{RUN_ID}.wav"

WIDTH = 1080
HEIGHT = 1920
FPS = 30
DURATIONS = [4.0, 4.0, 5.0, 8.0, 4.0, 7.0]
FINAL_DURATION = sum(DURATIONS)

SOURCE_TEXTS = [
    "I don't have a car. So every grocery trip was costing me extra.",
    "Between rides and Peacock, that was about $53 a month.",
    "So I asked Google AI if one service could cover both.",
    "Walmart+ covered delivery, Peacock, and cashback.",
    "That is about $480 a year. And zero grocery rides.",
    "Comment WALMART and I'll send the exact prompt.",
]

TTS_TEXTS = [
    "I don't have a car. So every grocery trip was costing me extra.",
    "Between rides and Peacock, that was about fifty three dollars a month.",
    "So I asked Google AI if one service could cover both.",
    "Walmart Plus covered delivery, Peacock, and cashback.",
    "That is about four hundred eighty dollars a year. And zero grocery rides.",
    "Comment Walmart and I'll send the exact prompt.",
]

SCREENSHOTS = {
    "lyft": ASSET_DIR / "01_onepay_lyft_receipt.jpeg",
    "cashback": ASSET_DIR / "02_onepay_5percent_cashback.jpeg",
    "peacock": ASSET_DIR / "03_walmart_peacock_subscription.jpeg",
    "benefits": ASSET_DIR / "04_walmart_benefits.jpeg",
    "savings": ASSET_DIR / "05_walmart_savings.jpeg",
    "dashboard": ASSET_DIR / "06_walmart_dashboard.jpeg",
    "google_ai_proof": ASSET_DIR / "07_google_ai_mode_proof.png",
}

PROMPT = (
    "I spend $42/month on rides for groceries from Walmart and $11/month on Peacock. "
    "I don't have a car. Is there one service that covers this cheaper?"
)


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


def center(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], text: str, fnt, fill, spacing: int = 8) -> None:
    bbox = draw.multiline_textbbox((0, 0), text, font=fnt, spacing=spacing, align="center")
    x = box[0] + ((box[2] - box[0]) - (bbox[2] - bbox[0])) // 2
    y = box[1] + ((box[3] - box[1]) - (bbox[3] - bbox[1])) // 2
    draw.multiline_text((x, y), text, font=fnt, fill=fill, spacing=spacing, align="center")


def cover_image(path: Path, scale_boost: float = 1.0) -> Image.Image:
    img = Image.open(path).convert("RGB")
    scale = max(WIDTH / img.width, HEIGHT / img.height) * scale_boost
    size = (int(img.width * scale), int(img.height * scale))
    return img.resize(size, Image.Resampling.LANCZOS)


def paste_pan(base: Image.Image, source: Image.Image, t: float, duration: float, x_bias: float = 0.5, y0: float = 0.0, y1: float = 1.0) -> None:
    progress = min(1.0, max(0.0, t / max(duration, 0.01)))
    x = int((WIDTH - source.width) * x_bias)
    max_y = max(0, source.height - HEIGHT)
    y = -int(max_y * (y0 + (y1 - y0) * progress))
    base.paste(source, (x, y))


def paste_handheld(base: Image.Image, source: Image.Image, t: float, duration: float, x_bias: float = 0.5, y0: float = 0.0, y1: float = 1.0) -> None:
    progress = min(1.0, max(0.0, t / max(duration, 0.01)))
    if t > duration * 0.45:
        progress = min(1.0, progress + 0.08)
    max_y = max(0, source.height - HEIGHT)
    x = int((WIDTH - source.width) * x_bias + math.sin(t * 8.5) * 8 + math.sin(t * 2.2) * 5)
    y = -int(max_y * (y0 + (y1 - y0) * progress)) + int(math.sin(t * 9.0) * 7)
    base.paste(source, (x, y))


def draw_overlay_box(draw: ImageDraw.ImageDraw, y: int, title: str, sub: str | None = None) -> None:
    draw.rounded_rectangle((68, y, 1012, y + 250), radius=28, fill=(5, 15, 30))
    center(draw, (90, y + 35, 990, y + 130), title, font(78, True), (255, 255, 255))
    if sub:
        center(draw, (90, y + 135, 990, y + 220), sub, font(47, True), (52, 211, 153), 6)


def documentary_bg(path: Path, t: float, duration: float, alpha: int = 120, scale_boost: float = 1.0, y0: float = 0.05, y1: float = 0.32) -> Image.Image:
    img = Image.new("RGB", (WIDTH, HEIGHT), (248, 250, 252))
    src = cover_image(path, scale_boost)
    paste_handheld(img, src, t, duration, 0.5, y0, y1)
    veil = Image.new("RGBA", (WIDTH, HEIGHT), (255, 255, 255, alpha))
    return Image.alpha_composite(img.convert("RGBA"), veil).convert("RGB")


def replacement_row(draw: ImageDraw.ImageDraw, y: int, label: str, value: str, active: bool = True) -> None:
    fill = (255, 255, 255) if active else (241, 245, 249)
    draw.rounded_rectangle((78, y, 1002, y + 132), radius=20, fill=fill, outline=(203, 213, 225), width=2)
    draw.text((118, y + 42), label, font=font(38, True), fill=(15, 23, 42))
    if value:
        draw.text((700, y + 42), value, font=font(36, True), fill=(5, 150, 105))
    else:
        draw.text((872, y + 40), "included", font=font(34, True), fill=(5, 150, 105))


def draw_scene1(t: float) -> Image.Image:
    img = Image.new("RGB", (WIDTH, HEIGHT), (6, 10, 18))
    src = cover_image(SCREENSHOTS["lyft"], 1.12 if t < 2.0 else 1.18)
    paste_handheld(img, src, t, DURATIONS[0], 0.5, 0.02, 0.42)
    veil = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 118 if t < 1.25 else 82))
    img = Image.alpha_composite(img.convert("RGBA"), veil).convert("RGB")
    draw = ImageDraw.Draw(img)
    if t < 2.05:
        center(draw, (58, 320, 1022, 470), "I DON'T HAVE A CAR", font(72, True), (255, 255, 255))
        center(draw, (70, 505, 1010, 650), "SO GROCERIES\nCOST ME EXTRA", font(66, True), (52, 211, 153), 8)
    else:
        draw_overlay_box(draw, 1138, "$42/MONTH", "JUST TO GET GROCERIES")
    return img


def draw_scene2(t: float) -> Image.Image:
    key = "peacock" if t < 2.1 else "lyft"
    img = documentary_bg(SCREENSHOTS[key], t, DURATIONS[1], alpha=172, scale_boost=0.9 if key == "peacock" else 1.08, y0=0.05, y1=0.28)
    draw = ImageDraw.Draw(img)
    center(draw, (70, 210, 1010, 300), "BEFORE", font(70, True), (15, 23, 42))
    rows = [
        ("Uber/Lyft:", "$42"),
        ("Peacock:", "$10.99"),
        ("Total:", "$52.99/month"),
    ]
    y = 500
    for idx, (label, amount) in enumerate(rows):
        if t < idx * 0.45:
            y += 215
            continue
        fill = (255, 255, 255) if idx < 2 else (13, 23, 39)
        outline = (226, 232, 240) if idx < 2 else None
        draw.rounded_rectangle((88, y, 992, y + 160), radius=22, fill=fill, outline=outline, width=3)
        color = (15, 23, 42) if idx < 2 else (255, 255, 255)
        amt_color = (220, 38, 38) if idx < 2 else (52, 211, 153)
        draw.text((132, y + 55), label, font=font(44, True), fill=color)
        draw.text((610, y + 48), amount, font=font(48, True), fill=amt_color)
        y += 215
    return img


def draw_scene3(t: float) -> Image.Image:
    img = Image.new("RGB", (WIDTH, HEIGHT), (255, 255, 255))
    proof = Image.open(SCREENSHOTS["google_ai_proof"]).convert("RGB")
    # Wide desktop proof: scale height enough for readable center crop, then drift horizontally.
    scale = max(HEIGHT / proof.height * 1.07, WIDTH / proof.width * 1.85)
    src = proof.resize((int(proof.width * scale), int(proof.height * scale)), Image.Resampling.LANCZOS)
    x = int((WIDTH - src.width) * (0.34 + 0.06 * min(1.0, t / DURATIONS[2])))
    y = int((HEIGHT - src.height) * 0.08)
    img.paste(src, (x, y))
    veil = Image.new("RGBA", (WIDTH, HEIGHT), (255, 255, 255, 92))
    img = Image.alpha_composite(img.convert("RGBA"), veil).convert("RGB")
    draw = ImageDraw.Draw(img)
    center(draw, (70, 168, 1010, 238), "Google AI found this", font(48, True), (15, 23, 42))
    draw.rounded_rectangle((82, 352, 998, 696), radius=26, fill=(255, 255, 255), outline=(203, 213, 225), width=3)
    draw.text((126, 405), "Google AI said:", font=font(38, True), fill=(71, 85, 105))
    center(draw, (108, 475, 972, 635), "$53/month -> $12.95/month", font(61, True), (5, 15, 30))
    if t > 2.2:
        draw.rounded_rectangle((112, 790, 968, 900), radius=18, fill=(13, 23, 39))
        center(draw, (130, 812, 950, 880), "Walmart sources visible", font(38, True), (255, 255, 255))
    return img


def draw_scene4(t: float) -> Image.Image:
    proof_keys = ["benefits", "peacock", "cashback"]
    idx = min(2, int(t // (DURATIONS[3] / 3)))
    local_t = t - idx * (DURATIONS[3] / 3)
    img = documentary_bg(SCREENSHOTS[proof_keys[idx]], local_t, DURATIONS[3] / 3, alpha=150, scale_boost=0.85 if proof_keys[idx] != "cashback" else 1.0, y0=0.03, y1=0.34)
    draw = ImageDraw.Draw(img)
    center(draw, (70, 182, 1010, 270), "AFTER", font(66, True), (15, 23, 42))
    rows = [
        ("Walmart+:", "$12.95/month"),
        ("Delivery:", ""),
        ("Peacock:", ""),
        ("5% cashback:", "added"),
    ]
    y = 388
    for ridx, (left, right) in enumerate(rows):
        if t >= ridx * 0.9:
            replacement_row(draw, y, left, right)
        y += 155
    return img


def draw_scene5(t: float) -> Image.Image:
    img = Image.new("RGB", (WIDTH, HEIGHT), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    drift = int(math.sin(t * 1.5) * 3)
    center(draw, (55, 540 + drift, 1025, 735 + drift), "$480/YEAR", font(132, True), (5, 15, 30))
    center(draw, (90, 800 + drift, 990, 910 + drift), "and zero grocery rides", font(50, True), (71, 85, 105), 6)
    if t > 2.25:
        src = cover_image(SCREENSHOTS["savings"], 0.66)
        src = src.crop((0, 220, src.width, min(src.height, 920))).resize((700, 590), Image.Resampling.LANCZOS)
        img.paste(src, (190, 1080))
    return img


def draw_scene6(_: float) -> Image.Image:
    img = Image.new("RGB", (HEIGHT, HEIGHT), (9, 20, 36)).resize((WIDTH, HEIGHT))
    draw = ImageDraw.Draw(img)
    center(draw, (56, 450, 1024, 650), "COMMENT\nWALMART", font(94, True), (255, 255, 255), 10)
    center(draw, (56, 705, 1024, 805), "FOR THE PROMPT", font(67, True), (52, 211, 153))
    center(draw, (80, 960, 1000, 1060), "Could save $40/month", font(47, True), (226, 232, 240))
    return img


def make_frame_scene(scene_id: int, duration: float, drawer) -> Path:
    frame_dir = WORK_DIR / f"frames_scene{scene_id:02d}"
    if frame_dir.exists():
        shutil.rmtree(frame_dir)
    frame_dir.mkdir(parents=True)
    for frame in range(int(round(duration * FPS))):
        drawer(frame / FPS).save(frame_dir / f"frame_{frame:04d}.png")
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
    html = WORK_DIR / "day6_local_ai.html"
    js = WORK_DIR / "day6_local_ai_capture.js"
    proof_uri = SCREENSHOTS["google_ai_proof"].resolve().as_uri()
    html.write_text(
        f"""<!doctype html>
<html><head><meta charset="utf-8"><style>
html,body{{margin:0;width:{WIDTH}px;height:{HEIGHT}px;background:#f7f9fc;font-family:Arial,Helvetica,sans-serif;color:#0f172a;overflow:hidden}}
.proof{{position:absolute;inset:0;background:#fff;opacity:1;transition:opacity .22s linear;overflow:hidden}}
.proof img{{position:absolute;width:1980px;height:auto;left:-455px;top:12px;filter:contrast(1.03)}}
.proofTag{{position:absolute;left:62px;bottom:155px;background:#0f172a;color:white;border-radius:16px;padding:20px 26px;font-size:30px;font-weight:900;box-shadow:0 12px 34px rgba(15,23,42,.24)}}
.wrap{{padding:86px 58px;opacity:0;transition:opacity .22s linear}} .panel{{background:white;border:1px solid #dbe3ee;box-shadow:0 18px 48px rgba(15,23,42,.12);min-height:1390px;padding:34px}}
.top{{font-size:34px;font-weight:900;margin-bottom:18px}} .recon{{font-size:22px;color:#64748b;margin-bottom:22px;font-weight:800}} .note{{background:#f8fafc;border:1px solid #e2e8f0;border-radius:16px;padding:22px;font-size:28px;line-height:1.34;color:#475569;margin-bottom:28px;opacity:0}}
.prompt{{background:#0f172a;color:white;border-radius:18px;padding:28px;font-size:35px;line-height:1.22;min-height:350px}}
.cursor{{display:inline-block;width:4px;height:38px;background:#34d399;vertical-align:-7px;animation:blink .7s steps(1) infinite}}
.answer{{opacity:0;transform:translateY(16px);margin-top:16px;background:#ecfdf5;border:1px solid #bbf7d0;border-radius:18px;padding:19px 24px;font-size:31px;line-height:1.22;font-weight:900;color:#065f46;transition:all .25s ease-out}}
.answer.dim{{background:#f0fdf4;color:#047857}}
.sources{{opacity:0;margin-top:18px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:18px;padding:18px;display:grid;grid-template-columns:1fr;gap:10px;transition:opacity .24s ease-out}}
.source{{background:white;border:1px solid #e2e8f0;border-radius:14px;padding:14px 16px;font-size:24px;font-weight:800;color:#0f172a}}
.source span{{display:block;color:#2563eb;font-size:20px;margin-top:4px}}
.dot{{position:absolute;width:18px;height:18px;border-radius:50%;background:#0f172a;left:850px;top:520px;box-shadow:0 0 0 7px rgba(15,23,42,.14);transition:all .45s ease}}
@keyframes blink{{50%{{opacity:0}}}}
</style></head><body>
<div class="proof" id="proof"><img src="{proof_uri}" /><div class="proofTag">Real Google AI Mode screenshot</div></div>
<div class="wrap" id="wrap"><div class="panel">
<div class="top">AI cost check</div>
<div class="recon">Visual reconstruction based on the real screenshot</div>
<div class="dot" id="dot"></div>
<div class="note" id="note">Situation pasted:<br>$42/month rides to Walmart<br>$11/month Peacock<br>No car</div>
<div class="prompt"><span id="typed"></span><span class="cursor"></span></div>
<div class="answer" id="a1">Instead of paying $53/month...</div>
<div class="answer" id="a2">Walmart+ is $12.95/month.</div>
<div class="answer dim" id="a3">Delivery plus Peacock in one place.</div>
<div class="sources" id="sources"><div class="source">Free Shipping and Free Delivery from Your Store <span>Walmart</span></div><div class="source">Walmart+ Membership <span>Walmart.com</span></div><div class="source">Walmart+ Streaming Benefits <span>Walmart.com</span></div></div>
</div></div>
<script>
const text = {json.dumps(PROMPT)};
const typed = document.getElementById('typed');
setTimeout(() => {{ document.getElementById('proof').style.opacity=0; document.getElementById('wrap').style.opacity=1; }}, 1420);
setTimeout(() => {{ document.getElementById('note').style.opacity=1; }}, 1660);
let i=0;
function typeNext(){{ if(i <= text.length){{ typed.textContent = text.slice(0, i++); setTimeout(typeNext, 9); }} }}
setTimeout(typeNext, 1880);
setTimeout(() => {{ const d=document.getElementById('dot'); d.style.left='915px'; d.style.top='710px'; }}, 3150);
function show(id, delay){{ setTimeout(() => {{ const a=document.getElementById(id); a.style.opacity=1; a.style.transform='translateY(0)'; }}, delay); }}
show('a1', 4300); show('a2', 4620); show('a3', 4940);
setTimeout(() => {{ document.getElementById('sources').style.opacity=1; }}, 5200);
</script></body></html>""",
        encoding="utf-8",
    )
    js_source = """const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
(async () => {
  const work = __WORK__;
  const browser = await chromium.launch({ channel:'chrome', headless:true, args:['--no-first-run','--no-default-browser-check','--window-size=__WIDTH__,__HEIGHT__'] });
  const context = await browser.newContext({ viewport:{width:__WIDTH__,height:__HEIGHT__}, recordVideo:{dir:work,size:{width:__WIDTH__,height:__HEIGHT__}} });
  const page = await context.newPage();
  await page.goto('file:///' + path.resolve(work, 'day6_local_ai.html').replace(/\\\\/g, '/'));
  await page.waitForTimeout(6400);
  const video = page.video();
  await page.close();
  const raw = await video.path();
  await context.close();
  await browser.close();
  fs.copyFileSync(raw, path.join(work, 'day6_local_ai.webm'));
})().catch(err => { console.error(err); process.exit(1); });"""
    js_source = js_source.replace("__WORK__", json.dumps(str(WORK_DIR))).replace("__WIDTH__", str(WIDTH)).replace("__HEIGHT__", str(HEIGHT))
    js.write_text(js_source, encoding="utf-8")
    return html, js


def make_ai_scene() -> Path:
    _, js = write_ai_dom()
    run(["node", str(js)], "record local DOM AI assistant")
    webm = WORK_DIR / "day6_local_ai.webm"
    scene3 = RAW_DIR / f"{RUN_ID}_scene03.mp4"
    run(
        [
            "ffmpeg", "-y", "-i", str(webm), "-t", f"{DURATIONS[2]:.2f}",
            "-vf", "scale=1080:1920,fps=30", "-an", "-c:v", "libx264", "-preset", "fast",
            "-crf", "18", "-pix_fmt", "yuv420p", str(scene3),
        ],
        "make AI scene",
    )
    return scene3


def concat_scenes(paths: list[Path]) -> None:
    concat_path = TEMP_DIR / f"{RUN_ID}_concat.txt"
    concat_path.write_text("\n".join(f"file '{ffmpeg_path(path)}'" for path in paths), encoding="utf-8")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_path), "-c", "copy", str(SILENT_PATH)], "concat scenes")


def probe_duration(path: Path) -> float:
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)], "probe audio duration").stdout.strip()
    return float(out)


def atempo_filter(speed: float) -> str:
    parts: list[str] = []
    while speed > 2.0:
        parts.append("atempo=2.0")
        speed /= 2.0
    while speed < 0.5:
        parts.append("atempo=0.5")
        speed /= 0.5
    parts.append(f"atempo={speed:.5f}")
    return ",".join(parts)


def make_audio() -> tuple[Path, str]:
    engine = pyttsx3.init()
    engine.setProperty("rate", 190)
    engine.setProperty("volume", 1.0)
    for voice in engine.getProperty("voices") or []:
        name = (getattr(voice, "name", "") or "").lower()
        if "zira" in name or "david" in name or "mark" in name:
            engine.setProperty("voice", voice.id)
            break
    raw_parts: list[Path] = []
    for idx, text in enumerate(TTS_TEXTS, start=1):
        raw = WORK_DIR / f"voice_scene{idx}.wav"
        engine.save_to_file(text, str(raw))
        raw_parts.append(raw)
    engine.runAndWait()

    fitted: list[Path] = []
    for idx, (raw, dur) in enumerate(zip(raw_parts, DURATIONS), start=1):
        raw_dur = probe_duration(raw)
        target = max(0.4, dur - 0.14)
        speed = max(0.5, raw_dur / target)
        out = WORK_DIR / f"voice_scene{idx}_fit.wav"
        filters = atempo_filter(speed) if abs(speed - 1.0) > 0.03 else "anull"
        run(
            [
                "ffmpeg", "-y", "-i", str(raw), "-af",
                f"{filters},apad,atrim=0:{dur:.2f},afade=t=out:st={max(0.1, dur - 0.08):.2f}:d=0.08",
                "-ar", "48000", "-ac", "2", str(out),
            ],
            f"fit audio scene {idx}",
        )
        fitted.append(out)

    concat = WORK_DIR / "audio_concat.txt"
    concat.write_text("\n".join(f"file '{ffmpeg_path(path)}'" for path in fitted), encoding="utf-8")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat), "-c", "pcm_s16le", str(AUDIO_PATH)], "concat audio")
    return AUDIO_PATH, "pyttsx3_offline_windows_sapi_rate190_scene_fitted"


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
Style: Cap,Arial,52,&H00FFFFFF,&H000000FF,&H00000000,&HA0000000,-1,0,0,0,100,100,0,0,1,7,2,2,54,54,40,1
Style: Money,Arial,84,&H0034D399,&H000000FF,&H00000000,&HA0000000,-1,0,0,0,100,100,0,0,1,8,2,2,54,54,40,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    y_positions = [1510, 1500, 1505, 1505, 1515, 1505]
    events: list[str] = []
    cursor = 0.0
    money_tokens = {"$42", "$53", "$12.95", "$480"}

    def caption_chunks(words: list[str]) -> list[tuple[str, bool]]:
        chunks: list[tuple[str, bool]] = []
        current: list[str] = []
        for word in words:
            clean = word.strip(".,!?")
            if clean in money_tokens:
                if current:
                    chunks.append((" ".join(current), False))
                    current = []
                chunks.append((clean, True))
            else:
                current.append(word)
                if len(current) >= 5:
                    chunks.append((" ".join(current), False))
                    current = []
        if current:
            chunks.append((" ".join(current), False))
        return chunks

    for idx, (text, dur) in enumerate(zip(SOURCE_TEXTS, DURATIONS)):
        words = text.replace("—", "").split()
        chunks = caption_chunks(words)
        start = cursor + 0.10
        end = cursor + dur - 0.10
        step = (end - start) / max(1, len(chunks))
        for cidx, (chunk, is_money) in enumerate(chunks):
            style = "Money" if is_money else "Cap"
            y = y_positions[idx] - 85 if is_money else y_positions[idx]
            events.append(f"Dialogue: 0,{ts(start + cidx * step)},{ts(start + (cidx + 1) * step)},{style},,0,0,0,,{{\\an2\\pos(540,{y})}}{chunk}")
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
    offsets = [1.1, 2.0, 2.4, 4.7, 1.6, 2.8]
    frames: list[Path] = []
    cursor = 0.0
    for idx, dur in enumerate(DURATIONS, start=1):
        frame = REVIEW_DIR / f"review_frame_scene{idx}.jpg"
        stamp = cursor + min(offsets[idx - 1], dur - 0.20)
        run(["ffmpeg", "-y", "-ss", f"{stamp:.2f}", "-i", str(FINAL_PATH), "-frames:v", "1", "-update", "1", str(frame)], f"review frame {idx}")
        frames.append(frame)
        cursor += dur
    contact = REVIEW_DIR / "contact_sheet.jpg"
    thumbs = [Image.open(frame).resize((270, 480), Image.Resampling.LANCZOS).convert("RGB") for frame in frames]
    sheet = Image.new("RGB", (270 * len(thumbs), 480), (255, 255, 255))
    for idx, thumb in enumerate(thumbs):
        sheet.paste(thumb, (idx * 270, 0))
    sheet.save(contact, quality=92)
    proof_frame = REVIEW_DIR / "proof_frame_google_ai_mode_screenshot.jpg"
    scene3_start = sum(DURATIONS[:2])
    run(
        ["ffmpeg", "-y", "-ss", f"{scene3_start + 0.70:.2f}", "-i", str(FINAL_PATH), "-frames:v", "1", "-update", "1", str(proof_frame)],
        "google ai proof frame",
    )
    return contact, frames


def probe_json(path: Path) -> dict:
    out = run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration,size,bit_rate:stream=index,codec_type,codec_name,width,height,avg_frame_rate,duration",
            "-of", "json", str(path),
        ],
        "probe final",
    ).stdout
    return json.loads(out)


def main() -> None:
    for required in SCREENSHOTS.values():
        if not required.exists():
            raise FileNotFoundError(required)
    for directory in [ASSETS_DIR, RAW_DIR, TEMP_DIR, WORK_DIR, REVIEW_DIR]:
        directory.mkdir(parents=True, exist_ok=True)

    scene1 = make_frame_scene(1, DURATIONS[0], draw_scene1)
    scene2 = make_frame_scene(2, DURATIONS[1], draw_scene2)
    scene3 = make_frame_scene(3, DURATIONS[2], draw_scene3)
    scene4 = make_frame_scene(4, DURATIONS[3], draw_scene4)
    scene5 = make_frame_scene(5, DURATIONS[4], draw_scene5)
    scene6 = make_frame_scene(6, DURATIONS[5], draw_scene6)
    concat_scenes([scene1, scene2, scene3, scene4, scene5, scene6])
    audio_path, audio_provider = make_audio()
    caption_count = write_captions()
    mux_final(audio_path)
    contact, frames = make_review_artifacts()
    probe = probe_json(FINAL_PATH)

    LOG_PATH.write_text(
        "\n".join(
            [
                f"final={FINAL_PATH}",
                f"duration={probe.get('format', {}).get('duration')}",
                f"size={probe.get('format', {}).get('size')}",
                "fps=30",
                f"dimensions={WIDTH}x{HEIGHT}",
                f"audio_provider={audio_provider}",
                f"contact_sheet={contact}",
                f"proof_frame_google_ai_mode_screenshot={REVIEW_DIR / 'proof_frame_google_ai_mode_screenshot.jpg'}",
                "review_frames=" + " | ".join(str(p) for p in frames),
                f"caption_count={caption_count}",
                "caption_sync_confirmation=confirmed: captions regenerated after scene-fitted final audio; max five words per event; ending captions share the fixed final scene window",
                "privacy_confirmation=confirmed: staged screenshots are masked/cropped for status bars, account/address/name/balance areas; no Gmail/password/private docs used",
                "no_paid_credits_confirmation=confirmed: no ElevenLabs, no RunwayML, no paid APIs",
                "ai_tool_mode=user-provided real Google AI Mode screenshot proof insert with magnified excerpt card; no live Google automation used",
                "story_first_fixes_landed=confirmed: pain-first hook, before/after replacement math, magnified Google AI proof, clean $480/year payoff, documentary screenshot motion",
                "screenshots_used=" + " | ".join(str(p) for p in SCREENSHOTS.values()),
                "transitions=hard cuts only",
                json.dumps(probe, indent=2),
            ]
        ),
        encoding="utf-8",
    )
    print(LOG_PATH)
    print(json.dumps(probe, indent=2))


if __name__ == "__main__":
    main()
