# Scene Intelligence / HMR Architecture Gap Audit for Issue #3

Date: 2026-04-30

This audit inspected code only. No Anthropic, OpenAI, ElevenLabs, RunwayML, Pexels, or Pixabay calls were made.

## Files Inspected

Primary HMR path:

- `backend/utils/hybrid_motion_renderer.py`
- `backend/utils/hybrid_scene_templates.py`
- `backend/utils/hybrid_motion_qa.py`
- `backend/utils/create_hmr_review_package.py`
- `backend/utils/run_hybrid_motion_poc.py`
- `backend/utils/run_hybrid_motion_colab_benchmark.py`
- `backend/utils/run_hook_retention_sprint1.py`
- `backend/utils/run_visual_realism_sprint1.py`
- `backend/routes/generate.py`

Existing scene-intelligence / stock / capture path:

- `backend/storyboard/anthropic_planner.py`
- `backend/storyboard/scene_selection_policy.py`
- `backend/storyboard/scene_critic.py`
- `backend/storyboard/creative_director.py`
- `backend/storyboard/visual_director.py`
- `backend/storyboard/provider_availability.py`
- `backend/storyboard/run_scene_selection_tests.py`
- `backend/storyboard/run_cd_day7.py`
- `backend/utils/visual_scoring.py`
- `backend/utils/video_pipeline.py`
- `backend/utils/browser_capture.py`
- `backend/utils/playwright_mocks/*.html`

Prior generated planning artifacts:

- `backend/generated_videos/storyboard_review/scene_selection_plan_day7.json`
- `backend/generated_videos/storyboard_review/scene_selection_plan_day7_diversified.json`
- `backend/generated_videos/storyboard_review/critic_report_day7.json`
- `backend/generated_videos/storyboard_review/critic_report_day7_diversified.json`
- `backend/generated_videos/storyboard_review/day7_creative_director_report.json`

## Summary

Threadforge already has multiple scene-intelligence systems:

- `backend/storyboard/anthropic_planner.py` has an Anthropic-gated creative planner with a rule-based fallback.
- `backend/storyboard/scene_selection_policy.py` wraps provider detection, the planner, and a deterministic critic.
- `backend/storyboard/creative_director.py` and `backend/storyboard/visual_director.py` contain offline scene/asset planning heuristics.
- `backend/utils/video_pipeline.py` has the richest stock intelligence: domain packs, hook query templates, stock query candidates, Pexels/Pixabay search, stock candidate quality scoring, fallback proof/screen-demo renderers, and Playwright/local demo paths.
- `backend/utils/hybrid_motion_renderer.py` has only a small local stock lookup path for `hook_footage_overlay`, with simple query rules and no bridge into the older scene intelligence.

The current HMR runners mostly bypass existing intelligence by passing explicit templates and often setting `use_stock_backgrounds=False` or `--no-stock` for deterministic free renders.

## Current HMR Architecture

### Renderer

File: `backend/utils/hybrid_motion_renderer.py`

Main function:

- `render_hybrid_video(scenes, script_text, output_path, audio_path=None, fps=30, width=1080, height=1920, use_stock_backgrounds=True, use_free_tts=True, style_preset="documentary_money_short")`

Template selection:

- `_scene_template(scene, idx)` checks explicit `template` / `hybrid_template` first.
- If no explicit template exists, it maps `method`, `medium`, `part`, or `scene_type` to a small HMR template set.
- `HYBRID_METHOD_TO_TEMPLATE` maps old-ish method labels to HMR templates, but not to assets or selector plans.

Stock path:

- `_scene_query`
- `_fetch_pexels_candidates`
- `_fetch_pixabay_candidates`
- `_score_stock_candidate`
- `_select_stock_background`

Important limitation:

- In `render_hybrid_video`, stock lookup is only attempted when `template_name == "hook_footage_overlay"`.
- All other templates render with PIL/OpenCV canvas logic, even if `use_stock_backgrounds=True`.

### Templates

