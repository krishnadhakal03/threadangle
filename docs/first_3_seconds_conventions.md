# First 3 Seconds Conventions

## Purpose

The first 3 seconds are planned separately from normal scene flow. The goal is
to give Shorts/Reels/TikTok a swipe-stop opening before the rest of the script
continues unchanged.

## Required Fields

Each first-3-seconds plan includes:

- `big_claim_text`: the compressed opening claim from the selected hook.
- `proof_object`: the visible object that makes the claim feel real.
- `number_payoff_preview`: the number, money value, or payoff teased early.
- `urgency_warning_label`: a short label such as `CHECK THIS FIRST`.
- `no_slow_intro`: always true for this slice.
- `pattern_interrupt`: a snap zoom or hard cut before second 2.

## Timing

Default timing hints:

- `0.00-0.45`: big claim text.
- `0.45-1.20`: proof object.
- `1.20-1.65`: pattern interrupt.
- `1.65-3.00`: number/payoff preview.

## Metadata

The planner does not render video. It produces metadata for smoke plans, render
reports, human review fields, and manifests:

- `first_frame_style`
- `first_3_sec_strategy`
- `human_review.first_frame_style`
- `human_review.first_three_seconds_strategy`
- `manifest.first_3_seconds`

## Visual Execution Status

Current status: `planned_only`.

The fields below are planning/review metadata today. They do not guarantee that
renderer templates visually execute the treatment:

- `big_claim_text`: metadata-only.
- `proof_object`: metadata-only.
- `pattern_interrupt`: metadata-only.
- `number_payoff_preview`: metadata-only.

Future renderer work should move individual items to `partially_executed` or
`fully_executed` only after pixel-visible behavior is implemented and tested.

## Renderer Checklist

- Render big claim text as a first-frame layer.
- Prefer or crop a real proof object during `0.45-1.20`.
- Execute the planned snap zoom or hard cut before second 2.
- Reveal the payoff/number preview before second 3.
- Add screenshot/pixel tests that prove each executed behavior is visible.

## Guardrails

- Preserve existing script and caption text.
- Avoid slow intros, logo intros, and empty establishing shots.
- Do not call paid APIs.
- Do not run full renders for plan tests.
