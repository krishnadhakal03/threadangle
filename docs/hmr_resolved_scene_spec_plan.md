# HMR ResolvedSceneSpec Plan

Date: 2026-04-30

## Purpose

Hybrid Motion Renderer now supports mixed media: stock footage, local
Playwright captures, local assets, and motion-template fallbacks. The next
architecture risk is allowing `hybrid_motion_renderer.py` to keep growing into
a source-specific branch monolith.

This document proposes a normalized resolved scene layer before more daily
content branches are added.

## Current Runtime Branches

Current relevant flow:

- `backend/utils/hmr_scene_asset_strategy.py`
  - Plans visual medium, role, query candidates, capture hints, and fallback
    order.
- `backend/utils/hybrid_motion_renderer.py`
  - Calls `plan_hmr_scene_assets`.
  - Resolves Playwright captures with `resolve_hmr_playwright_capture`.
  - Resolves hook/reveal stock or local assets through `_resolve_hook_reveal_asset`.
  - Contains fallback branches for stock provider availability.
  - Passes resolved asset fields into scene template config.
  - Builds `scene_reports`, `media_mix`, and `visual_realism_human_gate`.
- `backend/utils/hmr_playwright_capture.py`
  - Builds deterministic local HTML captures and screenshot sequences.
- `backend/utils/hybrid_scene_templates.py`
  - Renders motion templates and consumes resolved asset paths when present.

The current flow works, but planning, source resolution, fallback selection,
template config preparation, and reporting are too close together.

## Problem

Adding each new source directly inside the renderer loop creates drift:

- stock footage branches compete with Playwright branches;
- local asset fallback rules are repeated;
- template names can leak topic-specific assumptions;
- reporting fields can drift from actual resolved assets;
- adding daily scripts encourages one-off renderer changes;
- postability gates become harder to trust.

The renderer should compose already-resolved scene specs. It should not need to
know how each provider works.

## Proposed Shape

Introduce a normalized `ResolvedSceneSpec` dictionary or dataclass:

```python
{
    "scene_id": "ai_compare",
    "template": "grocery_ai_comparison",
    "duration": 3.2,
    "scene": {...},
    "asset_strategy": {
        "visual_medium": "playwright_capture",
        "asset_role": "screen_proof_or_ai_comparison",
        "query_candidates": [],
        "capture_hint": "receipt_audit_comparison",
        "fallback_order": ["playwright_capture", "local_asset", "stock_image", "motion_template"]
    },
    "resolved_asset": {
        "type": "playwright_capture",
        "path": "backend/generated_videos/cache/hybrid_motion/captures/example.png",
        "paths": ["..."],
        "provider": "local_playwright_html",
        "status": "resolved",
        "fallback_used": false,
        "query_used": null,
        "queries_attempted": [],
        "missing_config": [],
        "metadata": {
            "playwright_motion_mode": "screenshot_sequence",
            "capture_steps": ["empty_input", "typing_prompt", "submit_analyze", "results_reveal", "savings_result"],
            "visible_interaction": true,
            "saved_chrome_profile_used": false
        }
    },
    "render_config": {
        "background_path": null,
        "resolved_asset_path": "...",
        "resolved_asset_paths": ["..."],
        "playwright_motion_mode": "screenshot_sequence",
        "visible_interaction": true
    },
    "report": {
        "media_classification": "LOCAL_CAPTURE",
        "postability_signals": {}
    }
}
```

Keep the shape JSON-serializable so render reports can include it directly.

## Adapter Responsibilities

### Stock Adapter

Input:

- scene dictionary,
- query candidates,
- desired medium,
- used stock IDs,
- provider availability.

Output:

- resolved stock footage/image path,
- provider name,
- query used,
- queries attempted,
- fallback status,
- missing config details.

### Playwright Adapter

Input:

- scene dictionary,
- capture hint,
- output directory,
- viewport dimensions.

Output:

- screenshot path or sequence paths,
- HTML fallback path,
- motion mode,
- capture steps,
- visible interaction flag,
- failure reason if Playwright is unavailable.

### Local Asset Adapter

Input:

- scene ID,
- asset role,
- domain or production slug.

Output:

- local file path if present,
- asset type,
- fallback status,
- expected local filenames when missing.

### Motion Template Adapter

Input:

- scene dictionary,
- template name,
- previous adapter failures.

Output:

- explicit fallback spec,
- no fake real-asset success,
- reason for fallback.

## Migration Order

1. Add type aliases or a small dataclass for `ResolvedSceneAsset` and
   `ResolvedSceneSpec`.
2. Extract current Playwright resolution call into a `resolve_playwright_asset`
   adapter wrapper without changing behavior.
3. Extract stock/local hook-reveal resolution into `resolve_stock_or_local_asset`.
4. Add a resolver coordinator that accepts scene + strategy and returns one
   `ResolvedSceneSpec`.
5. Update the renderer loop to consume `ResolvedSceneSpec.render_config`.
6. Update `scene_reports` to serialize from `ResolvedSceneSpec.report`.
7. Add tests for asset strategy, adapter fallback truthfulness, and report
   consistency.

Do this in narrow slices. Avoid rewriting templates during the first extraction.

## Test Plan

- Unit-test planner output for grocery and bill-leak scenes.
- Unit-test adapter behavior with provider keys removed.
- Unit-test Playwright unavailable path does not mark assets as resolved.
- Unit-test local asset fallback path with fake image/video files.
- Render a tiny mixed-media scene set without stock keys.
- Keep the required HMR regression test:

```powershell
python -m pytest backend/tests/test_hybrid_motion_renderer.py -q
```

## Risks

- Over-abstracting too early could slow daily production.
- Changing report field names could break existing review package tooling.
- Adapter extraction could accidentally mark fallback templates as real assets.
- Existing template names are still topic-specific in places, so the resolver
  must use scene content and strategy, not template names alone, for domain
  decisions.

## Next Recommended Engineering Sprint

Implement `ResolvedSceneAsset` first, then extract Playwright resolution behind
an adapter. Playwright is the safest first adapter because it is local,
deterministic, and already reports proof-motion metadata.