File: `backend/utils/hybrid_scene_templates.py`

Current HMR template registry:

- `hook_footage_overlay`
- `money_shock_math`
- `ai_prompt_mock`
- `comparison_split`
- `payoff_number_reveal`
- `cta_callback`
- `grocery_receipt_hook`
- `grocery_reveal_scene`
- `grocery_ai_comparison`
- `grocery_savings_payoff`

These templates draw directly to OpenCV/PIL frames. The grocery templates added during Visual Realism Sprint 1 improved polish and object specificity, but they are still drawn/composited objects, not stock/captured visuals.

### HMR Runners / Benchmarks

- `backend/utils/run_hybrid_motion_poc.py`
  - Calls `render_hybrid_video(..., use_stock_backgrounds=True, ...)`.
  - Still only hook stock can be used because renderer stock lookup is hook-template-only.

- `backend/utils/run_hybrid_motion_colab_benchmark.py`
  - Has `--no-stock`.
  - Defaults `use_stock_backgrounds=not args.no_stock`.
  - Intended to avoid paid APIs and produce benchmark/report outputs.

- `backend/utils/run_hook_retention_sprint1.py`
  - Builds explicit scenes/templates.
  - Defaults `no_stock=True`, so sprint variants use local animated/compositor visuals unless `--allow-stock` is passed.

- `backend/utils/run_visual_realism_sprint1.py`
  - Builds explicit grocery scenes/templates.
  - Calls `render_hybrid_video(..., use_stock_backgrounds=False, ...)`.
  - This guarantees drawn/composited visuals.

### Route-Level HMR Path

File: `backend/routes/generate.py`

When `hybrid_motion_requested` is true:

- It calls `render_hybrid_video(...)` directly.
- It passes `scenes=make_scene_response(scenes)`.
- It passes `use_stock_backgrounds=True`.
- It bypasses `fetch_scene_clips(...)`.

When HMR is not requested:

- The old path calls `fetch_scene_clips(...)`, then `assemble_video(...)`.
- This old path gets the mature stock/Runway/Playwright/screen-demo behavior.

Therefore the route has two mostly separate video stacks:

- Old MoviePy/stock pipeline: scene intelligence active.
- HMR pipeline: scene intelligence mostly bypassed.

### Review Package Tool

File: `backend/utils/create_hmr_review_package.py`

This tool packages already-rendered HMR outputs:

- copies MP4
- creates `contact_sheet.jpg`
- copies `render_report.json`
- copies `qa_report.json`
- writes `review_summary.md`

It does not select scenes or assets. It only reports existing render/QA/human-review metadata.

### Story Candidate Generation

Recent sprint runners generate story candidates manually:

- `run_hook_retention_sprint1.py` uses `build_variants()`.
- `run_visual_realism_sprint1.py` uses `build_grocery_scenes()`.

These scene lists contain explicit `template` values, narration, captions, and template-specific fields. They do not run through the storyboard planner, old stock query generator, or provider router.

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

Important caution:

- This file imports MoviePy and `fetch_runwayml_clip` at module import.
- Its `fetch_scene_clips` function contains AI/Runway branches, though stock mode avoids Runway execution.
- Some branches are env-gated and broad.
- Directly importing this whole module into HMR would couple HMR to old pipeline dependencies and fragility.

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

Launch proof images exist under:

- `launch_assets/day6_walmart_receipts/`

Those are not currently part of an HMR asset resolver.

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

## Integration Gap

The exact architectural gap is:

1. HMR scene input has no asset strategy layer.
   - HMR receives scenes with concrete template names.
   - It does not first ask, "what visual medium should this scene use?"

2. HMR stock lookup is local and narrow.
   - It uses `_scene_query`, not the legacy `_scene_query_candidates`.
   - It tries one query concept per hook scene.
   - It only applies to `hook_footage_overlay`.

3. Old video pipeline intelligence is trapped behind the old render path.
   - The route-level HMR branch calls `render_hybrid_video` directly.
   - The route-level non-HMR branch calls `fetch_scene_clips`.
   - There is no shared scene-asset abstraction between them.

