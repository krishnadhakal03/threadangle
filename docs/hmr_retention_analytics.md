# HMR Retention Analytics Feedback Loop

Date: 2026-05-01

## Purpose

Track posted video performance manually so future hooks, agency templates, and
creative decisions can use real retention signals.

No platform API automation is included in this slice.

## Tracker Format

Default local tracker:

```text
backend/data/hmr_retention_analytics.jsonl
```

Each line is one JSON record with:

- `platform`
- `post_url_or_id`
- `topic_domain`
- `hook_used`
- `agency_template`
- `first_frame_style`
- `video_duration_sec`
- `three_second_hold`
- `average_view_duration_sec`
- `completion_rate`
- `rewatch_rate`
- `saves`
- `shares`
- `comments`
- `follows_gained`
- `posted_at`
- `notes`
- `manifest_path`
- `issue_number`

Supported platforms:

- `youtube_shorts`
- `tiktok`
- `instagram_reels`
- `facebook_reels`
- `other`

## Helpers

`backend/utils/hmr_retention_analytics.py` provides:

- `validate_analytics_record(record)`
- `append_analytics_record(record, path=...)`
- `read_analytics_records(path=...)`
- `link_analytics_to_manifest(manifest, records)`
- `summarize_next_video_decisions(records)`

## Manual Workflow

After posting:

1. Add one record per platform.
2. Include the review package or manifest path when available.
3. Capture retention after a meaningful read window.
4. Run the summary helper before planning the next related video.
5. Use notes to decide whether to keep the hook/template, revise first-frame
   proof, or change pacing.
