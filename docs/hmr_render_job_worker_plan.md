# HMR Render Job Worker Boundary

## Current Route Audit

`/api/generate/video/free` still executes the Hybrid Motion Renderer directly when
`scene_mode="hybrid_motion"` and `ENABLE_HYBRID_MOTION_RENDERER=1`.

The older preview-generation path already uses a queued `Generation` row,
`BackgroundTasks`, and the in-memory `_task_progress` map. The HMR UI path did
not yet have an equivalent state contract, which made future non-blocking work
hard to test without invoking the renderer.

## Current Truthful Execution Model

The current code has a serializable HMR render job state object, but it is a
scaffold only. It does not start a durable background worker.

- `queued`: job accepted, no render invoked.
- `processing`: render execution has started in the current process.
- `success`: render and productization artifacts finished.
- `failed`: renderer or artifact step failed with an explicit message.

The state object can be converted into the existing progress endpoint shape and
seeded into the `_task_progress` store once a real `Generation.id` exists. The
UI smoke plan now exposes the planned queued job state and the
`hmr_async` request flag without invoking render work.

Default `/video/free` behavior is intentionally preserved. HMR direct rendering
continues until the next migration binds this state to a background task or
external worker.

Truthfulness fields:

- `execution_mode`: currently `scaffold_only`.
- `worker_active`: currently `false`.
- `durable_progress`: currently `false`.
- `progress_store`: currently `in_memory_task_progress`.
- `non_blocking_hmr_active`: currently `false` in smoke plans.

`hmr_async=true` means the caller requested future non-blocking behavior. It does
not mean a real worker is active today.

## Worker Migration Boundary

The production worker step should:

1. Create a `Generation(status="queued")` row before render execution.
2. Seed `_task_progress[generation.id]` with `seed_hmr_render_progress`.
3. Transition to `processing` immediately before calling `render_hybrid_video`.
4. Run `materialize_hmr_ui_review_workflow` after render success.
5. Mark the row `success` only after the review package and platform export plan
   are written.
6. Mark the row `failed` with the renderer/productization error if any step
   raises.

## Implementation Slices Needed

- Add a durable HMR job table or persist job state on `Generation`.
- Move HMR render execution into `BackgroundTasks`, a queue worker, or an
  external worker process.
- Replace `_task_progress` as the source of truth, or add recovery that rebuilds
  progress from durable state.
- Make `hmr_async=true` return a queued response without doing direct render work.
- Add restart/recovery tests for queued and processing jobs.

## Remaining Risks

- `/api/generate/video/free` HMR render execution is still blocking by default.
- A true background worker must manage its own database session instead of using
  the request-scoped session.
- `_task_progress` is in-memory, so interrupted queued/processing jobs still need
  durable recovery before production use.
- No full HMR render or platform export transcoding is exercised by this slice.
