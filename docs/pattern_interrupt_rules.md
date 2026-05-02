# Pattern Interrupt Rules

## Primitives

The engine supports these planned visual changes:

- `punch_zoom`
- `number_flip`
- `red_circle`
- `highlight`
- `swipe_transition`
- `checklist_tick`
- `split_screen_before_after`
- `warning_label`
- `payoff_meter`

## Scene Rules

Interrupts are assigned from deterministic scene roles:

- `hook`: punch zoom, warning label, red circle.
- `payoff`: number flip, payoff meter, highlight.
- `comparison`: split screen before/after, swipe transition, red circle.
- `checklist`: checklist tick, highlight, swipe transition.
- `warning`: warning label, punch zoom, red circle.
- `body`: highlight, swipe transition, punch zoom.

Dollar amounts can promote `number_flip` so money moments are emphasized.

## Timing

The default cadence is 1.35 seconds. Hook scenes start with an interrupt at
0.75 seconds so there is a visual change before second 2. Scenes shorter than
1.2 seconds are skipped.

## Readability Guard

Plans avoid caption overlap and cap interrupt density:

- maximum 3 interrupts per scene by default
- dense captions are limited to 1 interrupt
- interrupts stop before the final 0.25 seconds of a scene

## Metadata

`build_pattern_interrupt_plan` returns:

- primitive list
- `visual_execution_status`, currently `planned_only`
- `primitive_implementation_status`
- scene-level interrupt schedules
- flattened interrupt list
- debug counts
- render-required flag set to false

`attach_pattern_interrupts_to_report` adds the plan to render reports and adds
`planned_pattern_interrupts` to matching scene reports without changing video
timing or rendering behavior.

## Visual Execution Status

Current status for every primitive is `metadata_only`.

Implementation status:

- `punch_zoom`: metadata-only.
- `number_flip`: metadata-only.
- `red_circle`: metadata-only.
- `highlight`: metadata-only.
- `swipe_transition`: metadata-only.
- `checklist_tick`: metadata-only.
- `split_screen_before_after`: metadata-only.
- `warning_label`: metadata-only.
- `payoff_meter`: metadata-only.

Do not describe these as fully rendered effects until renderer templates consume
the primitive and tests verify pixel-visible behavior.

## Renderer Implementation Checklist

- Add a visible `punch_zoom` transform.
- Add numeric flip/count-up rendering for `number_flip`.
- Draw a visible target ring for `red_circle`.
- Add a bounded overlay treatment for `highlight`.
- Add scene-to-scene motion for `swipe_transition`.
- Render checklist state changes for `checklist_tick`.
- Build a visible before/after split for `split_screen_before_after`.
- Render warning labels in a safe area for `warning_label`.
- Render a payoff progress meter for `payoff_meter`.
- Add screenshot or pixel tests for every primitive before changing its status.
