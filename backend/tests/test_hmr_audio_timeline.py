from __future__ import annotations

import sys
import shutil
import subprocess
from pathlib import Path

import pytest


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def test_audio_timeline_binds_voice_sfx_music_and_payoff_events():
    from utils.hmr_audio_timeline import build_audio_binding_timeline
    from utils.hmr_editing_rhythm import build_quick_cut_schedule

    scene_timings = [
        {"scene_id": "hook", "start": 0.0, "end": 2.2},
        {"scene_id": "payoff", "start": 2.2, "end": 4.8},
    ]
    caption_events = [
        {"start": 0.0, "end": 1.1, "text": "I found $43"},
        {"start": 1.1, "end": 2.2, "text": "hiding in one bill"},
        {"start": 2.2, "end": 3.4, "text": "Save it today"},
        {"start": 3.4, "end": 4.8, "text": "before you pay"},
    ]
    rhythm = build_quick_cut_schedule(
        script_text="I found $43 hiding in one bill. Save it today before you pay.",
        scene_timings=scene_timings,
        caption_events=caption_events,
    )
    timeline = build_audio_binding_timeline(
        script_text="I found $43 hiding in one bill. Save it today before you pay.",
        scene_timings=scene_timings,
        caption_events=caption_events,
        sfx_plan={
            "cues": [
                {
                    "scene_id": "hook",
                    "role": "warning_beep",
                    "timeline_time": 1.4,
                    "volume": 0.4,
                    "status": "missing",
                    "reason": "warning_language",
                }
            ]
        },
        editing_rhythm_plan=rhythm,
        music_bed_path="assets/music/local-bed.wav",
    )

    assert timeline["timing_source"] == "voiceover_primary"
    assert timeline["timing_confidence"] == "caption_phrase_timing"
    assert timeline["event_types"] == ["voice_segment", "sfx_cue", "music_bed", "transition_hit", "payoff_hit"]
    assert timeline["mix_rules"]["voice_priority"] is True
    assert timeline["mix_rules"]["music_ducking_under_voice_db"] == -12
    assert timeline["debug"]["paid_providers_used"] == {
        "elevenlabs": False,
        "paid_music": False,
        "paid_sfx": False,
    }
    assert any(event["event_type"] == "music_bed" for event in timeline["events"])
    assert any(event["event_type"] == "payoff_hit" for event in timeline["events"])
    sfx = next(event for event in timeline["events"] if event["event_type"] == "sfx_cue")
    assert sfx["binding"] == "caption_phrase_timing"
    assert sfx["volume"] == 0.28
    assert sfx["bound_voice_text"] == "hiding in one bill"


def test_audio_timeline_falls_back_without_caption_timing():
    from utils.hmr_audio_timeline import build_audio_binding_timeline

    timeline = build_audio_binding_timeline(
        script_text="Stop scrolling. Check this number. Save $27 today.",
        scene_timings=[{"scene_id": "hook", "start": 0.0, "end": 3.0}],
        caption_events=[],
        sfx_plan={"cues": [{"scene_id": "hook", "role": "whoosh", "timeline_time": 0.2, "status": "missing"}]},
    )

    assert timeline["timing_confidence"] == "fallback_estimated"
    assert timeline["debug"]["voice_segment_count"] == 3
    assert any(event["event_type"] == "sfx_cue" for event in timeline["events"])


