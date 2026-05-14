# Issue #90: Sports Clip Lab UI QA + Scene Card Layout Fix

GitHub: https://github.com/krishnadhakal03/threadangle/issues/90

## Manual QA Finding

Generated football images do not reliably match real player profiles, and the product should not depend on exact player likeness. Sports Clip Lab should guide users toward generic team/story visuals now and reserve exact reference workflows for later user upload/reference support.

The scene card layout also cuts off the `Regenerate Image` button.

## Scope

- Update prompt and UX guidance toward generic team, matchup, position, emotion, stadium, and story visuals.
- Avoid promising exact player likeness or real-player replication.
- Add guidance that exact player/reference workflows should come later through user-provided uploads or references.
- Fix scene card layout so all primary actions remain visible.

## Acceptance Criteria

- Scene prompt generation does not depend on exact player likeness.
- UI text clearly frames generated images as generic sports story visuals.
- `Regenerate Image` is fully visible and usable in scene cards.
- Scene cards do not clip primary actions across common desktop and narrow viewport sizes.

## Guardrails

- No Runway.
- No ElevenLabs.
- No paid credits.
- Local/dev first.
- Preserve manual approval.
- Do not auto-post.
- Run `npm build`.
