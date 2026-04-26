from __future__ import annotations

import json
import math
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pyttsx3

from .formatting import format_spec
from .render_modes import assert_provider_allowed
from .schema import Storyboard


@dataclass
class CaptionEvent:
    start: float
    end: float
    text: str
    is_money: bool = False
    y: int = 1505


def run(cmd: list[str], label: str) -> subprocess.CompletedProcess:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"{label} failed:\n{result.stderr[-3000:]}")
    return result


def ffmpeg_path(path: Path) -> str:
    return str(path.resolve()).replace("\\", "/")


def ass_path(path: Path) -> str:
    return ffmpeg_path(path).replace(":", "\\:")


def probe_duration(path: Path) -> float:
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)], "probe duration").stdout.strip())


def make_silence(duration: float, out: Path) -> None:
    run(
        [
            "ffmpeg", "-y", "-f", "lavfi", "-i",
            "anullsrc=channel_layout=stereo:sample_rate=48000",
            "-t", f"{max(0.01, duration):.3f}", "-c:a", "pcm_s16le", str(out),
        ],
        "make silence",
    )


def regenerate_audio_only(storyboard: Storyboard, work_dir: Path, rate: int = 224) -> tuple[Path, list[dict], str]:
    assert_provider_allowed(storyboard, "local_tts", "draft narration")
    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    engine = pyttsx3.init()
    engine.setProperty("rate", rate)
    engine.setProperty("volume", 1.0)
    for voice in engine.getProperty("voices") or []:
        name = (getattr(voice, "name", "") or "").lower()
        if "zira" in name or "david" in name or "mark" in name:
            engine.setProperty("voice", voice.id)
            break

    raw_parts: list[Path] = []
    for idx, scene in enumerate(storyboard.scenes, start=1):
        raw = work_dir / f"voice_scene_{idx:02d}.wav"
        engine.save_to_file(scene.narration_text, str(raw))
        raw_parts.append(raw)
    engine.runAndWait()

    concat_parts: list[Path] = []
    timings: list[dict] = []
    cursor = 0.0
    for idx, (scene, raw) in enumerate(zip(storyboard.scenes, raw_parts), start=1):
        scene_start = sum(s.duration for s in storyboard.scenes[: idx - 1]) + 0.28
        if scene_start > cursor:
            silence = work_dir / f"silence_{idx:02d}.wav"
            make_silence(scene_start - cursor, silence)
            concat_parts.append(silence)
            cursor = scene_start

        clean = work_dir / f"voice_scene_{idx:02d}_clean.wav"
        run(
            [
                "ffmpeg", "-y", "-i", str(raw),
                "-af", "atempo=0.96,aresample=48000,aformat=sample_fmts=s16:channel_layouts=stereo",
                "-ar", "48000", "-ac", "2", str(clean),
            ],
            "normalize local voice",
        )
        duration = probe_duration(clean)
        concat_parts.append(clean)
        timings.append({"scene_id": scene.scene_id, "start": cursor, "end": cursor + duration, "text": scene.caption_text or scene.narration_text})
        cursor += duration

    total_duration = sum(scene.duration for scene in storyboard.scenes)
    if cursor < total_duration:
        tail = work_dir / "silence_tail.wav"
        make_silence(total_duration - cursor, tail)
        concat_parts.append(tail)

    concat = work_dir / "audio_concat.txt"
    concat.write_text("\n".join(f"file '{ffmpeg_path(path)}'" for path in concat_parts), encoding="utf-8")
    audio_path = work_dir / f"{storyboard.project_id}_draft_audio.wav"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat), "-c", "pcm_s16le", str(audio_path)], "concat audio")
    (work_dir / "caption_timings.json").write_text(json.dumps(timings, indent=2), encoding="utf-8")
    return audio_path, timings, f"pyttsx3_offline_rate{rate}"


def _chunks(text: str, max_words: int = 5) -> list[tuple[str, bool]]:
    money = {"$42", "$53", "$12.95", "$480", "$52.99/month", "$480/YEAR"}
    chunks: list[tuple[str, bool]] = []
    current: list[str] = []
    for word in text.split():
        clean = word.strip(".,!?")
        if clean in money:
            if current:
                chunks.append((" ".join(current), False))
                current = []
            chunks.append((clean, True))
        else:
            current.append(word)
            if len(current) >= max_words:
                chunks.append((" ".join(current), False))
                current = []
    if current:
        chunks.append((" ".join(current), False))
    return chunks


def regenerate_captions_only(storyboard: Storyboard, timings: list[dict], ass_file: Path) -> tuple[Path, list[CaptionEvent]]:
    spec = format_spec(storyboard.format)
    width, height = spec["width"], spec["height"]

    def ts(seconds: float) -> str:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = seconds % 60
        return f"{h}:{m:02d}:{s:05.2f}"

    events: list[CaptionEvent] = []
    scene_by_id = {scene.scene_id: scene for scene in storyboard.scenes}
    for timing in timings:
        scene = scene_by_id[timing["scene_id"]]
        chunks = _chunks(timing["text"])
        phrase_start = float(timing["start"])
        phrase_end = float(timing["end"])
        duration = max(0.55, phrase_end - phrase_start)
        step = max(0.55, duration / max(1, len(chunks)))
        safe_y = scene.caption_safe_zone.y
        if scene.scene_type == "payoff":
            safe_y = min(height - 240, safe_y + 70)
        for idx, (chunk, is_money) in enumerate(chunks):
            start = phrase_start + idx * step
            end = min(phrase_end + 0.08, start + step)
            if end - start < 0.55:
                end = start + 0.55
            if start <= phrase_end + 0.2:
                events.append(CaptionEvent(start, end, chunk, is_money, safe_y - 85 if is_money else safe_y))

    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Arial,52,&H00FFFFFF,&H000000FF,&H00000000,&HA0000000,-1,0,0,0,100,100,0,0,1,7,2,2,54,54,40,1
Style: Money,Arial,84,&H0034D399,&H000000FF,&H00000000,&HA0000000,-1,0,0,0,100,100,0,0,1,8,2,2,54,54,40,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    rows = []
    for event in events:
        style = "Money" if event.is_money else "Cap"
        rows.append(f"Dialogue: 0,{ts(event.start)},{ts(event.end)},{style},,0,0,0,,{{\\an2\\pos({width//2},{event.y})}}{event.text}")
    ass_file.parent.mkdir(parents=True, exist_ok=True)
    ass_file.write_text(header + "\n".join(rows) + "\n", encoding="utf-8")
    return ass_file, events


def restitch_with_locked_visuals(storyboard: Storyboard, silent_video: Path, audio_path: Path, ass_file: Path, output_path: Path) -> Path:
    spec = format_spec(storyboard.format)
    total_duration = sum(scene.duration for scene in storyboard.scenes)
    run(
        [
            "ffmpeg", "-y", "-i", str(silent_video), "-i", str(audio_path),
            "-filter_complex", f"[0:v]ass='{ass_path(ass_file)}'[v];[1:a]apad,atrim=0:{total_duration:.2f}[a]",
            "-map", "[v]", "-map", "[a]", "-t", f"{total_duration:.2f}", "-r", str(spec["fps"]),
            "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(output_path),
        ],
        "restitch locked visuals",
    )
    return output_path


def estimate_wpm(storyboard: Storyboard, timings: list[dict]) -> float:
    words = sum(len((scene.narration_text or "").split()) for scene in storyboard.scenes)
    active = sum(max(0.01, float(item["end"]) - float(item["start"])) for item in timings)
    return words / active * 60.0
