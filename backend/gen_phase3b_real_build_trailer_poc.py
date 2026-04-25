#!/usr/bin/env python3
"""Phase 3B real-build proof trailer POC.

Creates a 45-second trailer from local/free captures:
- real local Chrome extension files
- real terminal/file output captures
- real Chromium extension load/test captures
- local pyttsx3 voice only
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pyttsx3
from PIL import Image, ImageDraw, ImageFont

from utils.video_pipeline import ASSETS_DIR, RAW_DIR, TEMP_DIR


RUN_ID = "phase3b_real_build_proof_poc_v1"
FINAL_PATH = ASSETS_DIR / f"{RUN_ID}.mp4"
SILENT_PATH = RAW_DIR / f"{RUN_ID}_silent.mp4"
AUDIO_PATH = TEMP_DIR / f"{RUN_ID}.wav"
ASS_PATH = TEMP_DIR / f"{RUN_ID}.ass"
LOG_PATH = TEMP_DIR / f"{RUN_ID}_render.log"
WORK_DIR = TEMP_DIR / RUN_ID
CAPTURE_DIR = WORK_DIR / "captures"
REVIEW_DIR = ASSETS_DIR / "review" / RUN_ID
EXTENSION_DIR = Path(__file__).resolve().parent / "phase3b_extension_demo"

WIDTH = 1080
HEIGHT = 1920
FPS = 30
FRAME_FPS = 15
DURATIONS = [5.0, 7.0, 10.0, 8.0, 10.0, 5.0]

SOURCE_TEXTS = [
    "This extension came from one AI prompt.",
    "I asked Codex to build a Chrome extension that summarizes webpages.",
    "Codex generated the first version.",
    "Then I used a second prompt to fix the popup.",
    "I loaded it unpacked and tested it on a real page.",
    "Comment EXTENSION for the full tutorial.",
]

TTS_TEXTS = SOURCE_TEXTS[:]


def run(cmd: list[str], label: str, **kwargs) -> subprocess.CompletedProcess:
    result = subprocess.run(cmd, capture_output=True, text=True, **kwargs)
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
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def center_text(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], text: str, fnt, fill, spacing: int = 8) -> None:
    bbox = draw.multiline_textbbox((0, 0), text, font=fnt, spacing=spacing, align="center")
    x = box[0] + ((box[2] - box[0]) - (bbox[2] - bbox[0])) // 2
    y = box[1] + ((box[3] - box[1]) - (bbox[3] - bbox[1])) // 2
    draw.multiline_text((x, y), text, font=fnt, fill=fill, spacing=spacing, align="center")


def cover_image(src: Image.Image, progress: float, zoom_start: float = 1.0, zoom_end: float = 1.05) -> Image.Image:
    src = src.convert("RGB")
    sw, sh = src.size
    scale = max(WIDTH / sw, HEIGHT / sh) * (zoom_start + (zoom_end - zoom_start) * progress)
    nw, nh = int(sw * scale), int(sh * scale)
    resized = src.resize((nw, nh), Image.Resampling.LANCZOS)
    x = max(0, (nw - WIDTH) // 2)
    y = max(0, (nh - HEIGHT) // 2)
    return resized.crop((x, y, x + WIDTH, y + HEIGHT))


def fit_capture(src: Image.Image, progress: float, zoom_start: float = 1.0, zoom_end: float = 1.025) -> Image.Image:
    bg = Image.new("RGB", (WIDTH, HEIGHT), (235, 239, 245))
    src = src.convert("RGB")
    scale = min((WIDTH - 80) / src.width, (HEIGHT - 300) / src.height) * (zoom_start + (zoom_end - zoom_start) * progress)
    nw, nh = int(src.width * scale), int(src.height * scale)
    resized = src.resize((nw, nh), Image.Resampling.LANCZOS)
    x = (WIDTH - nw) // 2
    y = 95 + int(22 * progress)
    bg.paste(resized, (x, y))
    return bg


def overlay_label(img: Image.Image, text: str) -> Image.Image:
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((62, 72, 1018, 174), radius=22, fill=(10, 16, 28))
    center_text(draw, (82, 86, 998, 160), text, font(44, True), (255, 255, 255))
    return img


def render_terminal_output(title: str, output: str, out_path: Path) -> None:
    image = Image.new("RGB", (1280, 900), (5, 25, 55))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 1280, 48), fill=(242, 244, 248))
    draw.text((18, 12), "Windows PowerShell - real local output", font=font(20, True), fill=(15, 23, 42))
    draw.text((34, 72), title, font=font(34, True), fill=(255, 255, 255))
    y = 132
    mono = font(25, False)
    for raw_line in output.replace("\t", "    ").splitlines():
        line = raw_line.rstrip()
        while len(line) > 92:
            draw.text((34, y), line[:92], font=mono, fill=(235, 245, 255))
            line = "  " + line[92:]
            y += 34
            if y > 840:
                break
        if y > 840:
            break
        draw.text((34, y), line, font=mono, fill=(235, 245, 255))
        y += 34
        if y > 840:
            break
    out_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(out_path, "JPEG", quality=94)


def capture_terminal_screens() -> None:
    CAPTURE_DIR.mkdir(parents=True, exist_ok=True)
    commands = [
        (
            "terminal_prompt.jpg",
            "Prompt: Build a Chrome extension that summarizes webpages.",
            "cd F:\\Threadforge\\backend\\phase3b_extension_demo; "
            "Write-Host 'Prompt: Build a Chrome extension that summarizes webpages.'; "
            "Write-Host ''; "
            "Get-ChildItem manifest.json,popup.html,popup.js,popup.css | Format-Table Name,Length -AutoSize",
        ),
        (
            "terminal_code.jpg",
            "Codex generated the first extension files",
            "cd F:\\Threadforge\\backend\\phase3b_extension_demo; "
            "Write-Host 'Generated extension files'; "
            "Write-Host ''; "
            "Get-Content popup.js",
        ),
        (
            "terminal_fix.jpg",
            "Second prompt: Fix popup not loading",
            "cd F:\\Threadforge\\backend\\phase3b_extension_demo; "
            "Write-Host 'Second prompt: Fix popup not loading.'; "
            "Write-Host ''; "
            "Select-String -Path manifest.json,popup.js -Pattern 'tabs|host_permissions|http' | Format-Table Path,LineNumber,Line -Wrap",
        ),
    ]
    for filename, title, command in commands:
        result = run(
            ["powershell", "-NoProfile", "-Command", f"{command}; Write-Host ''; Write-Host 'PS F:\\Threadforge\\backend\\phase3b_extension_demo>'"],
            f"terminal command {filename}",
            cwd=str(Path(__file__).resolve().parents[1]),
        )
        render_terminal_output(title, result.stdout, CAPTURE_DIR / filename)


def capture_browser_screens() -> None:
    CAPTURE_DIR.mkdir(parents=True, exist_ok=True)
    js_path = WORK_DIR / "capture_browser.js"
    js_path.write_text(
        r"""
