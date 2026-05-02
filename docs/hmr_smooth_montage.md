# HMR Smooth Multi-Clip Montage

Date: 2026-05-02

## Purpose

Quick cuts need a montage layer so fast edits feel intentional instead of
randomly stitched. HMR now emits a smooth montage plan that sequences
local/stock/proof clips, normalizes clip durations, and chooses transition
metadata aligned to voice, beats, and payoff hits.

This is report/planning metadata. It does not run a full render and does not
call paid providers.

## Montage Schema

Each planned clip includes:

- `clip_id`
- `scene_id`
- `path`
- `timeline_start`
- `timeline_end`
- `trim_start`
- `trim_end`
- `transition_in`
- `transition_out`
- `speed_factor`
- `beat_voice_alignment_marker`
- `motion_continuity_hint`
- `motion_continuity_score`
- `source_status`

Supported transitions:

- `hard_cut`
- `whip_cut`
- `speed_ramp`
- `crossfade_short`
- `match_motion_cut`
- `zoom_blend`

## Profiles

`smooth_high_energy_shorts` is the default HMR montage profile:

- max clip duration: 1.35s
- min clip duration: 0.45s
- beat aligned: true
- voice aligned: true
- default transition: `match_motion_cut`
- continuity target: direction or energy match

`clean_proof_montage` is available for slower proof-first scenes.

## Planning Rules

The planner consumes:

- `scene_reports`
- `scene_timings`
- `editing_rhythm_plan`
- `audio_binding_timeline`

If a scene has `resolved_asset_paths`, the planner rotates through those assets
for micro-clips. If only `resolved_asset_path` exists, it uses that path. If no
asset is resolved, it truthfully marks the clip as a generated motion template
placeholder such as `generated_motion_template:ai_prompt_mock`.

Transition choice is deterministic:

- first clip starts with `hard_cut`
- payoff/number reveal clips prefer `zoom_blend`
- beat accents prefer `whip_cut`
- comparison scenes prefer `match_motion_cut`
- periodic high-energy clips may use `speed_ramp`

## Report Metadata

`render_hybrid_video(...)` now attaches:

- `montage_plan`
- `montage_plan.profile`
- `montage_plan.transitions_supported`
- `montage_plan.clips`
- `montage_plan.debug`
- `montage_execution_status`
- `executed_transition_types`
- `planned_only_transition_types`
- `planned_vs_executed_clip_count`
- `montage_renderer_execution`

Each scene report also receives:

- `montage_clips`
- `montage_clip_count`

## Manual QA Checklist

- Transitions feel smooth, not random.
- Number/payoff moments land on `zoom_blend` or another clear emphasis.
- Beat/voice alignment markers match the audio timeline.
- Resolved stock/proof/local assets are not overstretched.
- Generated-template placeholders are reviewed before claiming real multi-clip
  footage.

## Current Limit

The renderer now consumes the quick-cut portion of the montage/rhythm plan for a
minimal execution slice:

- `hard_cut` is executed by resetting local template/background progress at
  planned micro-cut boundaries;
- `zoom_blend` is executed as a short in-frame zoom pulse on payoff cuts.

The remaining transition types are still planned-only metadata:

- `whip_cut`
- `speed_ramp`
- `crossfade_short`
- `match_motion_cut`

Those transitions should consume `montage_plan.clips` in a later renderer pass
once the frame compositor supports them directly.
