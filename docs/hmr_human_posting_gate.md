# HMR Human Posting Gate

Date: 2026-05-01

## Purpose

HMR now reports a separate `human_posting_gate` so automated QA does not imply a
video is ready to publish before product/human review is complete.

This field is additive. It does not change `technical_status`,
`postability_status`, or postability scoring.

## Status Layers

`technical_status`

- Renderer and QA correctness.
- Examples: frame generation succeeded, captions did not crop, key numbers were
  not covered, audio/video timing is acceptable.
- Values remain `PASS` or `FAIL`.

`postability_status`

- Automated quality estimate from postability scoring.
- Examples: hook strength, motion variety, pacing, caption readability, social
  platform readiness.
- Values remain `FAIL`, `REVIEW`, `PASS`, or `STRONG_PASS`.

`human_posting_gate`

- Production decision gate for whether a candidate can move toward manual
  posting.
- Blocks can come from missing real assets, failed platform export, or human
  visual review concerns even when automated QA is strong.

## Gate Statuses

- `READY_FOR_HUMAN_POST_REVIEW`
- `BLOCKED_ASSET_MISSING`
- `BLOCKED_PLATFORM_EXPORT`
- `BLOCKED_HUMAN_VISUAL_REVIEW`
- `POSTED`
- `UNKNOWN`

## Computation Rules

`backend/utils/hmr_posting_gate.py` computes or normalizes the gate.

Priority order:

1. Keep explicit `POSTED` terminal.
2. Block on platform export failure metadata.
3. Block if planned real assets are unresolved.
4. Use an explicit valid `human_posting_gate` if one is already present.
5. Use human review recommendation text when it clearly says ready/post
   candidate or do-not-post.
6. Return `UNKNOWN` when metadata is missing or ambiguous.

This means `STRONG_PASS` plus missing planned real assets becomes
`BLOCKED_ASSET_MISSING`, not ready.

## Report Integration

The gate is included when available in:

- QA reports from `run_hybrid_motion_qa(...)`.
- render reports produced by current HMR production runners.
- review package summaries.
- future `manifest.json` files.

Missing metadata returns `UNKNOWN` rather than faking readiness.