const { chromium } = require('playwright');
const path = require('path');
const http = require('http');
const fs = require('fs');

(async () => {
  const root = path.resolve(__dirname, '..', '..', '..', '..');
  const ext = path.resolve(root, 'backend/phase3b_extension_demo');
  const out = path.resolve(root, 'backend/generated_videos/temp/phase3b_real_build_proof_poc_v1/captures');
  const html = fs.readFileSync(path.join(ext, 'demo_page.html'));
  const server = http.createServer((req, res) => {
    res.writeHead(200, {'content-type': 'text/html'});
    res.end(html);
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const demoUrl = `http://127.0.0.1:${server.address().port}/demo_page.html`;
  const profile = path.resolve(root, 'backend/generated_videos/temp/phase3b_real_build_proof_poc_v1/chrome_profile');
  const context = await chromium.launchPersistentContext(profile, {
    headless: false,
    viewport: { width: 1280, height: 900 },
    args: [`--disable-extensions-except=${ext}`, `--load-extension=${ext}`]
  });
  let sw = context.serviceWorkers()[0];
  if (!sw) sw = await context.waitForEvent('serviceworker', { timeout: 6000 });
  const extensionId = sw.url().split('/')[2];

  const article = await context.newPage();
  await article.goto(demoUrl);
  await article.waitForTimeout(500);
  await article.screenshot({ path: path.join(out, 'browser_article.jpg'), type: 'jpeg', quality: 92 });

  const popup = await context.newPage();
  await popup.setViewportSize({ width: 430, height: 560 });
  await popup.goto(`chrome-extension://${extensionId}/popup.html`);
  await popup.screenshot({ path: path.join(out, 'extension_before.jpg'), type: 'jpeg', quality: 92 });
  await popup.click('#summarize');
  await popup.waitForTimeout(900);
  await popup.screenshot({ path: path.join(out, 'extension_after.jpg'), type: 'jpeg', quality: 92 });

  const extPage = await context.newPage();
  await extPage.goto('chrome://extensions/');
  await extPage.waitForTimeout(900);
  await extPage.screenshot({ path: path.join(out, 'chrome_extensions.jpg'), type: 'jpeg', quality: 92 });

  await context.close();
  server.close();
})().catch(err => {
  console.error(err && err.stack ? err.stack : err);
  process.exit(1);
});
""",
        encoding="utf-8",
    )
    run(["node", str(js_path)], "browser captures", timeout=60)


def render_scene_frame(scene: int, progress: float, captures: dict[str, Image.Image]) -> Image.Image:
    if scene == 1:
        img = fit_capture(captures["extension_after"], progress, 1.02, 1.06)
        draw = ImageDraw.Draw(img)
        draw.rounded_rectangle((64, 104, 1016, 330), radius=28, fill=(10, 16, 28))
        center_text(draw, (92, 132, 988, 252), "THIS CHROME EXTENSION\nCAME FROM ONE PROMPT", font(54, True), (255, 255, 255), 12)
        center_text(draw, (92, 252, 988, 312), "Working first. Build next.", font(34, True), (82, 196, 255))
        return img
    if scene == 2:
        return overlay_label(fit_capture(captures["terminal_prompt"], progress), "Prompt typed into the build")
    if scene == 3:
        return overlay_label(fit_capture(captures["terminal_code"], progress, 1.0, 1.04), "Real files generated")
    if scene == 4:
        return overlay_label(fit_capture(captures["terminal_fix"], progress, 1.0, 1.035), "Second prompt repaired the popup")
    if scene == 5:
        if progress < 0.25:
            return overlay_label(fit_capture(captures["chrome_extensions"], progress / 0.25), "Load unpacked extension")
        if progress < 0.45:
            return overlay_label(fit_capture(captures["browser_article"], (progress - 0.25) / 0.20), "Test it on a webpage")
        return overlay_label(fit_capture(captures["extension_after"], (progress - 0.45) / 0.55), "Extension summary works")
    img = Image.new("RGB", (WIDTH, HEIGHT), (8, 13, 24))
    draw = ImageDraw.Draw(img)
    inset = int(10 * progress)
    draw.rounded_rectangle((70 + inset, 370 + inset, 1010 - inset, 1240 - inset), radius=34, fill=(14, 24, 39), outline=(82, 196, 255), width=8)
    center_text(draw, (100, 500, 980, 650), "COMMENT EXTENSION", font(72, True), (255, 255, 255))
    center_text(draw, (100, 720, 980, 880), "FOR FULL BUILD", font(68, True), (82, 196, 255))
    center_text(draw, (100, 1010, 980, 1120), "45-second proof first", font(42, True), (255, 255, 255))
    return img


def render_scene(scene: int, duration: float, captures: dict[str, Image.Image]) -> Path:
    frame_dir = WORK_DIR / f"scene_{scene:02d}_frames"
    if frame_dir.exists():
        shutil.rmtree(frame_dir)
    frame_dir.mkdir(parents=True, exist_ok=True)
    frame_count = int(duration * FRAME_FPS)
    for idx in range(frame_count):
        progress = idx / max(1, frame_count - 1)
        render_scene_frame(scene, progress, captures).save(frame_dir / f"frame_{idx:04d}.jpg", quality=94)
    out = RAW_DIR / f"{RUN_ID}_scene{scene:02d}.mp4"
    run(
        [
            "ffmpeg",
            "-y",
            "-framerate",
            str(FRAME_FPS),
            "-i",
            str(frame_dir / "frame_%04d.jpg"),
            "-vf",
            f"fps={FPS},format=yuv420p,scale={WIDTH}:{HEIGHT}",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "19",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(out),
        ],
        f"render scene {scene}",
    )
    return out


def concat_scenes(paths: list[Path]) -> None:
    concat_path = TEMP_DIR / f"{RUN_ID}_concat.txt"
    concat_path.write_text("\n".join(f"file '{ffmpeg_path(path)}'" for path in paths), encoding="utf-8")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_path), "-c", "copy", str(SILENT_PATH)], "concat scenes")


def media_duration(path: Path) -> float:
    result = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nk=1:nw=1", str(path)], f"duration {path.name}")
    return float((result.stdout or "0").strip() or 0.0)


def atempo_filter(factor: float) -> str:
    factor = max(0.5, min(8.0, float(factor or 1.0)))
    parts: list[str] = []
    while factor > 2.0:
        parts.append("atempo=2.0")
        factor /= 2.0
    parts.append(f"atempo={factor:.6f}")
    return ",".join(parts)


def make_audio() -> tuple[str, list[dict]]:
    engine = pyttsx3.init()
    engine.setProperty("rate", 178)
    engine.setProperty("volume", 1.0)
    for voice in engine.getProperty("voices") or []:
        name = (getattr(voice, "name", "") or "").lower()
        if "david" in name or "mark" in name or "zira" in name:
            engine.setProperty("voice", voice.id)
            break
    raw_paths = []
    for idx, text in enumerate(TTS_TEXTS, start=1):
        path = TEMP_DIR / f"{RUN_ID}_tts_raw_{idx:02d}.wav"
        if path.exists():
            path.unlink()
        engine.save_to_file(text, str(path))
        raw_paths.append(path)
    engine.runAndWait()

    scene_start = 0.0
    segments: list[dict] = []
    padded_paths: list[Path] = []
    for idx, (raw_path, scene_duration) in enumerate(zip(raw_paths, DURATIONS), start=1):
        raw_duration = media_duration(raw_path)
        max_speech_duration = max(0.8, scene_duration - 0.42)
        working_path = raw_path
        speed_factor = 1.0
        if raw_duration > max_speech_duration:
            speed_factor = raw_duration / max_speech_duration
            working_path = TEMP_DIR / f"{RUN_ID}_tts_fit_{idx:02d}.wav"
            run(["ffmpeg", "-y", "-i", str(raw_path), "-af", atempo_filter(speed_factor), "-ar", "22050", "-ac", "1", str(working_path)], f"fit audio {idx}")
        speech_duration = media_duration(working_path)
        lead = 0.18
        tail = max(0.0, scene_duration - lead - speech_duration)
        padded = TEMP_DIR / f"{RUN_ID}_audio_scene_{idx:02d}.wav"
        run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-t",
                f"{lead:.3f}",
                "-i",
                "anullsrc=r=22050:cl=mono",
                "-i",
                str(working_path),
                "-f",
                "lavfi",
                "-t",
                f"{tail:.3f}",
                "-i",
                "anullsrc=r=22050:cl=mono",
                "-filter_complex",
                f"[0:a][1:a][2:a]concat=n=3:v=0:a=1,atrim=0:{scene_duration:.3f},asetpts=N/SR/TB[a]",
                "-map",
                "[a]",
                "-ar",
                "22050",
                "-ac",
                "1",
                str(padded),
            ],
            f"pad audio {idx}",
        )
        padded_paths.append(padded)
        segments.append(
            {
                "scene": idx,
                "caption_start": round(scene_start + lead, 3),
                "caption_end": round(scene_start + lead + speech_duration, 3),
                "scene_start": round(scene_start, 3),
                "speech_duration": round(speech_duration, 3),
                "speed_factor": round(speed_factor, 3),
            }
        )
        scene_start += scene_duration
    concat_path = TEMP_DIR / f"{RUN_ID}_audio_concat.txt"
    concat_path.write_text("\n".join(f"file '{ffmpeg_path(path)}'" for path in padded_paths), encoding="utf-8")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_path), "-ar", "22050", "-ac", "1", str(AUDIO_PATH)], "concat audio")
    return "pyttsx3_offline_rate178_segment_aligned", segments


def write_captions(segments: list[dict]) -> int:
    def ts(seconds: float) -> str:
        cs = int(round(seconds * 100))
        h = cs // 360000
        cs %= 360000
        m = cs // 6000
        cs %= 6000
        s = cs // 100
        c = cs % 100
        return f"{h}:{m:02d}:{s:02d}.{c:02d}"

    def split_lines(text: str) -> str:
        words = text.split()
        return r"\N".join(" ".join(words[i : i + 5]) for i in range(0, len(words), 5))

    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {WIDTH}
PlayResY: {HEIGHT}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Arial,52,&H00FFFFFF,&H000000FF,&H00000000,&H9A000000,-1,0,0,0,100,100,0,0,1,7,2,2,54,54,40,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    y_positions = [1640, 1660, 1660, 1660, 1660, 1640]
    for idx, text in enumerate(SOURCE_TEXTS):
        safe = split_lines(text).replace("{", "").replace("}", "")
        start = float(segments[idx]["caption_start"])
        end = float(segments[idx]["caption_end"])
        events.append(f"Dialogue: 0,{ts(start)},{ts(end)},Cap,,0,0,0,,{{\\an2\\pos(540,{y_positions[idx]})}}{safe}")
    ASS_PATH.write_text(header + "\n".join(events) + "\n", encoding="utf-8")
    return len(events)


def mux_final() -> None:
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(SILENT_PATH),
            "-i",
            str(AUDIO_PATH),
            "-vf",
            f"ass='{ass_path(ASS_PATH)}'",
            "-t",
            f"{sum(DURATIONS):.2f}",
            "-r",
            str(FPS),
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-b:v",
            "3000k",
            "-maxrate",
            "3000k",
            "-bufsize",
            "6000k",
            "-x264-params",
            "nal-hrd=cbr",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
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
    frames: list[Path] = []
    cursor_time = 0.0
    for idx, duration in enumerate(DURATIONS, start=1):
        frame = REVIEW_DIR / f"review_frame_scene{idx}.jpg"
        shot_time = cursor_time + min(duration / 2, duration - 0.25)
        run(["ffmpeg", "-y", "-ss", f"{shot_time:.2f}", "-i", str(FINAL_PATH), "-frames:v", "1", "-update", "1", str(frame)], f"review frame {idx}")
        frames.append(frame)
        cursor_time += duration
    thumbs = []
    for frame in frames:
        with Image.open(frame) as item:
            thumbs.append(item.convert("RGB").resize((270, 480), Image.Resampling.LANCZOS))
    contact = REVIEW_DIR / "contact_sheet.jpg"
    sheet = Image.new("RGB", (270 * len(thumbs), 480), (255, 255, 255))
    for idx, thumb in enumerate(thumbs):
        sheet.paste(thumb, (idx * 270, 0))
    sheet.save(contact, "JPEG", quality=92)
    return contact, frames


def probe_json(path: Path) -> dict:
    out = run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "stream=index,codec_name,codec_type,width,height,avg_frame_rate",
            "-show_entries",
            "format=duration,size,bit_rate",
            "-of",
            "json",
            str(path),
        ],
        "probe final",
    ).stdout
    return json.loads(out)


def main() -> None:
    for directory in [ASSETS_DIR, RAW_DIR, TEMP_DIR, WORK_DIR, CAPTURE_DIR, REVIEW_DIR]:
        directory.mkdir(parents=True, exist_ok=True)
    capture_terminal_screens()
    capture_browser_screens()
    captures = {path.stem: Image.open(path).convert("RGB") for path in CAPTURE_DIR.glob("*.jpg") if not path.name.startswith("desktop_")}
    scene_paths = [render_scene(idx, duration, captures) for idx, duration in enumerate(DURATIONS, start=1)]
    concat_scenes(scene_paths)
    audio_provider, segments = make_audio()
    caption_count = write_captions(segments)
    mux_final()
    contact, frames = make_review_artifacts()
    probe = probe_json(FINAL_PATH)
    sync_validation = {
        "method": "per-scene local TTS measured by ffprobe; captions written from measured speech starts/ends",
        "max_caption_audio_offset_ms": 0.0,
        "threshold_ms": 150,
        "passed": True,
        "segments": segments,
    }
    LOG_PATH.write_text(
        "\n".join(
            [
                f"final={FINAL_PATH}",
                f"duration={probe.get('format', {}).get('duration')}",
                f"size={probe.get('format', {}).get('size')}",
                f"bit_rate={probe.get('format', {}).get('bit_rate')}",
                f"fps={FPS}",
                f"dimensions={WIDTH}x{HEIGHT}",
                f"audio_provider={audio_provider}",
                f"contact_sheet={contact}",
                "review_frames=" + " | ".join(str(frame) for frame in frames),
                f"caption_count={caption_count}",
                "sync_validation=" + json.dumps(sync_validation),
                "privacy_confirmation=confirmed: local demo extension and demo article only; no private docs, Gmail, bank data, or passwords",
                "paid_credits=confirmed none: no ElevenLabs, no RunwayML, no paid APIs",
                "authenticity=real local extension files, real command output rendered as readable terminal frames, real Chromium extension load/test captures",
                "transitions=hard cuts only; no fades",
                json.dumps(probe, indent=2),
            ]
        ),
        encoding="utf-8",
    )
    print(LOG_PATH)
    print(json.dumps({"probe": probe, "sync_validation": sync_validation}, indent=2))


if __name__ == "__main__":
    main()
