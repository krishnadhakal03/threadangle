# HMR UI Smoke-Test Plan

Date: 2026-05-01

## Purpose

Prepare the UI/backend path for later manual HMR generation testing without
running full renders during the coding roadmap.

This is a coding-only smoke harness. It validates request, path, and safety
configuration before manual UI testing.

## Audited Path

Frontend:

- `frontend/src/components/Dashboard.jsx`
- `frontend/src/utils/api.js`
- API call: `POST /api/generate/video/free`
- Progress polling: `GET /api/generate/video/progress/{generation_id}`

Backend:

- Route entry point: `backend/routes/generate.py::generate_free_video`
- Request schema: `GenerateVideoRequest`
- HMR selection: `scene_mode="hybrid_motion"` plus
  `ENABLE_HYBRID_MOTION_RENDERER=1`
- Output path: `backend/generated_videos/<run_id>.mp4`
- Render orchestration: `render_hybrid_video(...)`
- Review package: available from production runner tooling, not automatically
  created by the UI route today.
- Platform exports: `backend/utils/hmr_platform_exports.py` is available after
  render/package creation.

## Coding Harness

`backend/routes/generate.py` now exposes:

```python
build_hmr_ui_generation_smoke_plan(request, generated_root=None, run_id=None)
```

The helper does not render. It validates:

- HMR mode can be selected.
- Renderer feature flag state is visible.
- dry-run state is resolved.
- output path is unique/safe for a generated run id.
- frozen manifest guard is checked.
- HMR defaults to free TTS and no paid Runway/OpenAI/Anthropic providers.
- platform export integration is available as a post-render step.
- `hmr_async` is surfaced as requested intent only.
- async execution is marked `scaffold_only`, with `worker_active=false`.
- progress is marked non-durable and in-memory only.

## Manual UI Test Checklist

Run this only after coding queue review:

1. Set `ENABLE_HYBRID_MOTION_RENDERER=1`.
2. Keep paid provider guardrails active.
3. In the UI, choose HMR/hybrid motion mode.
4. Use free/local TTS.
5. Submit one short, known script.
6. Confirm progress polling starts and reaches a terminal state.
7. Confirm output path is not inside a frozen package.
8. Confirm render report includes `human_posting_gate`.
9. Create review package manually or via runner tooling if needed.
10. Generate platform-safe export from the resulting MP4 only after render
    review.

## Current Blockers / Notes

- The UI route currently renders directly when HMR is enabled and selected.
  The smoke harness intentionally avoids calling the route to prevent full
  renders during coding work.
- `hmr_async=true` does not activate a durable worker yet. It only records that
  non-blocking behavior was requested.
- `_task_progress` is an in-memory map. It is lost on server restart and should
  not be described as durable production progress.
- Automatic review-package creation is not part of the UI route yet.
- Platform export is available as a separate helper, not automatic UI behavior.

## Tests

Focused dry-run tests cover:

- HMR smoke plan selects the HMR path without invoking render.
- HMR smoke plan uses free-provider defaults.
- frozen manifest protection blocks unsafe output roots.