4. Playwright/UI capture exists but is only used by old pipeline helpers.
   - HMR `ai_prompt_mock` is a drawn mock.
   - HMR never calls `_render_playwright_local_demo`, `_render_screen_demo_clip`, or `RealBrowserCapture`.

5. Local assets are detected in storyboard provider logic but not resolved in HMR.
   - `provider_availability.py` knows about `assets/stock` and `assets/proofs`.
   - HMR has no provider router or local-asset resolver.

6. Sprint runners intentionally disabled provider variation for repeatability.
   - This was safe for no-paid-provider constraints, but it reinforced drawn output.

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

In short: Visual Realism Sprint 1 made better drawn visuals because that was the only visual surface HMR was using.

It did not become real/captured/stock-native because:

- no strategy bridge selected real media,
- stock was explicitly disabled,
- HMR stock only supports one hook template,
- Playwright/capture was not wired,
- existing old intelligence was outside the HMR branch.

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
     - `fallback_order`

2. Reuse safe legacy logic by extraction or thin wrappers:
   - Start with domain/query concepts from `video_pipeline.py`:
     - `_VISUAL_KEYWORD_MAP`
     - `_DOMAIN_PACKS`
     - hook/query template logic
   - Avoid importing the full `video_pipeline.py` into HMR if possible because it imports MoviePy and Runway client paths at module import.
   - Copy or extract only pure-data/pure-function pieces into a lightweight module if necessary.

3. Connect HMR stock background selection to strategy:
   - Let HMR receive `stock_query_candidates`.
   - Try candidates in order, not one hardcoded `_scene_query`.
   - Keep provider use free-only: Pexels/Pixabay only if keys exist and explicitly enabled.
   - Do not fail rendering when providers are unavailable; report fallback reason and use local/compositor fallback.

4. Extend HMR beyond hook-only stock:
   - Allow selected templates such as grocery hook/reveal/comparison to accept a `background_asset_path`, `stock_background_path`, or `resolved_asset_path`.
   - Keep compositor overlays as fallback.
   - Start with real-world scenes: hook/reveal/receipt/cart/bag contexts.

5. Add Playwright only for specific AI/UI scenes:
   - Use Option D narrowly for `ai_prompt_mock` replacement candidates.
   - Prefer existing mocks like `ai_chat_typing.html` or `spreadsheet_savings_mock.html`.
   - Do not make Playwright a general scene selector.
   - Suggested first scope: AI comparison panel and receipt audit spreadsheet/mock page.

6. Add audit/report fields, not scoring-policy changes:
   - Report `asset_strategy_used`, `query_candidates`, `selected_provider`, `fallback_reason`, and `visual_medium`.
   - Add human-review notes for realism and story-object fit.

7. Add tests:
   - Pure unit tests for strategy outputs.
   - HMR test that confirms query candidates are accepted without network calls.
   - Mock Pexels/Pixabay candidate selection if needed.

8. Keep Anthropic disabled:
   - Do not use `plan_with_anthropic` for Issue #3 implementation.
   - Later, it can be offered as an optional planning mode behind an explicit env flag.

## Recommended First Implementation Slice

The safest first PR for Issue #3 should be:

1. `hmr_scene_asset_strategy.py`
   - Pure offline strategy.
   - No network.
   - No MoviePy.
   - No paid providers.

2. Strategy output attached into HMR `render_report.json`.
   - No visual behavior change required for first commit if desired.

3. HMR stock query candidate support.
   - Update `_select_stock_background` to accept scene-provided `stock_query_candidates`.
   - Keep fallback to `_scene_query`.

4. Enable stock candidates for more than `hook_footage_overlay`.
   - Start with grocery/receipt real-world templates.
   - Keep fallback drawn template path.

5. Add one Playwright mock integration only after stock-query bridge is working.
   - Scope it to AI/UI scenes.

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
