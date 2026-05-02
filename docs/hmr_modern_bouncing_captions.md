# HMR Modern Bouncing Captions

Date: 2026-05-02

## Purpose

Modern Shorts captions act like part of the edit, not passive subtitles. HMR now
has caption style profiles for bounce/pop animation metadata, keyword emphasis,
phrase-aware chunk sizing, and safe mobile placement.

This is local renderer/report behavior only. It does not call paid APIs and does
not require a full render to test the profile metadata.

## Profiles

`modern_bounce` is the default HMR caption profile:

- `bounce_enabled=true`
- `pop_scale=1.12`
- `emphasis_keywords`: save/saved/found/leak/hidden/stop/compare/before/after/today/money
- `max_words_per_chunk=4`
- `safe_area`: top 12%, bottom 82%, left 8%, right 92%
- `animation_in=0.16`
- `animation_out=0.10`
- `highlight_style=mint_keyword_pop`

Additional presets:

- `clean_proof`: less animated, up to five words, for proof-first explainers
- `high_energy`: stronger bounce, three-word chunks, yellow pop highlights

## Renderer Integration

`render_hybrid_video(...)` selects `modern_bounce` and uses the profile’s
`max_words_per_chunk` for caption event generation. The existing caption drawing
path remains backward compatible: callers that do not pass a profile get the old
behavior.

The draw path now accepts optional:

- `caption_style`
- `animation_state`

When present, captions can scale during pop-in/pop-out, use profile keyword
emphasis, and return style debug fields.

## Report Metadata

Reports include:

- `caption_style_plan.profile`
- `caption_style_plan.styled_events`
- `caption_style_plan.timing_confidence`
- `caption_style_plan.debug`
- `caption_report.style_profile`
- `caption_report.bounce_enabled`
- `caption_report.highlight_style`

## Manual Review Checklist

- Caption chunks stay under the profile word limit.
- Bounced captions do not cover key numbers, proof assets, or app UI.
- Emphasis highlights land on meaningful money/action words.
- Pop animation feels energetic without making text hard to read.
- Clean/proof-first videos can switch to `clean_proof` if bounce feels too busy.

## Current Limit

The current implementation adds profile-driven draw behavior and report
metadata. Deeper per-word bounce using true Whisper word timings can build on
the same profile schema in a later pass.
