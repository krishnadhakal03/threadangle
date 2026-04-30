# Content Performance Tracker

Date: 2026-04-30

## Purpose

Track posted short-form content so retention and platform signals feed the next
HMR hook, visual, and production decisions. This document is a lightweight
manual tracker until a database or dashboard exists.

## Metrics

- `views`: platform reach.
- `average_watch_time`: average watch duration.
- `retention_drop_off`: known drop-off point or curve note.
- `full_watch_rate`: percent watched to completion.
- `comments`, `saves`, `shares`: engagement signals.
- `next_decision`: what the next production or sprint should do because of the
  data.

## Tracker

| Date | Platform | Title/topic | Hook | Video path/package | Views | Average watch time | Retention drop-off | Full-watch rate | Comments | Saves | Shares | Notes | Next decision |
| --- | --- | --- | --- | --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| 2026-04 baseline | YouTube Shorts | Coffee savings baseline | Coffee cost/habit comparison | First coffee video package, path TBD | ~184 | TBD | Flattened after initial distribution | TBD | TBD | TBD | TBD | Reach arrived, retention did not prove strong enough. | Improve first 1-4 seconds with payoff-first hooks. |
| 2026-04 baseline | TikTok | Coffee savings baseline | Coffee cost/habit comparison | First coffee video package, path TBD | 84 | ~1.41s | Very early drop-off | 0% | TBD | TBD | TBD | Cold viewers did not stay through the setup. | Show dominant loss/payoff inside first second. |
| 2026-04 baseline | Instagram Reels | Coffee savings baseline | Coffee cost/habit comparison | First coffee video package, path TBD | ~146 | TBD | TBD | TBD | 1 | TBD | TBD | Some reach and one comment. | Continue testing clearer hook visuals. |
| 2026-04 baseline | Facebook Reels | Coffee savings baseline | Coffee cost/habit comparison | First coffee video package, path TBD | ~153 | ~3s | Major drop-off around 0:04 | TBD | TBD | TBD | TBD | First four seconds are the main bottleneck. | Reduce visual/math clutter before second 4. |
| 2026-04-30 candidate | Pending | Grocery receipt / inflation savings leak | I found a $40/week leak in my grocery receipt. | `backend/generated_videos/storyboard_review/post ready 30 april/review_package/` | Pending | Pending | Pending | Pending | Pending | Pending | Pending | READY_FOR_HUMAN_POST_REVIEW. Mixed media breakthrough: stock hook/reveal plus Playwright proof-motion/payoff. | Post manually, then collect platform metrics before generating more daily variants. |
| 2026-04-30 queued | Pending | Day 9 bill leak / money-saving | I found a $27/month leak hiding in one bill. | `backend/generated_videos/storyboard_review/day9_bill_leak/review_package/` | Pending | Pending | Pending | Pending | Pending | Pending | Pending | Queued candidate. Do not make this active until grocery package is posted/reviewed. | Use only after grocery metrics or human posting decision. |

## Decision Notes

Current manual baseline says the main bottleneck is early retention:

- TikTok average watch time: about 1.41 seconds.
- Facebook average watch time: about 3 seconds.
- Facebook drop-off: around 0:04.

Near-term production should prioritize:

- one dominant number in the first second;
- real-world stock or local assets in hook/reveal;
- proof-motion for AI comparison scenes;
- no accidental topic leakage in CTA copy;
- preserving post-ready packages before new experiments.

## Update Routine

After each post:

1. Add one row per platform.
2. Record metrics after the first meaningful read window.
3. Add a short note for the likely cause of retention or engagement behavior.
4. Add one next decision, not a broad wish list.
5. Link back to the package path and issue number where possible.
