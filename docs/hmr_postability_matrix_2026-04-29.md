# HMR v1 Postability Matrix - 2026-04-29

Validation goal: check whether Hybrid Motion Renderer v1 can consistently produce postability `PASS` across multiple scripts using gTTS, no stock footage, no ElevenLabs, and no RunwayML.

Run settings:

- Renderer: Hybrid Motion Renderer v1
- Preset: matrix quick validation, 270x480, 6 fps
- TTS: gTTS
- Stock: disabled
- Paid providers: disabled
- Output root: `backend/generated_videos/storyboard_review/hybrid_motion_postability_matrix/`

## Summary Table

| Run | Topic | Render time | Technical | Postability | Avg | Hook | Polish | Variety | Pacing | Captions | Sync | Platform | Recommendations |
| --- | --- | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| coffee_habit | Daily coffee spending habit | 88.356s | PASS | PASS | 7.29 | 7 | 7 | 8 | 7 | 8 | 7 | 7 | None |
| subscription_audit | Forgotten subscription audit | 89.535s | PASS | PASS | 7.29 | 7 | 7 | 8 | 7 | 8 | 7 | 7 | None |
| grocery_receipt | Grocery receipt swap | 90.294s | PASS | PASS | 7.29 | 7 | 7 | 8 | 7 | 8 | 7 | 7 | None |
| phone_plan | Phone plan overpayment | 89.460s | PASS | PASS | 7.29 | 7 | 7 | 8 | 7 | 8 | 7 | 7 | None |
| commute_cost | Commute cost comparison | 88.278s | PASS | PASS | 7.29 | 7 | 7 | 8 | 7 | 8 | 7 | 7 | None |

PASS rate: 5/5, 100%.

## Variance

The postability dimensions did not vary across this validation set. The current score model is mostly driven by renderer/media-class signals rather than semantic script differences, so all five runs converged to the same category scores.

Audio duration alignment was stable:

| Run | Source audio | Planned video | Final video | Delta | Strategy |
| --- | ---: | ---: | ---: | ---: | --- |
| coffee_habit | 25.872s | 25.872s | 25.833s | 0.039s | scaled_to_audio_duration_preserve_hook |
| subscription_audit | 27.072s | 27.072s | 27.072s | 0.000s | scaled_to_audio_duration_preserve_hook |
| grocery_receipt | 27.024s | 27.024s | 27.024s | 0.000s | scaled_to_audio_duration_preserve_hook |
| phone_plan | 26.784s | 26.784s | 26.667s | 0.117s | scaled_to_audio_duration_preserve_hook |
| commute_cost | 26.976s | 26.976s | 26.833s | 0.143s | scaled_to_audio_duration_preserve_hook |

## Recurring Weaknesses

Weakest recurring dimensions:

- `hook_visual_strength`: 7
- `template_polish`: 7
- `pacing_retention`: 7
- `audio_video_sync`: 7
- `social_platform_readiness`: 7

These are passing but not strong. `motion_variety` and `caption_readability` are consistently stronger at 8.

## Next Quality Target

Recommended next improvement target: template polish and platform readiness.

Reason: the renderer now reaches `PASS` consistently, but the average score stays at 7.29. The fastest route toward `STRONG_PASS` is likely not another timing fix; it is making the repeated motion-card scenes feel less generic and more platform-native while preserving the current hook and audio alignment gains.

Suggested next experiment:

- Keep the current hook.
- Upgrade one non-hook template, likely `comparison_split` or `payoff_number_reveal`, with better typography, visual hierarchy, and fewer benchmark-like card surfaces.
- Add postability signals only if they reflect real, reviewable improvements.

