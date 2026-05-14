# Issue #91: Local Image Motion Preview Engine

GitHub: https://github.com/krishnadhakal03/threadangle/issues/91

## Manual QA Finding

Sports Clip Lab needs a local image-to-motion preview so users can evaluate generated stills as simple motion clips before deciding whether to use external tools.

## Scope

- Add a local/dev-first image-to-motion preview engine.
- Generate short preview clips from still images using local processing only.
- Support basic motion treatments such as slow zoom, pan, hold, and subtle crop movement where feasible.
- Keep output suitable for review/approval rather than production-grade paid video generation.
- Store local motion preview artifacts in a way that can feed per-scene decisions.

## Acceptance Criteria

- A user can generate a short local motion preview from a Sports Clip Lab scene image.
- Preview generation consumes no paid credits and calls no paid video APIs.
- The user can review the local motion preview before approving it.
- Failure states are visible and recoverable per scene.
- Generated preview assets have clear local/dev lifecycle handling.

## Guardrails

- No Runway.
- No ElevenLabs.
- No paid credits.
- Local/dev first.
- Preserve manual approval.
- Do not auto-post.
- Run `npm build`.
