# HMR Legacy Stock Fallback Compatibility

Date: 2026-05-01

## Question

Can the remaining direct `hook_footage_overlay` stock fallback branch in
`backend/utils/hybrid_motion_renderer.py` be removed now that HMR has:

- `ResolvedSceneAsset`
- `ResolvedSceneSpec`
- Playwright adapter
- stock/local adapter
- strategy-driven coordinator path

## Finding

Updated after Slice 6: the legacy branch has been removed. Strategy-planned
stock/image scenes use the stock/local adapter path regardless of scene ID.

Before Slice 5, the stock/local adapter path only ran when:

- scene ID is exactly `hook` or `reveal`, and
- the planned visual medium is `stock_footage` or `stock_image`.

After Slice 5, the adapter path runs when:

- the planned visual medium is `stock_footage` or `stock_image`.

The previous direct branch could run when a scene was not planned as stock/image
by `scene_asset_strategy`, had template `hook_footage_overlay`, and stock
backgrounds/providers were enabled. That path could make an unplanned scene look
like a successful stock resolution.

After Slice 6, unplanned scenes do not call the stock selector directly. They
fall back through the normal animated/motion template path with no resolved stock
asset and `asset_resolution_status=not_attempted`.

## Callers And Scene Builders

Known `hook_footage_overlay` usage:

- `backend/utils/run_hybrid_motion_poc.py`
  - Uses scene ID `hook`; this uses the strategy-driven stock/local adapter path.
- `backend/utils/run_hook_retention_sprint1.py`
  - Uses scene ID `hook`; this uses the strategy-driven stock/local adapter path.
  - Also uses scene ID `habit_reveal` with template `hook_footage_overlay`;
    after Slice 5 this is covered by the strategy-driven stock/local adapter path.
- Older method-based scenes using `stock_plus_motion_overlay`
  - `_scene_template(...)` maps this method to `hook_footage_overlay`.
  - After Slice 5 this is covered by the strategy-driven stock/local adapter path
    when `scene_asset_strategy` maps the template to `stock_footage`.

## Compatibility Tests Added

`backend/tests/test_hybrid_motion_renderer.py` now includes:

- `test_strategy_driven_stock_hook_uses_adapter_not_legacy_branch`
  - proves scene ID `hook` with `hook_footage_overlay` uses
    `resolve_stock_or_local_scene_asset(...)`.
- `test_generalized_stock_adapter_covers_habit_reveal_hook_overlay`
  - proves scene ID `habit_reveal` with `hook_footage_overlay` now uses
    `resolve_stock_or_local_scene_asset(...)` and does not call the legacy branch.
- `test_generalized_stock_adapter_covers_method_mapped_stock_overlay`
  - proves method-based `stock_plus_motion_overlay` scenes mapped to
    `hook_footage_overlay` now use the adapter path.
- `test_generalized_stock_adapter_covers_generic_non_hook_stock_scene`
  - proves a generic non-hook stock scene ID with `visual_medium=stock_image`
    now uses the adapter path.
- `test_unplanned_hook_overlay_does_not_fake_stock_success`
  - proves an unplanned `hook_footage_overlay` scene does not call the adapter
    or the removed direct stock branch, and reports no resolved stock asset.

## Removal Risk

The main risk after removal is an older unplanned caller that expected
`hook_footage_overlay` alone to trigger provider lookup. That caller now needs a
real `scene_asset_strategy` stock/image plan to resolve stock. This is
intentional: unplanned scenes should not fake stock success or hide missing
planning.

## Recommendation

The legacy branch is removed. Keep future stock/local work on the
`scene_asset_strategy` plus `resolve_stock_or_local_scene_asset(...)` path so
all report fields come from the normalized `ResolvedSceneSpec` asset contract.

## Frozen Package Status

The frozen grocery package remains untouched:

```text
backend/generated_videos/storyboard_review/post ready 30 april/review_package/
```
