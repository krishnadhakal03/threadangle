# HMR Proof Asset Injection

Date: 2026-05-01

## Purpose

Proof assets let a specific HMR scene use a Krishna/user-provided image or video
instead of generated, stock, or local fallback visuals. This is for receipts,
bills, calculator captures, app screenshots, browser captures, and short proof
clips.

## Folder Convention

Store local proof assets under:

```text
assets/proof/<topic_or_run>/
```

Examples:

```text
assets/proof/bill_leak/statement.png
assets/proof/grocery_receipt/run_01_hook.jpg
assets/proof/browser_capture/ai_answer.mp4
```

Supported asset types:

- `image`
- `video`
- `screenshot`
- `browser_capture`

## Input Schema

Proof assets can be passed as render inputs:

```json
{
  "scene_id": "ai_proof",
  "asset_path": "grocery_receipt/google_ai_answer.png",
  "asset_type": "screenshot",
  "crop_fit": "contain",
  "lock_behavior": "lock",
  "label": "Google AI proof"
}
```

They can also be embedded on a scene:

```json
{
  "id": "receipt_reveal",
  "proof_asset_path": "grocery_receipt/receipt_closeup.jpg",
  "proof_asset_type": "image",
  "proof_asset_crop_fit": "cover",
  "proof_asset_lock_behavior": "replace"
}
```

Targeting can use `scene_id` or `scene_role`. Supported lock behavior values:

- `replace`: use this proof asset when present.
- `lock`: use this proof asset and mark it as locked replacement metadata.
- `prefer`: prefer this proof asset when present.
- `fallback_only`: reserve for future fallback-only workflows.

## Report Fields

HMR render reports include:

- top-level `proof_asset_plan`;
- per-scene `proof_asset`;
- per-scene `proof_asset_used`.

Missing proof assets appear in `proof_asset_plan.missing_assets` and renderer
warnings as `proof_asset_missing:<scene_id>:<candidate_path>`. Missing assets do
not block generation; the existing stock/local/generated fallback continues.

No paid providers or full renders are required to validate the resolver.
