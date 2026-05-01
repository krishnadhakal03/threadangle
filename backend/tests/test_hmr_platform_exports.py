import json

import pytest

from utils.hmr_artifact_manifest import build_manifest, write_manifest
from utils.hmr_platform_exports import (
    PRESETS,
    build_ffmpeg_command,
    default_output_path,
    export_platform_safe_video,
    validate_presets,
)


def test_platform_export_output_naming(tmp_path):
    source = tmp_path / "day9_bill_leak_full.mp4"
    assert default_output_path(source, "instagram_reels") == tmp_path / "day9_bill_leak_full_IG_SAFE.mp4"
    assert default_output_path(source, "tiktok") == tmp_path / "day9_bill_leak_full_TT_SAFE.mp4"
    assert default_output_path(source, "youtube_shorts") == tmp_path / "day9_bill_leak_full_YT_SHORTS_SAFE.mp4"


def test_ffmpeg_command_uses_platform_safe_settings(tmp_path):
    source = tmp_path / "input.mp4"
    target = tmp_path / "input_IG_SAFE.mp4"
    cmd = build_ffmpeg_command(source, target, "instagram_reels")

    assert cmd[:3] == ["ffmpeg", "-y", "-i"]
    assert "-c:v" in cmd
    assert cmd[cmd.index("-c:v") + 1] == "libx264"
    assert "-c:a" in cmd
    assert cmd[cmd.index("-c:a") + 1] == "aac"
    assert "-pix_fmt" in cmd
    assert cmd[cmd.index("-pix_fmt") + 1] == "yuv420p"
    assert "-r" in cmd
    assert cmd[cmd.index("-r") + 1] == "30"
    assert "-vsync" in cmd
    assert cmd[cmd.index("-vsync") + 1] == "cfr"
    assert "-movflags" in cmd
    assert cmd[cmd.index("-movflags") + 1] == "+faststart"
    assert "scale=1080:1920" in cmd[cmd.index("-vf") + 1]
    assert "pad=1080:1920" in cmd[cmd.index("-vf") + 1]


def test_strict_fallback_uses_baseline_and_aac_128k(tmp_path):
    cmd = build_ffmpeg_command(tmp_path / "input.mp4", tmp_path / "safe.mp4", "strict_fallback")

    assert "-profile:v" in cmd
    assert cmd[cmd.index("-profile:v") + 1] == "baseline"
    assert "-b:a" in cmd
    assert cmd[cmd.index("-b:a") + 1] == "128k"


def test_missing_input_handling(tmp_path):
    with pytest.raises(FileNotFoundError):
        export_platform_safe_video(tmp_path / "missing.mp4", preset="instagram_reels", run=False)


def test_preset_config_validation():
    validate_presets()
    assert {"instagram_reels", "tiktok", "youtube_shorts", "strict_fallback"} == set(PRESETS)


def test_frozen_package_blocks_default_export_without_force(tmp_path):
    source = tmp_path / "review_package" / "final.mp4"
    source.parent.mkdir()
    source.write_bytes(b"not a real mp4")
    manifest = build_manifest(
        topic="Frozen",
        hook="Frozen hook",
        video_path=source,
        review_package_path=source.parent,
        frozen=True,
    )
    write_manifest(source.parent, manifest)

    with pytest.raises(RuntimeError, match="Refusing to write under frozen"):
        export_platform_safe_video(source, preset="instagram_reels", run=False)


def test_frozen_package_allows_explicit_separate_output_dir(tmp_path):
    source = tmp_path / "review_package" / "final.mp4"
    source.parent.mkdir()
    source.write_bytes(b"not a real mp4")
    manifest = build_manifest(
        topic="Frozen",
        hook="Frozen hook",
        video_path=source,
        review_package_path=source.parent,
        frozen=True,
    )
    write_manifest(source.parent, manifest)

    result = export_platform_safe_video(
        source,
        preset="youtube_shorts",
        output_dir=tmp_path / "platform_exports",
        run=False,
    )

    assert result["output"].endswith("final_YT_SHORTS_SAFE.mp4")


def test_manifest_update_when_export_runs(monkeypatch, tmp_path):
    source = tmp_path / "review_package" / "final.mp4"
    source.parent.mkdir()
    source.write_bytes(b"not a real mp4")
    manifest = build_manifest(
        topic="Draft",
        hook="Draft hook",
        video_path=source,
        review_package_path=source.parent,
        frozen=False,
    )
    write_manifest(source.parent, manifest)

    def fake_run(cmd, check, timeout):
        target = cmd[-1]
        with open(target, "wb") as handle:
            handle.write(b"safe mp4")

    monkeypatch.setattr("utils.hmr_platform_exports.subprocess.run", fake_run)
    result = export_platform_safe_video(source, preset="tiktok")

    updated = json.loads((source.parent / "manifest.json").read_text(encoding="utf-8"))
    assert updated["platform_exports"]["tiktok"] == result["output"]
