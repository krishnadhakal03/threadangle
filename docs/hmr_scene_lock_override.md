# HMR Scene Lock And Override Workflow

Date: 2026-05-01

## Purpose

Scene locks protect approved creative decisions while allowing targeted changes
to weak scenes. This avoids regenerating an entire HMR plan when only one scene
needs a new caption, asset, timing, script, or visual treatment.

## Lock Schema

```json
{
  "scene_id": "hook",
  "lock_reason": "approved hook visual",
  "locked_asset_reference": "review_package/hook.mp4",
  "locked_render_reference": "render_report.json#scene_reports[0]",
  "allowed_override_fields": ["caption"]
}
```

Supported lock fields:

- `scene_id`
- `lock_reason`
- `locked_asset_reference`
- `locked_render_reference`
- `allowed_override_fields`

If `allowed_override_fields` is empty, the scene is fully protected.

## Override Schema

```json
{
  "scene_id": "payoff",
  "fields": {
    "caption_text": "Save $43 this month.",
    "duration": 3.4,
    "proof_asset_path": "bill_leak/payoff.png"
  },
  "reason": "tighten weak payoff"
}
```

Supported override groups:

- `script`: `script`, `narration`, `narration_text`, `voiceover`
- `visual`: `visual`, `template`, `hybrid_template`, `visual_description`, `style`
- `asset`: `asset`, `asset_path`, `proof_asset_path`, `proof_asset`, `resolved_asset_path`
- `timing`: `timing`, `duration`, `start`, `end`
- `caption`: `caption`, `caption_text`, `caption_behavior`, `allow_caption_edit`

## Report Fields

HMR render reports include `scene_iteration` with:

- `locked_scenes`
- `applied_overrides`
- `rejected_overrides`
- `missing_override_targets`
- `preservation_policy`

Rejected overrides are also reported as warnings such as
`scene_override_rejected:<scene_id>`.

The workflow is metadata-first and does not require full rendering to validate
lock and override behavior.
