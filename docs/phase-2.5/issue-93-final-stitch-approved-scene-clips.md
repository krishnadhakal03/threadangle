# Issue #93: Final Stitch From Approved Scene Clips

GitHub: https://github.com/krishnadhakal03/threadangle/issues/93

## Manual QA Finding

Sports Clip Lab needs a final stitch step that assembles only approved clips with audio, captions, music, and metadata.

## Scope

- Add a final stitch pipeline that uses approved scene clips only.
- Combine approved clips with narration/audio, captions, optional music, and generated metadata.
- Block final stitch when any required scene is missing approval.
- Keep the workflow local/dev first and explicit about what assets are being used.
- Produce a final preview/export artifact suitable for user review before any publishing step.

## Acceptance Criteria

- Final stitch can only run when every required scene clip is manually approved.
- Output includes approved clips, audio, captions, optional music, and metadata.
- The workflow does not auto-post or schedule publishing.
- The user can inspect final output/artifact paths and metadata before taking external action.
- No paid APIs or paid credits are consumed.

## Guardrails

- No Runway.
- No ElevenLabs.
- No paid credits.
- Local/dev first.
- Preserve manual approval.
- Do not auto-post.
- Run `npm build`.
