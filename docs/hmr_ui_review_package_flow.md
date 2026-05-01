# HMR UI Review Package Flow

Date: 2026-05-01

## Purpose

UI-generated HMR videos need a predictable path into the same production review
workflow as runner-generated videos: render report, QA report, review package,
manifest, and platform-safe export commands.

This flow is coding-first and testable without running a full render.

## Backend Integration

The UI entry point remains:

```text
POST /api/generate/video/free
```

When `scene_mode="hybrid_motion"` and `ENABLE_HYBRID_MOTION_RENDERER=1`, the
route can attach `hmr_productization` metadata to the response.

The metadata is built by:

```python
utils.hmr_ui_productization.build_hmr_ui_productization_metadata(...)
```

After a real HMR render, the route calls:

```python
utils.hmr_ui_productization.materialize_hmr_ui_review_workflow(...)
```

That materialization step writes or creates:

- `render_report.json`
- `qa_report.json`
- `story_candidate.json`
- `review_package/`
- `review_package/manifest.json`
- planned platform export paths and FFmpeg commands

## Path Convention

For a UI run id:

```text
backend/generated_videos/hmr_ui_runs/<run_id>/
```

Expected files:

```text
backend/generated_videos/hmr_ui_runs/<run_id>/render_report.json
backend/generated_videos/hmr_ui_runs/<run_id>/qa_report.json
backend/generated_videos/hmr_ui_runs/<run_id>/story_candidate.json
backend/generated_videos/hmr_ui_runs/<run_id>/review_package/
backend/generated_videos/hmr_ui_runs/<run_id>/review_package/manifest.json
backend/generated_videos/hmr_ui_runs/<run_id>/review_package/platform_exports/
```

The original MP4 path remains the UI-rendered video path. Review-package tools
copy that MP4 into the review package.

## Platform Export Plan

The UI metadata includes planned exports for:

- `instagram_reels`
- `tiktok`
- `youtube_shorts`

Each planned export includes:

- output MP4 path
- FFmpeg command
- `generated=false`

Exports are not transcoded during smoke tests. They can be run later through
`backend/utils/hmr_platform_exports.py`.

## Safety

The flow checks `assert_not_frozen_output(...)` before assigning run, review, or
export paths. This keeps frozen post-ready packages protected.

HMR UI mode forces free TTS behavior in the route. The productization metadata
does not select ElevenLabs, RunwayML, Anthropic, or OpenAI paid APIs.

## Known Limits

- The route still performs direct HMR rendering when HMR is enabled and selected;
  #23 tracks moving this to a non-blocking worker/job path.
- Platform exports are planned, not automatically transcoded.
- Review package creation still depends on an already completed render output.
