# Playwright UI/Server-Safe Capture

Date: 2026-05-01

## Purpose

HMR Playwright captures can be triggered from CLI runners or from UI/server
generation paths. FastAPI route handlers may already have an active asyncio
event loop, so capture code must not depend exclusively on direct
`asyncio.run(...)`.

## Safe Execution Path

`backend/utils/hmr_playwright_capture.py` uses `_run_capture_coroutine(...)` for
HTML-to-PNG capture work.

Behavior:

- CLI/no active event loop: run the coroutine with `asyncio.run(...)`.
- Active UI/server event loop: run the coroutine inside a short-lived isolated
  thread, where `asyncio.run(...)` owns that thread's loop.
- Exceptions are propagated back to the caller and converted into the existing
  HMR asset-resolution failure report fields.

This preserves the synchronous renderer contract while avoiding
`RuntimeError: asyncio.run() cannot be called from a running event loop`.

## UI Route Context

`backend/routes/generate.py` can call `render_hybrid_video(...)` for
`scene_mode=hybrid_motion`. That renderer path resolves Playwright capture
assets through:

```text
render_hybrid_video(...)
resolve_playwright_scene_asset(...)
resolve_hmr_playwright_capture(...)
_run_capture_coroutine(...)
```

## Report Contract

The safe runner does not change HMR visual output or report field names.
Successful captures still report:

- `resolved_asset_type=playwright_capture`
- `resolved_asset_provider=local_playwright_html`
- `playwright_motion_mode`
- `capture_steps`
- `visible_interaction`

When Playwright is unavailable or capture fails, the renderer still falls back
truthfully with `fallback_used=true` and an `asset_resolution_status` beginning
with `playwright_unavailable:` or `playwright_capture_failed:`.

## Testing

Focused tests cover:

- normal no-event-loop capture calls,
- already-running event-loop calls,
- truthful unavailable/failure reporting,
- screenshot-sequence report fields.

No full renders are required for this runtime-safety check.
