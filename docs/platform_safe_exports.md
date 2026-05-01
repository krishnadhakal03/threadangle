# Platform-Safe HMR Exports

Date: 2026-05-01

## Purpose

Use platform-safe exports when an HMR video is visually approved but needs a
browser/upload-friendly MP4 for Instagram Reels, TikTok, or YouTube Shorts.
This is a transcode step from an existing MP4, not a rerender.

## CLI

```bash
python backend/utils/hmr_platform_exports.py --input backend/generated_videos/storyboard_review/day9_bill_leak/review_package/day9_bill_leak_full.mp4 --preset instagram_reels
```

Available presets:

- `instagram_reels`
- `tiktok`
- `youtube_shorts`
- `strict_fallback`

Use `--output-dir` to write exports outside a frozen package:

```bash
python backend/utils/hmr_platform_exports.py --input path/to/final.mp4 --preset youtube_shorts --output-dir backend/generated_videos/storyboard_review/day9_bill_leak/platform_exports
```

Use `--dry-run` to print the FFmpeg command without writing an export.

## FFmpeg Settings

The standard platform presets use:

- video codec: `libx264`
- audio codec: `aac`
- pixel format: `yuv420p`
- frame rate: constant `30fps`
- output size: `1080x1920`
- scaling: preserve aspect ratio, pad to vertical 9:16
- metadata: `-movflags +faststart`
- CRF: `18`
- encoder preset: `medium`
- audio bitrate: `160k`

The `strict_fallback` preset additionally uses:

- H.264 profile: `baseline`
- audio bitrate: `128k`
- CRF: `20`

## Output Names

Default outputs are written next to the input unless `--output` or
`--output-dir` is provided:

- `*_IG_SAFE.mp4` for `instagram_reels`
- `*_TT_SAFE.mp4` for `tiktok`
- `*_YT_SHORTS_SAFE.mp4` for `youtube_shorts`
- `*_STRICT_SAFE.mp4` for `strict_fallback`

## Frozen Packages

The exporter calls `assert_not_frozen_output(...)` before writing. If the input
video lives in a package with `manifest.json` and `"frozen": true`, the default
next-to-input export is blocked. Write to a separate `--output-dir` for normal
production use.

`--force` is reserved for explicit maintenance tasks that intentionally update a
named frozen package.

## Manifest Integration

When an export is written into a non-frozen package that already has
`manifest.json`, the exporter adds or updates:

```json
{
  "platform_exports": {
    "instagram_reels": "path/to/video_IG_SAFE.mp4"
  }
}
```

Missing manifests do not block exports outside frozen paths.
