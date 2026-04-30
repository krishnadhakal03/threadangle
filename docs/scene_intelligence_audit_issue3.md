# Scene Intelligence Audit for Issue #3

Date: 2026-04-30

This audit inspected code only. No Anthropic, OpenAI, ElevenLabs, RunwayML, Pexels, or Pixabay calls were made.

## Summary

Threadforge already has multiple scene-intelligence systems:

- `backend/storyboard/anthropic_planner.py` has an Anthropic-gated creative planner with a rule-based fallback.
- `backend/storyboard/scene_selection_policy.py` wraps provider detection, the planner, and a deterministic critic.
- `backend/storyboard/creative_director.py` and `backend/storyboard/visual_director.py` contain offline scene/asset planning heuristics.
- `backend/utils/video_pipeline.py` has the richest stock intelligence: domain packs, hook query templates, stock query candidates, Pexels/Pixabay search, stock candidate quality scoring, fallback proof/screen-demo renderers, and Playwright/local demo paths.
- `backend/utils/hybrid_motion_renderer.py` has only a small local stock lookup path for `hook_footage_overlay`, with simple query rules and no bridge into the older scene intelligence.

The current HMR runners mostly bypass existing intelligence by passing explicit templates and often setting `use_stock_backgrounds=False` or `--no-stock` for deterministic free renders.

## Existing Anthropic/Claude Selector

File: `backend/storyboard/anthropic_planner.py`

Function: `plan_with_anthropic(scenes: List[Dict]) -> List[Dict]`

Fallback function: `_rule_based_plan(scenes, providers)`

Current usage:

- Called by `backend/storyboard/scene_selection_policy.py` in `run_policy_on_storyboard`.
- That policy is used by `backend/storyboard/run_scene_selection_tests.py`.
- It does not appear to be connected to `backend/utils/hybrid_motion_renderer.py` or current HMR sprint runners.

Credit behavior:

- Requires `ANTHROPIC_API_KEY` and `ENABLE_ANTHROPIC_PLANNER=1`.
- If both are enabled, it calls Claude (`anthropic.Client(...).completions.create(model="claude-2.1", ...)`) and uses API credits.
- Otherwise it returns deterministic rule-based plans without API calls.

## Existing Scene Intelligence

### Storyboard Scene Selection

- `backend/storyboard/scene_selection_policy.py`
  - `run_policy_on_storyboard`
  - Coordinates provider detection, `plan_with_anthropic`, and `run_critic`.

- `backend/storyboard/scene_critic.py`
  - `run_critic`
  - Flags generated-card hook use, prompt scenes not using capture, shock/proof scenes without visual objects, generated-card overuse, and consecutive same media.

- Generated prior outputs exist:
  - `backend/generated_videos/storyboard_review/scene_selection_plan_day7.json`
  - `backend/generated_videos/storyboard_review/scene_selection_plan_day7_diversified.json`
  - `backend/generated_videos/storyboard_review/critic_report_day7.json`
  - `backend/generated_videos/storyboard_review/critic_report_day7_diversified.json`

### Offline Creative / Asset Planning

- `backend/storyboard/creative_director.py`
  - `generate_creative_plan`
  - `plan_assets_for_scene`
  - `run_qa_on_plans`
  - Chooses media such as `stock_clip`, `playwright_browser_capture`, `comparison_card`, `payoff_card`, and `generated_card_last_resort`.

- `backend/storyboard/visual_director.py`
  - `classify_scene`
  - `plan_assets`
  - `visual_modality_breakdown`
  - Maps beats to visual media and required objects.

### Legacy Stock / Scene Pipeline

- `backend/utils/video_pipeline.py`
  - `_VISUAL_KEYWORD_MAP`
  - `_DOMAIN_PACKS`
  - `_stock_hook_visual_intent`
  - `_stock_hook_visual_description`
  - `_hook_query_templates`
  - `_scene_query_candidates`
  - `_score_clip_quality_for_scene`
  - `_build_visual_profile`
  - `_search_pexels_video`
  - `_search_pixabay_video`
  - `_download_file`
  - `fetch_scene_clips`

This is the strongest reusable scene-intelligence layer today. It has domain packs for phone bills, subscriptions, airline, rent, generic money problems, and creator tools, plus stock query generation and clip quality/diversity checks.

### Playwright / Local UI Demos

- `backend/utils/browser_capture.py`
  - `RealBrowserCapture`
  - Browser-recorded local DOM scenes, no external login/private surface needed.

- `backend/utils/playwright_mocks/`
  - `ai_chat_typing.html`
  - `ai_script_mock.html`
  - `editor_mock.html`
  - `search_results_mock.html`
  - `spreadsheet_savings_mock.html`
  - `travel_compare_mock.html`
  - `video_gen_mock.html`
  - `voice_mock.html`

- `backend/utils/video_pipeline.py`
  - `_render_playwright_local_demo`
  - `_render_screen_demo_clip`
  - `_render_proof_scene_clip`
  - `_render_before_after_proof_clip`
  - `_render_hook_shock_clip`

These are not wired into HMR.

### Local Assets

Provider detection checks for:

- `assets/stock`
- `assets/proofs`
- `PLAYWRIGHT_SANDBOX_PROFILE`

In this workspace, `assets/stock` and `assets/proofs` were not present in the inspected listing. Most visible local assets are voice caches and launch proof images.

## HMR Connection Status

File: `backend/utils/hybrid_motion_renderer.py`

HMR has a small internal stock path:

