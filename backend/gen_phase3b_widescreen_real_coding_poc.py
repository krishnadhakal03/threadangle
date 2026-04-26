#!/usr/bin/env python3
"""Assemble Phase 3B widescreen real-coding POC from real captures.

Inputs are captured footage:
- VS Code/Codex/terminal desktop recording
- Chromium extension load/test desktop recording

No paid APIs, no ElevenLabs, no RunwayML.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pyttsx3
from PIL import Image, ImageDraw, ImageFont

from utils.video_pipeline import ASSETS_DIR, RAW_DIR, TEMP_DIR


RUN_ID = "phase3b_widescreen_real_coding_poc_v3"
WIDTH = 1920
HEIGHT = 1080
FPS = 30
WORK_DIR = TEMP_DIR / RUN_ID
REVIEW_DIR = ASSETS_DIR / "review" / RUN_ID
CAPTURE_DIR = TEMP_DIR / "phase3b_widescreen_real_coding_poc_v1"
FINAL_PATH = ASSETS_DIR / f"{RUN_ID}.mp4"
SILENT_PATH = RAW_DIR / f"{RUN_ID}_silent.mp4"
AUDIO_PATH = TEMP_DIR / f"{RUN_ID}.wav"
ASS_PATH = TEMP_DIR / f"{RUN_ID}.ass"
LOG_PATH = TEMP_DIR / f"{RUN_ID}_render.log"
PROOF_PATH = TEMP_DIR / f"{RUN_ID}_proof.json"

VSCODE_CAPTURE = CAPTURE_DIR / "vscode_real_capture.mp4"
BROWSER_CAPTURE = CAPTURE_DIR / "browser_real_capture.mp4"

SEGMENTS = [
    {
        "name": "hook_extension_working",
        "source": BROWSER_CAPTURE,
        "start": 22.0,
        "duration": 3.0,
        "caption": "Can one AI prompt build a Chrome extension?",
        "overlay": "CAN ONE AI PROMPT\nBUILD A CHROME EXTENSION?",
        "requirement": "extension working on webpage",
    },
    {
        "name": "wow_payoff_summary",
        "source": BROWSER_CAPTURE,
        "start": 24.0,
        "duration": 4.0,
        "caption": "It turns a long article into a concise summary.",
        "overlay": "LONG ARTICLE\nTO CLEAN SUMMARY",
        "requirement": "extension working on webpage",
    },
    {
        "name": "vscode_editing_live",
        "source": VSCODE_CAPTURE,
        "start": 0.0,
        "duration": 3.0,
        "caption": "Now rewind to the real build.",
        "requirement": "VS Code editing",
    },
    {
        "name": "vscode_file_tree",
        "source": VSCODE_CAPTURE,
        "start": 3.5,
        "duration": 3.0,
        "caption": "The extension files are real.",
        "requirement": "code generation",
    },
    {
        "name": "codex_prompt_start",
        "source": VSCODE_CAPTURE,
        "start": 8.0,
        "duration": 3.5,
        "caption": "I typed the prompt into Codex.",
        "requirement": "prompt typed into Codex",
    },
    {
        "name": "codex_prompt_full",
        "source": VSCODE_CAPTURE,
        "start": 12.0,
        "duration": 3.5,
        "caption": "Build a summarizer from one prompt.",
        "requirement": "prompt typed into Codex",
    },
    {
        "name": "load_unpacked",
        "source": BROWSER_CAPTURE,
        "start": 7.0,
        "duration": 3.5,
        "caption": "Then I loaded it unpacked in Chrome.",
        "requirement": "load unpacked extension in browser",
    },
    {
        "name": "bug_terminal_error",
        "source": VSCODE_CAPTURE,
        "start": 22.0,
        "duration": 3.5,
        "caption": "The first test hit a popup bug.",
        "overlay": "BUG:\nPOPUP COULD NOT\nFIND THE PAGE",
        "requirement": "terminal command run",
    },
    {
        "name": "fix_prompt_terminal",
        "source": VSCODE_CAPTURE,
        "start": 26.0,
        "duration": 3.5,
        "caption": "So I asked for a fix.",
        "overlay": "FIX:\nTARGET THE OPEN TAB",
        "requirement": "terminal command run",
    },
    {
        "name": "terminal_command_run",
        "source": VSCODE_CAPTURE,
        "start": 30.0,
        "duration": 3.0,
        "caption": "Then I ran the command again.",
        "requirement": "terminal command run",
    },
    {
        "name": "demo_webpage",
        "source": BROWSER_CAPTURE,
        "start": 12.0,
        "duration": 3.5,
        "caption": "The test page stayed local.",
        "requirement": "extension working on webpage",
    },
    {
        "name": "browser_summary_click",
        "source": BROWSER_CAPTURE,
        "start": 18.0,
        "duration": 3.5,
        "caption": "Then I clicked summarize.",
        "requirement": "extension working on webpage",
    },
    {
        "name": "browser_summary_result",
        "source": BROWSER_CAPTURE,
        "start": 22.0,
        "duration": 4.0,
        "caption": "The extension read the page.",
        "overlay": "WORKING SUMMARY",
        "requirement": "extension working on webpage",
    },
    {
        "name": "closing_extension_result",
        "source": BROWSER_CAPTURE,
        "start": 26.0,
        "duration": 3.5,
        "caption": "Next I will build bigger tools with AI.",
        "overlay": "BIGGER AI TOOLS NEXT",
        "requirement": "extension working on webpage",
    },
    {
        "name": "closing_full_build_tease",
        "source": BROWSER_CAPTURE,
        "start": 22.0,
        "duration": 3.0,
        "caption": "Comment EXTENSION for the full build.",
        "overlay": "COMMENT EXTENSION\nFOR FULL BUILD",
        "requirement": "extension working on webpage",
    },
]

CTA_DURATION = 4.5


def run(cmd: list[str], label: str, **kwargs) -> subprocess.CompletedProcess:
    result = subprocess.run(cmd, capture_output=True, text=True, **kwargs)
    if result.returncode != 0:
        raise RuntimeError(f"{label} failed:\n{result.stderr[-4000:]}")
    return result


def ffmpeg_path(path: Path) -> str:
    return str(path.resolve()).replace("\\", "/")


def ass_path(path: Path) -> str:
    return ffmpeg_path(path).replace(":", "\\:")


def drawtext_path(path: Path) -> str:
    return ffmpeg_path(path).replace(":", "\\:")


def escape_drawtext(text: str) -> str:
    return str(text or "").replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"),
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


def media_duration(path: Path) -> float:
    result = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nk=1:nw=1", str(path)], f"duration {path.name}")
    return float((result.stdout or "0").strip() or 0.0)


def validate_inputs() -> None:
    missing = [str(path) for path in [VSCODE_CAPTURE, BROWSER_CAPTURE] if not path.exists()]
    if missing:
        raise RuntimeError("Missing mandatory real captures: " + ", ".join(missing))
    if media_duration(VSCODE_CAPTURE) < 34:
        raise RuntimeError("VS Code capture is too short for required evidence.")
    if media_duration(BROWSER_CAPTURE) < 29:
        raise RuntimeError("Browser capture is too short for required evidence.")


def make_cta_clip() -> Path:
    image_path = WORK_DIR / "cta.jpg"
    img = Image.new("RGB", (WIDTH, HEIGHT), (8, 13, 24))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((260, 180, 1660, 900), radius=36, fill=(14, 24, 39), outline=(82, 196, 255), width=8)
    center_text(draw, (300, 245, 1620, 360), "NEXT:", font(72, True), (82, 196, 255))
    center_text(draw, (300, 380, 1620, 500), "BIGGER AI TOOLS", font(82, True), (255, 255, 255))
    center_text(draw, (300, 555, 1620, 665), "COMMENT EXTENSION", font(82, True), (255, 255, 255))
    center_text(draw, (300, 700, 1620, 810), "FOR FULL BUILD", font(70, True), (82, 196, 255))
    img.save(image_path, "JPEG", quality=94)
    out = RAW_DIR / f"{RUN_ID}_cta.mp4"
    run(
        [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-i",
            str(image_path),
            "-t",
            f"{CTA_DURATION:.2f}",
            "-vf",
            f"fps={FPS},format=yuv420p,scale={WIDTH}:{HEIGHT}",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            str(out),
        ],
        "render cta",
    )
    return out


def make_segment_clip(segment: dict, idx: int) -> Path:
    out = RAW_DIR / f"{RUN_ID}_seg_{idx:02d}_{segment['name']}.mp4"
    vf = f"fps={FPS},scale={WIDTH}:{HEIGHT}:flags=lanczos,format=yuv420p"
    overlay = str(segment.get("overlay") or "").strip()
    if overlay:
        font_file = drawtext_path(Path("C:/Windows/Fonts/arialbd.ttf"))
        lines = [line.strip() for line in overlay.splitlines() if line.strip()]
        box_h = 170 if len(lines) <= 1 else 250
        box_y = 56
        vf += (
            f",drawbox=x=52:y={box_y}:w=1020:h={box_h}:"
            "color=black@0.70:t=fill"
        )
        for line_idx, line in enumerate(lines[:3]):
            y = box_y + 30 + line_idx * 68
            size = 56 if len(lines) <= 2 else 50
            vf += (
                f",drawtext=fontfile='{font_file}':"
                f"text='{escape_drawtext(line)}':"
                f"x=92:y={y}:fontsize={size}:"
                "fontcolor=white:borderw=3:bordercolor=black"
            )
    run(
        [
            "ffmpeg",
            "-y",
            "-ss",
            f"{segment['start']:.3f}",
            "-i",
            str(segment["source"]),
            "-t",
            f"{segment['duration']:.3f}",
            "-vf",
            vf,
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            str(out),
        ],
        f"segment {idx}",
    )
    return out


def concat_video(paths: list[Path]) -> None:
    concat_path = TEMP_DIR / f"{RUN_ID}_concat.txt"
    concat_path.write_text("\n".join(f"file '{ffmpeg_path(path)}'" for path in paths), encoding="utf-8")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_path), "-c", "copy", str(SILENT_PATH)], "concat video")


def atempo_filter(factor: float) -> str:
    factor = max(0.5, min(8.0, float(factor or 1.0)))
    parts: list[str] = []
    while factor > 2.0:
        parts.append("atempo=2.0")
        factor /= 2.0
    parts.append(f"atempo={factor:.6f}")
    return ",".join(parts)


def make_audio() -> tuple[str, list[dict]]:
    texts = [segment["caption"] for segment in SEGMENTS] + ["Next I will build bigger tools with AI. Comment EXTENSION for the full build."]
    durations = [segment["duration"] for segment in SEGMENTS] + [CTA_DURATION]
    engine = pyttsx3.init()
    engine.setProperty("rate", 184)
    engine.setProperty("volume", 1.0)
    for voice in engine.getProperty("voices") or []:
        name = (getattr(voice, "name", "") or "").lower()
        if "david" in name or "mark" in name or "zira" in name:
            engine.setProperty("voice", voice.id)
            break
    raw_paths = []
    for idx, text in enumerate(texts, start=1):
        path = TEMP_DIR / f"{RUN_ID}_tts_raw_{idx:02d}.wav"
        if path.exists():
            path.unlink()
        engine.save_to_file(text, str(path))
        raw_paths.append(path)
    engine.runAndWait()

    cursor = 0.0
    segments: list[dict] = []
    padded_paths: list[Path] = []
    for idx, (raw_path, duration, text) in enumerate(zip(raw_paths, durations, texts), start=1):
        raw_duration = media_duration(raw_path)
        max_speech = max(0.8, duration - 0.35)
        working = raw_path
        speed = 1.0
        if raw_duration > max_speech:
            speed = raw_duration / max_speech
            working = TEMP_DIR / f"{RUN_ID}_tts_fit_{idx:02d}.wav"
            run(["ffmpeg", "-y", "-i", str(raw_path), "-af", atempo_filter(speed), "-ar", "22050", "-ac", "1", str(working)], f"fit audio {idx}")
        speech = media_duration(working)
        lead = 0.15
        tail = max(0.0, duration - lead - speech)
        padded = TEMP_DIR / f"{RUN_ID}_audio_{idx:02d}.wav"
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
                str(working),
                "-f",
                "lavfi",
                "-t",
                f"{tail:.3f}",
                "-i",
                "anullsrc=r=22050:cl=mono",
                "-filter_complex",
                f"[0:a][1:a][2:a]concat=n=3:v=0:a=1,atrim=0:{duration:.3f},asetpts=N/SR/TB[a]",
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
        segments.append({"start": round(cursor + lead, 3), "end": round(cursor + lead + speech, 3), "text": text})
        cursor += duration
    concat_path = TEMP_DIR / f"{RUN_ID}_audio_concat.txt"
    concat_path.write_text("\n".join(f"file '{ffmpeg_path(path)}'" for path in padded_paths), encoding="utf-8")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_path), "-ar", "22050", "-ac", "1", str(AUDIO_PATH)], "concat audio")
    return "pyttsx3_offline_rate184_segment_aligned", segments


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
Style: Cap,Arial,46,&H00FFFFFF,&H000000FF,&H00000000,&H9A000000,-1,0,0,0,100,100,0,0,1,6,2,2,54,54,34,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    for segment in segments:
        safe = split_lines(segment["text"]).replace("{", "").replace("}", "")
        events.append(f"Dialogue: 0,{ts(segment['start'])},{ts(segment['end'])},Cap,,0,0,0,,{{\\an2\\pos(960,1005)}}{safe}")
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
            "-r",
            str(FPS),
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-b:v",
            "4500k",
            "-maxrate",
            "4500k",
            "-bufsize",
            "9000k",
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
    total = media_duration(FINAL_PATH)
    sample_times = [2, 12, 22, 35, 49, total - 7, total - 2]
    for idx, t in enumerate([max(0.5, min(total - 0.5, item)) for item in sample_times], start=1):
        frame = REVIEW_DIR / f"review_frame_{idx:02d}.jpg"
        run(["ffmpeg", "-y", "-ss", f"{t:.2f}", "-i", str(FINAL_PATH), "-frames:v", "1", "-update", "1", str(frame)], f"review frame {idx}")
        frames.append(frame)
    thumbs = []
    for frame in frames:
        with Image.open(frame) as item:
            thumbs.append(item.convert("RGB").resize((320, 180), Image.Resampling.LANCZOS))
    contact = REVIEW_DIR / "contact_sheet.jpg"
    sheet = Image.new("RGB", (320 * len(thumbs), 180), (255, 255, 255))
    for idx, thumb in enumerate(thumbs):
        sheet.paste(thumb, (idx * 320, 0))
    sheet.save(contact, "JPEG", quality=92)
    return contact, frames


def probe_json(path: Path) -> dict:
    return json.loads(
        run(
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
            "probe",
        ).stdout
    )


def main() -> None:
    for directory in [ASSETS_DIR, RAW_DIR, TEMP_DIR, WORK_DIR, REVIEW_DIR]:
        directory.mkdir(parents=True, exist_ok=True)
    validate_inputs()
    clips = [make_segment_clip(segment, idx) for idx, segment in enumerate(SEGMENTS, start=1)]
    clips.append(make_cta_clip())
    concat_video(clips)
    audio_provider, caption_segments = make_audio()
    caption_count = write_captions(caption_segments)
    mux_final()
    contact, frames = make_review_artifacts()
    probe = probe_json(FINAL_PATH)
    requirements = {
        "VS Code editing": "present in vscode_real_capture.mp4 segment 2",
        "prompt typed into Codex": "present in vscode_real_capture.mp4 segment 3",
        "code generation": "present in vscode_real_capture.mp4 segment 4 with generated extension files visible",
        "terminal command run": "present in vscode_real_capture.mp4 segment 5",
        "load unpacked extension in browser": "present in browser_real_capture.mp4 segment 6 on chrome://extensions",
        "extension working on webpage": "present in browser_real_capture.mp4 segments 1 and 7",
    }
    PROOF_PATH.write_text(json.dumps(requirements, indent=2), encoding="utf-8")
    LOG_PATH.write_text(
        "\n".join(
            [
                f"final={FINAL_PATH}",
                f"duration={probe.get('format', {}).get('duration')}",
                f"size={probe.get('format', {}).get('size')}",
                "dimensions=1920x1080",
                "fps=30",
                f"audio_provider={audio_provider}",
                f"contact_sheet={contact}",
                "review_frames=" + " | ".join(str(frame) for frame in frames),
                f"caption_count={caption_count}",
                "privacy_confirmation=local demo extension/article only; no private data used",
                "paid_credits=none; no ElevenLabs, no RunwayML, no paid APIs",
                "requirements=" + json.dumps(requirements),
                json.dumps(probe, indent=2),
            ]
        ),
        encoding="utf-8",
    )
    print(LOG_PATH)
    print(json.dumps({"probe": probe, "requirements": requirements}, indent=2))


if __name__ == "__main__":
    main()
