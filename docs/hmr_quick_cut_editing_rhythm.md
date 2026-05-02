# HMR Quick-Cut Editing Rhythm

Date: 2026-05-02

## Purpose

Hybrid Motion Renderer now emits an explicit editing rhythm plan for fast,
high-retention Shorts assembly. This is planning metadata only: it does not run
a full render, call paid providers, or rewrite the existing cleaner HMR path.

## Profiles

`quick_cut_shorts` is the default report profile for HMR:

- `cut_frequency`: `fast`
- `max_shot_duration`: `1.15`
- `phrase_sync_enabled`: `true`
- `beat_sync_enabled`: `true`
- `payoff_hit_timing`: `land_on_number_or_payoff_word`
- `visual_density_level`: `high_controlled`

Additional profiles are available for safer pacing:

- `balanced_clean`: moderate cuts, phrase sync, no beat accenting
- `slow_clarity`: slower hold timing for explanation-heavy scenes

## Schedule Generation

`utils.hmr_editing_rhythm.build_quick_cut_schedule(...)` accepts script text,
scene timings, optional caption events, and an optional profile id. It plans:

- scene-start cuts;
- phrase boundary cuts from caption timing;
- max-shot-duration cuts so quick edits do not hold too long;
- beat-accent cuts when the quick profile is active;
- payoff-hit cuts when a number, savings claim, leak, before/after, or result
  phrase appears.

When caption or word timing is unavailable, the planner falls back to estimated
phrase timing derived from script punctuation and compact word groups. Reports
surface this as `timing_confidence="fallback_estimated"`.

## Report Contract

`render_hybrid_video(...)` attaches:

- `editing_rhythm_plan.profile`
- `editing_rhythm_plan.timing_confidence`
- `editing_rhythm_plan.fallback_timing_used`
- `editing_rhythm_plan.payoff_hit_time`
- `editing_rhythm_plan.scene_schedules`
- `editing_rhythm_plan.cut_schedule`
- `editing_rhythm_plan.debug`

Each `scene_reports[]` row also receives:

- `planned_quick_cuts`
- `planned_quick_cut_count`

`editing_rhythm_plan.debug.render_required` is always `false` because the plan
can be tested without video rendering.

## Current Limit

The schedule is explicit metadata and report/debug scaffolding. Renderer-level
shot splitting, clip trimming, and transition execution should consume this
plan in a follow-up implementation once visual montage binding is ready.
