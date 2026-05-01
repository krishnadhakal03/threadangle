# Hook Lab Flow

## Purpose

Hook Lab creates a ranked set of first-line options before video generation. It
is deterministic and local by default, so it does not call ElevenLabs, RunwayML,
Anthropic, OpenAI, or any other paid provider.

## Candidate Generation

For each topic, Hook Lab creates 5-10 candidates from local hook archetypes:

- curiosity gap
- specific number
- mistake reversal
- personal discovery
- fast payoff
- emotional pain
- clear promise
- pattern interrupt
- review challenge
- category callout

The `/generate-hooks` endpoint now uses this local path and still returns a
`hooks` list for existing callers.

## Scoring

Each candidate receives a 1-10 score for:

- curiosity
- specificity
- emotional pull
- clarity
- speed-to-payoff
- first-2-seconds strength

Candidates are ranked by total score, with first-2-seconds strength used as a
tie-breaker.

## Manual Review

Krishna can select a ranked candidate by `selected_hook_id` or provide an
`override_hook`. Overrides are scored and marked as `manual_override` so review
packages and manifests can show that the final hook came from human judgment.

## Downstream Metadata

`build_hook_lab` returns `manifest_metadata` with:

- selected hook id/text/score
- per-dimension selected hook scores
- selected archetype
- manual override flag
- ranked candidate ids
- scoring dimensions

`build_manifest` accepts this metadata through the optional `hook_lab` field.
