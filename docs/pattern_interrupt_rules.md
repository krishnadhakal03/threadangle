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
- scene-level interrupt schedules
- flattened interrupt list
- debug counts
- render-required flag set to false

`attach_pattern_interrupts_to_report` adds the plan to render reports and adds
`planned_pattern_interrupts` to matching scene reports without changing video
timing or rendering behavior.
