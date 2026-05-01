"""Create platform-safe MP4 exports from existing HMR videos."""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from .hmr_artifact_manifest import MANIFEST_FILENAME, assert_not_frozen_output
except ImportError:  # pragma: no cover - direct script execution fallback
    from hmr_artifact_manifest import MANIFEST_FILENAME, assert_not_frozen_output


@dataclass(frozen=True)
class PlatformExportPreset:
    name: str
    suffix: str
    video_codec: str = "libx264"
    audio_codec: str = "aac"
    pixel_format: str = "yuv420p"
    frame_rate: int = 30
    width: int = 1080
    height: int = 1920
    movflags: str = "+faststart"
    video_profile: str | None = None
    audio_bitrate: str = "160k"
    crf: int = 18
    preset: str = "medium"


PRESETS: dict[str, PlatformExportPreset] = {
    "instagram_reels": PlatformExportPreset(name="instagram_reels", suffix="_IG_SAFE"),
    "tiktok": PlatformExportPreset(name="tiktok", suffix="_TT_SAFE"),
    "youtube_shorts": PlatformExportPreset(name="youtube_shorts", suffix="_YT_SHORTS_SAFE"),
    "strict_fallback": PlatformExportPreset(
        name="strict_fallback",
        suffix="_STRICT_SAFE",
        video_profile="baseline",
        audio_bitrate="128k",
        crf=20,
    ),
}


def get_preset(name: str) -> PlatformExportPreset:
    try:
        return PRESETS[name]
    except KeyError as exc:
        raise ValueError(f"Unknown platform export preset: {name}") from exc


def default_output_path(input_path: str | Path, preset: str, output_dir: str | Path | None = None) -> Path:
    source = Path(input_path).expanduser().resolve()
    config = get_preset(preset)
    target_dir = Path(output_dir).expanduser().resolve() if output_dir else source.parent
    return target_dir / f"{source.stem}{config.suffix}.mp4"


def build_ffmpeg_command(input_path: str | Path, output_path: str | Path, preset: str) -> list[str]:
    config = get_preset(preset)
    vf = (
        f"scale={config.width}:{config.height}:force_original_aspect_ratio=decrease,"
        f"pad={config.width}:{config.height}:(ow-iw)/2:(oh-ih)/2,"
        "setsar=1"
    )
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(Path(input_path).expanduser().resolve()),
        "-vf",
        vf,
        "-r",
        str(config.frame_rate),
        "-vsync",
        "cfr",
        "-c:v",
        config.video_codec,
        "-pix_fmt",
        config.pixel_format,
        "-preset",
        config.preset,
        "-crf",
        str(config.crf),
    ]
    if config.video_profile:
        cmd.extend(["-profile:v", config.video_profile])
    cmd.extend(
        [
            "-c:a",
            config.audio_codec,
            "-b:a",
            config.audio_bitrate,
            "-movflags",
            config.movflags,
            str(Path(output_path).expanduser().resolve()),
        ]
    )
    return cmd


def validate_presets() -> None:
    for name, config in PRESETS.items():
        if config.name != name:
            raise ValueError(f"Preset key/name mismatch: {name} != {config.name}")
        if config.video_codec != "libx264":
            raise ValueError(f"{name} must use libx264")
        if config.audio_codec != "aac":
            raise ValueError(f"{name} must use AAC")
        if config.pixel_format != "yuv420p":
            raise ValueError(f"{name} must use yuv420p")
        if config.frame_rate != 30:
            raise ValueError(f"{name} must use constant 30fps")
        if (config.width, config.height) != (1080, 1920):
            raise ValueError(f"{name} must export 1080x1920")
        if config.movflags != "+faststart":
            raise ValueError(f"{name} must use +faststart")


def _update_manifest_with_export(output_path: Path, preset: str, *, force: bool) -> None:
    manifest_path = output_path.parent / MANIFEST_FILENAME
    if not manifest_path.exists():
        return
    assert_not_frozen_output(output_path.parent, force=force)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    exports = dict(manifest.get("platform_exports") or {})
    exports[preset] = str(output_path)
    manifest["platform_exports"] = exports
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def export_platform_safe_video(
    input_path: str | Path,
    *,
    preset: str,
    output_path: str | Path | None = None,
    output_dir: str | Path | None = None,
    force: bool = False,
    run: bool = True,
) -> dict[str, Any]:
    """Transcode an existing HMR MP4 to a platform-safe preset."""
    validate_presets()
    source = Path(input_path).expanduser().resolve()
    if not source.exists():
        raise FileNotFoundError(f"Input video not found: {source}")
    if output_path and output_dir:
        raise ValueError("Use either output_path or output_dir, not both")
    target = Path(output_path).expanduser().resolve() if output_path else default_output_path(source, preset, output_dir)
    if target.exists() and not force:
        raise FileExistsError(f"Output already exists: {target}")
    assert_not_frozen_output(target, force=force)
    target.parent.mkdir(parents=True, exist_ok=True)
    cmd = build_ffmpeg_command(source, target, preset)
    if run:
        subprocess.run(cmd, check=True, timeout=600)
        _update_manifest_with_export(target, preset, force=force)
    return {
        "preset": preset,
        "input": str(source),
        "output": str(target),
        "command": cmd,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create platform-safe MP4 exports from an existing HMR video.")
    parser.add_argument("--input", required=True, help="Existing MP4 to transcode.")
    parser.add_argument("--preset", required=True, choices=sorted(PRESETS), help="Export preset to use.")
    parser.add_argument("--output", default=None, help="Optional explicit output MP4 path.")
    parser.add_argument("--output-dir", default=None, help="Optional directory for the preset-named output.")
    parser.add_argument("--force", action="store_true", help="Allow replacing an existing output or writing under a frozen manifest.")
    parser.add_argument("--dry-run", action="store_true", help="Print the ffmpeg command without running it.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = export_platform_safe_video(
        args.input,
        preset=args.preset,
        output_path=args.output,
        output_dir=args.output_dir,
        force=args.force,
        run=not args.dry_run,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
