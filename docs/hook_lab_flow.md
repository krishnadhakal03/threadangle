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

## Endpoint Contract

`POST /api/free/generate-hooks` accepts:

- `topic` (required, non-empty, max 500 characters)
- `category` (required by the current public UI)
- `candidate_count` (optional, 5-10, default 8)
- `selected_hook_id` (optional ranked candidate id)
- `override_hook` (optional manual hook text)

The response preserves the legacy `hooks` array for older clients. Each legacy
hook contains `type`, `text`, `why_it_works`, `score`, and `rank`.

The same response also returns the Hook Lab contract:

- `schema_version`
- `topic`
- `category`
- `candidate_count`
- `score_dimensions`
- `candidates`
- `selected_hook`
- `manifest_metadata`
- `paid_providers_used`

`candidates` is the richer ranked list. Each candidate includes its `id`,
`archetype`, `text`, `why_it_works`, per-dimension `scores`, `total_score`,
`rank`, `selected`, and `override` flags.

`selected_hook` is the winning candidate by default, the requested candidate
when `selected_hook_id` matches, or a scored manual candidate when
`override_hook` is supplied. Manual overrides are exposed through
`selected_hook.override` and `manifest_metadata.manual_override`.

The public free hook UI at `frontend/src/pages/FreeHookGenerator.jsx` uses the
richer `candidates` list when available and falls back to legacy `hooks` for
backward compatibility.

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
