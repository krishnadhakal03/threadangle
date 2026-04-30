# HMR Legacy Stock Fallback Compatibility

Date: 2026-04-30

## Question

Can the remaining direct `hook_footage_overlay` stock fallback branch in
`backend/utils/hybrid_motion_renderer.py` be removed now that HMR has:

- `ResolvedSceneAsset`
- `ResolvedSceneSpec`
- Playwright adapter
- stock/local adapter
- strategy-driven coordinator path

## Finding

Updated after Slice 5: the legacy branch is retained, but strategy-planned
stock/image scenes now use the stock/local adapter path regardless of scene ID.

Before Slice 5, the stock/local adapter path only ran when:

- scene ID is exactly `hook` or `reveal`, and
- the planned visual medium is `stock_footage` or `stock_image`.

After Slice 5, the adapter path runs when:

- the planned visual medium is `stock_footage` or `stock_image`.

The legacy direct branch is still present and can still run only if a scene is
not planned as stock/image by `scene_asset_strategy` while also meeting all of
these conditions:

- `use_stock_backgrounds` is true,
- the template is `hook_footage_overlay`,
- a stock provider is configured,
- and the scene ID is not exactly `hook` or `reveal`.

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

## Removal Risk

Removing the legacy branch is lower risk after Slice 5, but it should still be
done in a tiny follow-up. The remaining risk is an unplanned/non-strategy caller
with `hook_footage_overlay` that depends on the direct branch even though
`scene_asset_strategy` does not map it to stock/image.

## Recommendation

Retain the legacy branch for Slice 5.

Next migration slice:

1. Remove the direct legacy `hook_footage_overlay` stock fallback branch in a
   tiny commit.
2. Keep the current provider order and report fields.
3. Keep the Slice 5 tests as compatibility proof.
4. Add one negative test showing unplanned `hook_footage_overlay` scenes fall
   back truthfully instead of faking stock success.

## Frozen Package Status

The frozen grocery package remains untouched:

```text
backend/generated_videos/storyboard_review/post ready 30 april/review_package/
```
