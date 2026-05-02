# HMR Agency Preset Pack

Date: 2026-05-01

## Purpose

Agency presets bundle repeatable production defaults across hooks, first-three
seconds, proof requirements, pattern interrupts, SFX, captions, and export
targets.

## Schema

Each preset includes:

- `preset_id`
- `compatible_domains`
- `hook_lab_profile`
- `first_3_sec_profile`
- `agency_template_default`
- `pattern_interrupt_profile`
- `sfx_profile`
- `caption_style_hints`
- `proof_asset_requirement_level`
- `export_preset_recommendation`

## Presets

- `money_saving_agency`
- `bill_leak_expose`
- `receipt_shock`
- `proof_first_short`
- `fast_listicle_warning`

## Helpers

`backend/utils/hmr_agency_presets.py` provides:

- `list_agency_presets()`
- `get_agency_preset(preset_id)`
- `select_agency_preset(topic, domain=None, agency_template_id=None, preset_id=None)`
- `select_agency_preset_for_scenes(scenes, script_text=\"\", agency_template=None, preset_id=None)`

HMR render reports include `agency_preset`, and manifests can carry the same
metadata. Existing HMR mode remains available; presets are additive guidance for
downstream planning.
