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

Not yet. The legacy branch is still reachable.

The stock/local adapter path currently runs only when:

- scene ID is exactly `hook` or `reveal`, and
- the planned visual medium is `stock_footage` or `stock_image`.

The legacy direct branch still runs when:

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
  - Also uses scene ID `habit_reveal` with template `hook_footage_overlay`; this can still reach the legacy direct branch.
- Older method-based scenes using `stock_plus_motion_overlay`
  - `_scene_template(...)` maps this method to `hook_footage_overlay`.
  - If the scene ID is not `hook` or `reveal`, the legacy branch can still be reached.

## Compatibility Tests Added

`backend/tests/test_hybrid_motion_renderer.py` now includes:

- `test_strategy_driven_stock_hook_uses_adapter_not_legacy_branch`
  - proves scene ID `hook` with `hook_footage_overlay` uses
    `resolve_stock_or_local_scene_asset(...)`.
- `test_legacy_hook_footage_overlay_branch_remains_reachable`
  - proves scene ID `habit_reveal` with `hook_footage_overlay` still reaches
    the legacy direct fallback branch.

## Removal Risk

Removing the legacy branch now could change behavior for existing
`hook_footage_overlay` scenes whose IDs are not exactly `hook` or `reveal`.
Those scenes could lose stock backgrounds and report as animated/template
fallbacks unless the strategy-driven path is widened first.

## Recommendation

Retain the legacy branch for now.

Next migration slice:

1. Broaden the stock/local adapter path to apply to any scene whose
   `scene_asset_strategy.visual_medium` is `stock_footage` or `stock_image`,
   not only scene IDs `hook` and `reveal`.
2. Keep the current provider order and report fields.
3. Add compatibility tests for:
   - `habit_reveal` with `hook_footage_overlay`
   - method-based `stock_plus_motion_overlay`
   - generic non-hook stock scene IDs
4. Remove the direct legacy branch only after those tests prove equivalent
   behavior.

## Frozen Package Status

The frozen grocery package remains untouched:

```text
backend/generated_videos/storyboard_review/post ready 30 april/review_package/
```