- `_scene_query`
- `_provider_available`
- `_fetch_pexels_candidates`
- `_fetch_pixabay_candidates`
- `_score_stock_candidate`
- `_download_stock_candidate`
- `_select_stock_background`

But it only runs when:

- `use_stock_backgrounds=True`
- template is exactly `hook_footage_overlay`
- `PEXELS_API_KEY` or `PIXABAY_API_KEY` exists

HMR does not call:

- `scene_selection_policy.run_policy_on_storyboard`
- `anthropic_planner.plan_with_anthropic`
- `creative_director.generate_creative_plan`
- `visual_director.plan_assets`
- `video_pipeline._scene_query_candidates`
- `video_pipeline.fetch_scene_clips`
- Playwright demo renderers

HMR templates are selected from explicit scene `template` fields or simple method/scene-type mapping. Current sprint runners build explicit scene dicts and bypass old planning.

## Why Visual Realism Sprint 1 Still Used Drawn/Prototype Visuals

Exact reasons:

1. HMR bypasses the old stock pipeline.
   - It does not use `video_pipeline.fetch_scene_clips` or `_scene_query_candidates`.

2. The Visual Realism Sprint 1 runner explicitly disables stock:
   - `render_hybrid_video(..., use_stock_backgrounds=False, ...)`

3. HMR stock lookup is narrow even when enabled:
   - only `hook_footage_overlay` gets stock backgrounds.
   - new grocery templates and AI/comparison/payoff templates never ask for stock or local assets.

4. No asset strategy bridge exists.
   - Old planner outputs `chosen_medium`, `asset_query_or_capture_instruction`, `required_visual_objects`.
   - HMR expects concrete `template` names and optional stock backgrounds only for one template.

5. Templates are still compositor-drawn.
   - Visual Realism Sprint 1 improved drawing polish, but it remained generated by PIL/OpenCV templates rather than real stock/captures.

6. Playwright is not wired to HMR.
   - Existing Playwright mocks and browser capture renderers live in `video_pipeline.py` / `browser_capture.py`.
   - HMR uses `ai_prompt_mock`, a local drawn panel.

7. Provider keys may be absent, and HMR runners choose deterministic no-stock paths.
   - This was intentional to avoid paid/provider risk during sprint rendering.

## Reuse Recommendation

Smallest safe next step: **Option C with reuse from Option B**.

Build a small HMR-only `scene_asset_strategy` bridge that reuses the legacy query/domain intelligence but does not import or run the whole `video_pipeline.fetch_scene_clips` pipeline.

Do not start with Anthropic. The Anthropic planner is real, but it is gated, credit-using, older API style, and not connected to HMR. It should remain optional/off by default.

Do not broadly wire `fetch_scene_clips` into HMR as-is. It is powerful, but it carries old MoviePy pipeline assumptions, Runway branches, many env gates, and known test fragility.

## Proposed Implementation Plan for Issue #3

1. Add a small offline HMR strategy module:
   - Suggested file: `backend/utils/hmr_scene_asset_strategy.py`
   - Inputs: HMR scene dicts.
   - Outputs per scene:
     - `asset_role`
     - `visual_medium`
     - `query_candidates`
     - `template_hint`
     - `capture_hint`
     - `reason`

2. Reuse safe legacy logic by extraction or thin wrappers:
   - Start with domain/query concepts from `video_pipeline.py`:
     - `_VISUAL_KEYWORD_MAP`
     - `_DOMAIN_PACKS`
     - hook/query template logic
   - Avoid importing the full `video_pipeline.py` into HMR if possible because it imports MoviePy and Runway client paths at module import.

3. Connect HMR stock background selection to strategy:
   - Let HMR receive `stock_query_candidates`.
   - Try candidates in order, not one hardcoded `_scene_query`.
   - Keep provider use free-only: Pexels/Pixabay only if keys exist and explicitly enabled.

4. Extend HMR beyond hook-only stock:
   - Allow selected templates such as grocery hook/reveal/comparison to accept a `background_asset_path` or `stock_background_path`.
   - Keep compositor overlays as fallback.

5. Add Playwright only for specific AI/UI scenes:
   - Use Option D narrowly for `ai_prompt_mock` replacement candidates.
   - Prefer existing mocks like `ai_chat_typing.html` or `spreadsheet_savings_mock.html`.
   - Do not make Playwright a general scene selector.

6. Add audit/report fields, not scoring-policy changes:
   - Report `asset_strategy_used`, `query_candidates`, `selected_provider`, `fallback_reason`, and `visual_medium`.
   - Add human-review notes for realism and story-object fit.

7. Add tests:
   - Pure unit tests for strategy outputs.
   - HMR test that confirms query candidates are accepted without network calls.
   - Mock Pexels/Pixabay candidate selection if needed.

## Risks

- Importing `video_pipeline.py` directly may pull in MoviePy/Runway-related dependencies and unrelated failure modes.
- Existing stock pipeline has many env-gated branches and may be too broad for HMR.
- Anthropic planner can consume credits if enabled; keep disabled by default.
- Pexels/Pixabay can improve realism but introduces provider availability and relevance variance.
- Playwright capture is promising but should be limited to AI/UI scenes to avoid scope creep.

## Duplication Risk

Yes, building a brand-new selector from scratch would duplicate old work.

The reusable work is strongest in:

- legacy stock query/domain intelligence in `video_pipeline.py`
- storyboard policy/critic concepts in `storyboard/`
- existing Playwright/local UI mock assets

The missing piece is not intelligence. The missing piece is a small HMR bridge that converts scene intent into HMR-compatible assets, query candidates, and template hints.
