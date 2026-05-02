from __future__ import annotations

import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def test_sfx_lookup_uses_assets_sfx_role_convention(tmp_path):
    from utils.hmr_sfx import resolve_sfx_asset, sfx_asset_candidates

    root = tmp_path / "assets" / "sfx"
    whoosh = root / "whoosh" / "whoosh.wav"
    whoosh.parent.mkdir(parents=True)
    whoosh.write_bytes(b"fake wav")

    candidates = sfx_asset_candidates("whoosh", root)
    resolved = resolve_sfx_asset("whoosh", root)

    assert whoosh in candidates
    assert resolved["status"] == "resolved"
    assert resolved["path"] == str(whoosh.resolve())
    assert resolve_sfx_asset("payoff_chime", root)["status"] == "missing"


def test_sfx_plan_reports_missing_assets_without_blocking_generation(tmp_path):
    from utils.hmr_sfx import build_sfx_plan

    scenes = [
        {
            "id": "hook",
            "template": "hook_footage_overlay",
            "duration": 2.5,
            "caption_text": "Stop paying this hidden bill leak.",
        },
        {
            "id": "payoff",
            "template": "payoff_number_reveal",
            "duration": 3.0,
            "caption_text": "Save $43 this month.",
        },
    ]

    plan = build_sfx_plan(scenes, asset_root=tmp_path / "assets" / "sfx")

    assert plan["render_required"] is False
    assert plan["volume_policy"]["voice_and_captions_primary"] is True
    assert {"whoosh", "soft_hit", "warning_beep", "riser", "payoff_chime"}.issubset(set(plan["missing_roles"]))
    assert plan["cues"][0]["scene_id"] == "hook"
    assert plan["cues"][0]["timeline_time"] >= 0
    assert plan["resolved_cues"] == []


def test_sfx_plan_uses_explicit_scene_metadata_and_resolves_files(tmp_path):
    from utils.hmr_sfx import build_sfx_plan

    root = tmp_path / "assets" / "sfx"
    tick = root / "tick" / "tick.wav"
    tick.parent.mkdir(parents=True)
    tick.write_bytes(b"fake wav")
    scenes = [
        {
            "id": "compare",
            "duration": 4.0,
            "sfx_cues": [{"role": "tick", "local_time": 1.25, "volume": 0.11}],
        }
    ]

    plan = build_sfx_plan(scenes, asset_root=root)
    cue = plan["cues"][0]

    assert cue["status"] == "resolved"
    assert cue["path"] == str(tick.resolve())
    assert cue["timeline_time"] == 1.25
    assert cue["volume"] == 0.11
    assert plan["missing_roles"] == []


def test_sfx_mix_command_keeps_voice_primary_and_delays_cues(tmp_path):
    from utils.hmr_sfx import build_sfx_mix_command

    base = tmp_path / "voice.wav"
    out = tmp_path / "mixed.m4a"
    cue_path = tmp_path / "tick.wav"
    cues = [
        {
            "role": "tick",
            "status": "resolved",
            "path": str(cue_path),
            "timeline_time": 1.2,
            "volume": 0.12,
        }
    ]

    cmd = build_sfx_mix_command(base, out, cues)

    assert cmd[:5] == ["ffmpeg", "-y", "-i", str(base), "-i"]
    assert str(cue_path) in cmd
    filter_complex = cmd[cmd.index("-filter_complex") + 1]
    assert "[0:a]volume=1.0[voice]" in filter_complex
    assert "volume=0.120" in filter_complex
    assert "adelay=1200|1200" in filter_complex
    assert "amix=inputs=2:duration=first" in filter_complex
    assert cmd[-1] == str(out)
