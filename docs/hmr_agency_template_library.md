# HMR Agency Template Library

Date: 2026-05-01

## Purpose

Agency templates capture reusable high-retention structures so HMR planning does
not start from scratch for every money-saving or proof-style short.

## Schema

Each template includes:

- `template_id`
- `supported_domains`
- `hook_type`
- `scene_roles`
- `proof_requirement`
- `pacing_profile`
- `pattern_interrupt_profile`
- `sound_design_profile`
- `expected_cta_style`
- keyword hints for selection

## Initial Templates

- `bill_leak_expose`
- `receipt_shock`
- `checked_this_so_you_dont`
- `three_mistakes_costing_money`
- `before_after_savings`
- `hidden_fee_reveal`
- `one_setting_saved_me`
- `stop_paying_for_this`

## Selection

`backend/utils/hmr_agency_templates.py` provides:

- `list_agency_templates()`
- `get_agency_template(template_id)`
- `select_agency_template(topic, domain=None)`
- `select_agency_template_for_scenes(scenes, script_text=\"\")`

Selection scores topic keywords plus the HMR asset domain. HMR render reports
include `agency_template` with the selected template and compatibility scores.

This is additive. Existing non-agency HMR rendering remains available.