def test_audio_mix_plan_is_command_only_and_ducks_music(tmp_path):
    from utils.hmr_audio_timeline import build_audio_binding_timeline, build_audio_mix_plan

    voice = tmp_path / "voice.wav"
    music = tmp_path / "music.wav"
    tick = tmp_path / "tick.wav"
    output = tmp_path / "mixed.m4a"
    timeline = build_audio_binding_timeline(
        script_text="Save $27 today.",
        scene_timings=[{"scene_id": "hook", "start": 0.0, "end": 2.0}],
        caption_events=[{"start": 0.0, "end": 2.0, "text": "Save $27 today"}],
        sfx_plan={
            "cues": [
                {
                    "scene_id": "hook",
                    "role": "tick",
                    "timeline_time": 0.8,
                    "volume": 0.12,
                    "status": "resolved",
                    "path": str(tick),
                }
            ]
        },
        music_bed_path=music,
    )

    plan = build_audio_mix_plan(voice_audio_path=voice, output_audio_path=output, audio_timeline=timeline)

    assert plan["render_required"] is False
    assert plan["input_event_count"] == 2
    cmd = plan["command"]
    assert cmd[:5] == ["ffmpeg", "-y", "-i", str(voice), "-i"]
    assert str(music) in cmd
    assert str(tick) in cmd
    filter_complex = cmd[cmd.index("-filter_complex") + 1]
    assert "[0:a]volume=1.000[voice]" in filter_complex
    assert "sidechaincompress" in filter_complex
    assert "adelay=800|800" in filter_complex
    assert "alimiter=limit=0.95" in filter_complex


def _make_tiny_wav(path: Path, *, frequency: int = 440, duration: float = 0.35) -> None:
    if not shutil.which("ffmpeg"):
        pytest.skip("ffmpeg is required for synthetic audio fixture")
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency={frequency}:duration={duration}:sample_rate=44100",
            str(path),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=30,
    )


def test_execute_audio_mix_plan_mixes_local_assets(tmp_path):
    from utils.hmr_audio_timeline import build_audio_binding_timeline, execute_audio_mix_plan

    voice = tmp_path / "voice.wav"
    tick = tmp_path / "tick.wav"
    output = tmp_path / "mixed.m4a"
    _make_tiny_wav(voice, frequency=220, duration=0.8)
    _make_tiny_wav(tick, frequency=880, duration=0.2)
    timeline = build_audio_binding_timeline(
        script_text="Save $27 today.",
        scene_timings=[{"scene_id": "hook", "start": 0.0, "end": 0.8}],
        caption_events=[{"start": 0.0, "end": 0.8, "text": "Save $27 today"}],
        sfx_plan={
            "cues": [
                {
                    "scene_id": "hook",
                    "role": "tick",
                    "timeline_time": 0.2,
                    "volume": 0.12,
                    "status": "resolved",
                    "path": str(tick),
                }
            ]
        },
    )

    result = execute_audio_mix_plan(
        voice_audio_path=voice,
        output_audio_path=output,
        audio_timeline=timeline,
        enabled=True,
    )

    assert result["audio_mix_execution_status"] == "mixed"
    assert result["mixed"] is True
    assert result["mixed_event_count"] == 1
    assert result["skipped_event_count"] == 0
    assert result["local_assets_only"] is True
    assert output.exists()
    assert output.stat().st_size > 100


def test_execute_audio_mix_plan_skips_missing_and_nonlocal_assets(tmp_path):
    from utils.hmr_audio_timeline import build_audio_binding_timeline, execute_audio_mix_plan

    voice = tmp_path / "voice.wav"
    _make_tiny_wav(voice, duration=0.4)
    timeline = build_audio_binding_timeline(
        script_text="Save $27 today.",
        scene_timings=[{"scene_id": "hook", "start": 0.0, "end": 0.4}],
        caption_events=[{"start": 0.0, "end": 0.4, "text": "Save $27 today"}],
        sfx_plan={
            "cues": [
                {"scene_id": "hook", "role": "tick", "timeline_time": 0.1, "status": "missing", "path": None},
                {
                    "scene_id": "hook",
                    "role": "whoosh",
                    "timeline_time": 0.2,
                    "status": "resolved",
                    "path": "https://example.com/whoosh.wav",
                },
            ]
        },
    )

    result = execute_audio_mix_plan(
        voice_audio_path=voice,
        output_audio_path=tmp_path / "mixed.m4a",
        audio_timeline=timeline,
        enabled=True,
    )

    assert result["audio_mix_execution_status"] == "skipped_missing_assets"
    assert result["mixed"] is False
    assert result["mixed_event_count"] == 0
    assert result["skipped_event_count"] == 2
    assert result["skipped_missing_assets"][0]["path"] is None
    assert result["skipped_non_local_assets"][0]["path"] == "https://example.com/whoosh.wav"
