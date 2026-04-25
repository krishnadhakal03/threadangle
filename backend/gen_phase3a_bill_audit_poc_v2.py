#!/usr/bin/env python3
"""Phase 3A POC: local AI bill audit video.

Cost guardrails:
- no ElevenLabs
- no RunwayML
- no external/private bill data
- local demo visuals and pyttsx3 voice only
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pyttsx3
from PIL import Image, ImageDraw, ImageFont

from utils.video_pipeline import ASSETS_DIR, RAW_DIR, TEMP_DIR


RUN_ID = "phase3a_bill_audit_poc_v2"
FINAL_PATH = ASSETS_DIR / f"{RUN_ID}.mp4"
SILENT_PATH = RAW_DIR / f"{RUN_ID}_silent.mp4"
AUDIO_PATH = TEMP_DIR / f"{RUN_ID}.wav"
ASS_PATH = TEMP_DIR / f"{RUN_ID}.ass"
LOG_PATH = TEMP_DIR / f"{RUN_ID}_render.log"
WORK_DIR = TEMP_DIR / RUN_ID
REVIEW_DIR = ASSETS_DIR / "review" / RUN_ID

WIDTH = 1080
HEIGHT = 1920
FPS = 30
FRAME_FPS = 15
DURATIONS = [4.0, 4.0, 6.0, 8.0, 8.0, 8.0]
FINAL_DURATION = sum(DURATIONS)

SOURCE_TEXTS = [
    "You may be paying for subscriptions you forgot.",
    "One study found people guessed 86 dollars, but actually spent 219.",
    "First, list your recurring charges.",
    "Then ask AI to flag overlaps, downgrades, and bills to renegotiate.",
    "This example found three possible savings.",
    "That is 53 dollars a month, or 636 dollars a year. Comment AUDIT for the prompt.",
]

EXPENSES = [
    ("Netflix", "$22.99"),
    ("Hulu", "$17.99"),
    ("Spotify", "$11.99"),
    ("Gym", "$39.99"),
    ("Phone", "$95"),
    ("Internet", "$80"),
    ("Cloud Storage", "$9.99"),
]

PROMPT = "Find duplicate subscriptions, cheaper alternatives, and bills I should renegotiate."
AI_LINES = [
    ("Cancel overlap", "save $18/mo"),
    ("Renegotiate phone", "save $30/mo"),
    ("Downgrade storage", "save $5/mo"),
]


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


def base_bg() -> Image.Image:
    img = Image.new("RGB", (WIDTH, HEIGHT), (245, 247, 250))
    draw = ImageDraw.Draw(img)
    for y in range(HEIGHT):
        shade = 249 - int(y * 0.012)
        draw.line([(0, y), (WIDTH, y)], fill=(shade, min(255, shade + 1), min(255, shade + 4)))
    return img


def draw_browser(draw: ImageDraw.ImageDraw, title: str = "Local Bill Audit") -> tuple[int, int, int, int]:
    shell = (54, 122, 1026, 1508)
    draw.rounded_rectangle(shell, radius=34, fill=(255, 255, 255), outline=(210, 218, 230), width=3)
    draw.rounded_rectangle((54, 122, 1026, 244), radius=34, fill=(20, 28, 42))
    draw.rectangle((54, 185, 1026, 244), fill=(20, 28, 42))
    for i, color in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        x = 92 + i * 34
        draw.ellipse((x, 166, x + 20, 186), fill=color)
    draw.rounded_rectangle((210, 154, 950, 210), radius=18, fill=(245, 247, 250))
    draw.text((235, 166), title, font=font(28), fill=(71, 85, 105))
    return (82, 274, 998, 1454)


def cursor(draw: ImageDraw.ImageDraw, x: int, y: int) -> None:
    pts = [(x, y), (x, y + 48), (x + 14, y + 36), (x + 30, y + 66), (x + 44, y + 58), (x + 27, y + 31), (x + 47, y + 31)]
    draw.polygon(pts, fill=(15, 23, 42))
    draw.line(pts + [pts[0]], fill=(255, 255, 255), width=2)


def frame_scene(scene: int, progress: float) -> Image.Image:
    img = base_bg()
    draw = ImageDraw.Draw(img)

    if scene == 1:
        img = Image.new("RGB", (WIDTH, HEIGHT), (8, 13, 24))
        draw = ImageDraw.Draw(img)
        draw.rounded_rectangle((70, 360, 1010, 1138), radius=30, fill=(14, 24, 39), outline=(82, 196, 255), width=7)
        center_text(draw, (100, 420, 980, 820), "YOU MAY BE PAYING\nFOR SUBSCRIPTIONS\nYOU FORGOT", font(74, True), (255, 255, 255), 14)
        center_text(draw, (100, 900, 980, 1005), "Check recurring charges", font(48, True), (82, 196, 255))

    elif scene == 2:
        img = Image.new("RGB", (WIDTH, HEIGHT), (255, 255, 255))
        draw = ImageDraw.Draw(img)
        draw.rounded_rectangle((78, 290, 1002, 1240), radius=30, fill=(255, 255, 255), outline=(82, 196, 255), width=8)
        center_text(draw, (110, 360, 970, 460), "Subscription spending gap", font(54, True), (15, 23, 42))
        draw.text((140, 585), "People guessed:", font=font(46, True), fill=(71, 85, 105))
        draw.text((140, 655), "$86/mo", font=font(112, True), fill=(15, 23, 42))
        draw.text((140, 850), "Actual:", font=font(46, True), fill=(71, 85, 105))
        draw.text((140, 920), "$219/mo", font=font(128, True), fill=(5, 150, 105))
        center_text(draw, (110, 1110, 970, 1185), "Itemized spending was much higher", font(34, True), (29, 78, 216))

    elif scene == 3:
        area = draw_browser(draw, "local-demo://monthly-bill-audit")
        draw.text((area[0], area[1]), "Recurring charges", font=font(58, True), fill=(15, 23, 42))
        draw.text((area[0], area[1] + 78), "Sample demo data only", font=font(34), fill=(100, 116, 139))
        y = area[1] + 165
        visible = len(EXPENSES)
        for idx, (name, amount) in enumerate(EXPENSES[:visible]):
            top = y + idx * 126
            fill = (248, 250, 252) if idx % 2 == 0 else (255, 255, 255)
            draw.rounded_rectangle((area[0], top, area[2], top + 96), radius=18, fill=fill, outline=(226, 232, 240), width=2)
            draw.text((area[0] + 34, top + 26), name, font=font(42, True), fill=(15, 23, 42))
            draw.text((area[2] - 210, top + 24), amount, font=font(44, True), fill=(15, 23, 42))
        cx = area[2] - 170 + int(70 * progress)
        cy = y + min(int(progress * len(EXPENSES)), len(EXPENSES) - 1) * 126 + 36
        cursor(draw, cx, cy)

    elif scene == 4:
        area = draw_browser(draw, "local-demo://ai-bill-auditor")
        draw.text((area[0], area[1]), "AI Bill Auditor", font=font(58, True), fill=(15, 23, 42))
        box = (area[0], area[1] + 130, area[2], area[1] + 620)
        draw.rounded_rectangle(box, radius=24, fill=(248, 250, 252), outline=(203, 213, 225), width=3)
        draw.text((box[0] + 34, box[1] + 30), "Prompt", font=font(34, True), fill=(71, 85, 105))
        typed = PROMPT[: int(len(PROMPT) * min(1.0, progress / 0.48))]
        lines = wrap_words(draw, typed + ("|" if progress < 0.55 else ""), font(42, True), box[2] - box[0] - 70, 4)
        ty = box[1] + 92
        for line in lines:
            draw.text((box[0] + 34, ty), line, font=font(42, True), fill=(15, 23, 42))
            ty += 58
        button = (area[0], area[1] + 690, area[0] + 280, area[1] + 780)
        draw.rounded_rectangle(button, radius=22, fill=(37, 99, 235))
        center_text(draw, button, "Audit bill", font(36, True), (255, 255, 255))
        if progress > 0.58:
            cursor(draw, button[2] - 62, button[1] + 18)

    elif scene == 5:
        area = draw_browser(draw, "local-demo://ai-results")
        draw.text((area[0], area[1]), "Audit results", font=font(58, True), fill=(15, 23, 42))
        draw.rounded_rectangle((area[0], area[1] + 95, area[2], area[1] + 170), radius=18, fill=(239, 246, 255))
        draw.text((area[0] + 28, area[1] + 115), "AI found possible monthly savings", font=font(34, True), fill=(29, 78, 216))
        visible = min(3, 1 + int(progress * 5.0))
        for idx, (title, sub) in enumerate(AI_LINES[:visible]):
            top = area[1] + 245 + idx * 245
            draw.rounded_rectangle((area[0], top, area[2], top + 180), radius=24, fill=(255, 255, 255), outline=(203, 213, 225), width=3)
            draw.text((area[0] + 34, top + 34), title, font=font(44, True), fill=(15, 23, 42))
            draw.text((area[0] + 34, top + 100), sub, font=font(48, True), fill=(5, 150, 105))
        if visible < 3:
            draw.text((area[0], area[1] + 1040), "Checking recurring patterns...", font=font(34, True), fill=(100, 116, 139))

    elif scene == 6:
        img = Image.new("RGB", (WIDTH, HEIGHT), (255, 255, 255))
        draw = ImageDraw.Draw(img)
        draw.rounded_rectangle((58, 130, 1022, 1415), radius=32, fill=(255, 255, 255), outline=(82, 196, 255), width=10)
        center_text(draw, (100, 210, 980, 305), "POSSIBLE SAVINGS", font(58, True), (15, 23, 42))
        center_text(draw, (100, 405, 980, 575), "$53/month", font(122, True), (5, 150, 105))
        draw.rounded_rectangle((100, 680, 980, 980), radius=28, fill=(10, 16, 28))
        center_text(draw, (120, 705, 960, 850), "$636/year", font(124, True), (255, 255, 255))
        center_text(draw, (120, 855, 960, 930), "Potential annual savings", font(38, True), (82, 196, 255))
        draw.rounded_rectangle((100, 1070, 980, 1320), radius=26, fill=(14, 24, 39))
        center_text(draw, (120, 1100, 960, 1190), "COMMENT AUDIT", font(64, True), (255, 255, 255))
        center_text(draw, (120, 1210, 960, 1280), "FOR THE PROMPT", font(48, True), (82, 196, 255))

    return img


def wrap_words(draw: ImageDraw.ImageDraw, text: str, fnt, max_width: int, max_lines: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        width = draw.textbbox((0, 0), candidate, font=fnt)[2]
        if width <= max_width or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
        if len(lines) >= max_lines:
            break
    if current and len(lines) < max_lines:
        lines.append(current)
    return lines


def render_scene(scene: int, duration: float) -> Path:
    frame_dir = WORK_DIR / f"scene_{scene:02d}_frames"
    if frame_dir.exists():
        shutil.rmtree(frame_dir)
    frame_dir.mkdir(parents=True, exist_ok=True)
    frame_count = int(duration * FRAME_FPS)
    for idx in range(frame_count):
        progress = idx / max(1, frame_count - 1)
        frame_scene(scene, progress).save(frame_dir / f"frame_{idx:04d}.jpg", quality=94)
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
            f"fps={FPS},format=yuv420p",
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            str(out),
        ],
        f"render scene {scene}",
    )
    return out


def concat_scenes(paths: list[Path]) -> None:
    concat_path = TEMP_DIR / f"{RUN_ID}_concat.txt"
    concat_path.write_text("\n".join(f"file '{ffmpeg_path(path)}'" for path in paths), encoding="utf-8")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_path), "-c", "copy", str(SILENT_PATH)], "concat scenes")


def make_audio() -> str:
    engine = pyttsx3.init()
    engine.setProperty("rate", 166)
    engine.setProperty("volume", 1.0)
    for voice in engine.getProperty("voices") or []:
        name = (getattr(voice, "name", "") or "").lower()
        if "david" in name or "mark" in name or "zira" in name:
            engine.setProperty("voice", voice.id)
            break
    engine.save_to_file(" ".join(SOURCE_TEXTS), str(AUDIO_PATH))
    engine.runAndWait()
    if not AUDIO_PATH.exists() or AUDIO_PATH.stat().st_size < 1000:
        raise RuntimeError("audio generation failed")
    return "pyttsx3_offline_rate166"


def write_captions() -> int:
    def ts(seconds: float) -> str:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = seconds % 60
        return f"{h}:{m:02d}:{s:05.2f}"

    def split_lines(text: str) -> str:
        words = text.split()
        return r"\N".join(" ".join(words[i : i + 5]) for i in range(0, len(words), 5))

    starts: list[float] = []
    cursor_time = 0.0
    for duration in DURATIONS:
        starts.append(cursor_time)
        cursor_time += duration
    y_positions = [1500, 1510, 1550, 1535, 1535, 1630]
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {WIDTH}
PlayResY: {HEIGHT}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Arial,54,&H00FFFFFF,&H000000FF,&H00000000,&H9A000000,-1,0,0,0,100,100,0,0,1,7,2,2,54,54,40,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    for idx, text in enumerate(SOURCE_TEXTS):
        safe = split_lines(text).replace("{", "").replace("}", "")
        start = starts[idx] + 0.12
        end = starts[idx] + DURATIONS[idx] - 0.12
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
            "-filter_complex",
            f"[0:v]ass='{ass_path(ASS_PATH)}'[v];[1:a]apad,atrim=0:{FINAL_DURATION:.2f}[a]",
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
            "2600k",
            "-minrate",
            "2600k",
            "-maxrate",
            "2600k",
            "-bufsize",
            "5200k",
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
    contact = REVIEW_DIR / "contact_sheet.jpg"
    run(["ffmpeg", "-y", "-i", str(FINAL_PATH), "-vf", "fps=1/6,scale=270:-1,tile=6x1", "-frames:v", "1", "-update", "1", str(contact)], "contact sheet")
    frames: list[Path] = []
    cursor_time = 0.0
    for idx, duration in enumerate(DURATIONS, start=1):
        frame = REVIEW_DIR / f"review_frame_scene{idx}.jpg"
        shot_time = cursor_time + min(duration / 2, duration - 0.25)
        run(["ffmpeg", "-y", "-ss", f"{shot_time:.2f}", "-i", str(FINAL_PATH), "-frames:v", "1", "-update", "1", str(frame)], f"review frame {idx}")
        frames.append(frame)
        cursor_time += duration
    return contact, frames


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
    for directory in [ASSETS_DIR, RAW_DIR, TEMP_DIR, WORK_DIR, REVIEW_DIR]:
        directory.mkdir(parents=True, exist_ok=True)
    scene_paths = [render_scene(idx, duration) for idx, duration in enumerate(DURATIONS, start=1)]
    concat_scenes(scene_paths)
    audio_provider = make_audio()
    caption_count = write_captions()
    mux_final()
    contact, frames = make_review_artifacts()
    probe = probe_json(FINAL_PATH)
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
                "caption_integrity=confirmed: captions use SOURCE_TEXTS only, max five words per line",
                "privacy_confirmation=confirmed: local demo data only; no real bills, bank data, Gmail, passwords, or private documents",
                "paid_credits=confirmed none: no ElevenLabs, no RunwayML, no paid APIs",
                "motion=confirmed: cursor movement in scene 3; typing in scene 4; AI output reveals line by line in scene 5",
                "transitions=hard cuts only; no fades",
                json.dumps(probe, indent=2),
            ]
        ),
        encoding="utf-8",
    )
    print(LOG_PATH)
    print(json.dumps(probe, indent=2))


if __name__ == "__main__":
    main()
