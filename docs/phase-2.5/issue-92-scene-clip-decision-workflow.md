# Issue #92: Scene Clip Decision Workflow

GitHub: https://github.com/krishnadhakal03/threadangle/issues/92

## Manual QA Finding

Sports Clip Lab needs a per-scene decision workflow after image generation and local motion preview: approve the local motion clip, regenerate the image, or upload an external clip.

## Scope

- Add per-scene state for clip source and approval status.
- Let users approve a local motion clip.
- Let users regenerate an image without losing unrelated scene decisions.
- Let users upload an external clip for a scene.
- Keep manual approval required before any scene can be used in final stitching.
- Preserve generated image, local preview, and uploaded clip metadata for each scene.

## Acceptance Criteria

- Each scene displays its current decision state.
- Final workflow can distinguish approved local motion clips from uploaded external clips.
- A scene cannot silently advance to final stitching without manual approval.
- Users can regenerate an image without losing unrelated approved scenes.
- Users can upload an external clip for a scene and approve it manually.

## Guardrails

- No Runway.
- No ElevenLabs.
- No paid credits.
- Local/dev first.
- Preserve manual approval.
- Do not auto-post.
- Run `npm build`.
