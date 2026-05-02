# HMR Render Job Worker Boundary

## Current Route Audit

`/api/generate/video/free` keeps the existing direct HMR path for normal
requests. When `scene_mode="hybrid_motion"`, `ENABLE_HYBRID_MOTION_RENDERER=1`,
and `hmr_async=true`, the route now queues a durable HMR background job and
returns immediately.

## Current Truthful Execution Model

The async HMR path now persists progress in `hmr_render_jobs`:

- `queued`: durable job accepted, no render invoked yet.
- `processing`: background worker started and render invocation began.
- `success`: render and productization artifacts finished.
- `failed`: renderer, productization, restart, or worker error was recorded.

Truthfulness fields for active async HMR jobs:

- `execution_mode`: `background_task`
- `worker_active`: `true` while queued/processing, `false` after terminal state
- `durable_progress`: `true`
- `progress_store`: `hmr_render_jobs`
- `non_blocking_hmr_active`: `true`

Direct HMR rendering remains available when `hmr_async` is false.

## Worker Behavior

The current worker is an in-process FastAPI `BackgroundTasks` worker. It:

1. creates a queued `Generation` row;
2. creates a durable `HMRRenderJob` row;
3. returns a queued response to the caller;
4. opens its own `AsyncSessionLocal` session;
5. transitions `queued -> processing -> success/failed`;
6. calls `render_hybrid_video(...)`;
7. calls `materialize_hmr_ui_review_workflow(...)`;
8. stores result/error metadata on the durable job row.

Progress polling checks `hmr_render_jobs` before falling back to the older
in-memory `_task_progress` map.

## Recovery

`recover_interrupted_hmr_jobs(...)` marks queued or processing durable jobs as
failed after restart or worker interruption. This keeps the UI from treating a
lost in-process worker as endlessly active.

## Guardrails

- The async HMR worker owns its DB session instead of using the request-scoped
  session.
- The worker uses free/local HMR behavior and does not call ElevenLabs, RunwayML,
  Anthropic, OpenAI, Gemini, or paid music/SFX providers.
- Frozen-output checks still run through the HMR productization path.

## Remaining Risks

- This is an in-process background task, not an external queue. A process crash
  can interrupt active work, but durable state now makes that failure recoverable
  and visible.
- Full production HMR render coverage still belongs in an explicit manual or CI
  environment that permits render runtime.
