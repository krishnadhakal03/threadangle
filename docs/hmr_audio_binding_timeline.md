# HMR Audio Binding Timeline

Date: 2026-05-02

## Purpose

HMR now produces a structured audio binding timeline so voiceover, local music
beds, SFX cues, transition hits, and payoff hits can be coordinated before any
audio mix is rendered.

This workflow is local and conservative. It does not call ElevenLabs, paid music
providers, paid SFX providers, or run full video renders.

## Event Schema

`utils.hmr_audio_timeline.build_audio_binding_timeline(...)` emits:

- `voice_segment`: primary timing spine from caption/word timing or fallback
  phrase estimates
- `sfx_cue`: local SFX cue bound to a voice phrase, word/caption timing, or
  scene timing
- `music_bed`: optional local music bed under the full voice timeline
- `transition_hit`: audio accent tied to quick-cut/beat edit points
- `payoff_hit`: audio accent tied to number, savings, leak, result, or
  before/after payoff moments

The report stores these in `audio_binding_timeline.events`.

## Timing Confidence

Timeline confidence is explicit:

- `word_timing`: caption events include word-level timing metadata
- `caption_phrase_timing`: caption start/end events are available
- `fallback_estimated`: no caption timing was available, so script phrases were
  evenly estimated across scene duration
- `scene_duration_only`: no useful script or caption timing was available

## Mixing Rules

The default mix policy keeps voice first:

- `voice_priority=true`
- `voice_volume=1.0`
- `music_bed_volume=0.16`
- `music_ducking_under_voice_db=-12`
- `max_sfx_volume=0.28`
- `transition_hit_volume=0.14`
- `payoff_hit_volume=0.2`
- `limiter=0.95`

`build_audio_mix_plan(...)` returns an FFmpeg command plan without executing it.
The plan uses delayed local SFX, optional music ducking, `amix`, and a limiter.

## Renderer Report

`render_hybrid_video(...)` attaches:

- `audio_binding_timeline`
- `audio_binding_timeline.timing_source`
- `audio_binding_timeline.timing_confidence`
- `audio_binding_timeline.mix_rules`
- `audio_binding_timeline.events`
- `audio_binding_timeline.debug`

Each `scene_reports[]` row also receives `audio_bound_sfx_cues` for UI/debug
inspection.

## Current Limit

The timeline and mix command are planning outputs. The renderer still uses the
existing mux path for actual output audio; timeline-driven mix execution should
be enabled only after local music/SFX assets are curated and reviewed.
