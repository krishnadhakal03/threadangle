# Post-Ready Artifact Convention

Date: 2026-05-01

## Purpose

Post-ready packages are frozen review artifacts. Once a package is marked ready
for human posting or human post review, it must not be overwritten, regenerated,
or edited in place unless a task explicitly says to modify that exact package.

This protects the final candidate from accidental daily-production churn.

## Folder Rules

Use a unique output folder for each production candidate:

```text
backend/generated_videos/storyboard_review/<production_slug>/
```

Use a stable flat review package inside that folder:

```text
backend/generated_videos/storyboard_review/<production_slug>/review_package/
```

Examples:

```text
backend/generated_videos/storyboard_review/post ready 30 april/review_package/
backend/generated_videos/storyboard_review/day9_bill_leak/review_package/
```

Do not generate new work into an existing post-ready folder. Create a new slug
for every new candidate, sprint rerun, or substantial revision.

## Required Files

Every post-ready package should include:

- `*.mp4`: final full-resolution video.
- `contact_sheet.jpg`: broad visual scan sheet.
- `render_report.json`: renderer output and per-scene asset resolution.
- `qa_report.json`: technical and postability QA.
- `review_summary.md`: human-review summary.
- `manifest.json`: lightweight package identity and posting state.

If a Playwright proof-motion sequence is used, include:

- `ai_compare_proof_motion_contact_sheet.jpg`

## Naming Convention

Use descriptive lowercase slugs with dates or content identifiers:

```text
visual_realism_sprint1_grocery_full.mp4
day9_bill_leak_full.mp4
```

Recommended package slug format:

```text
<day_or_date>_<topic>_<variant_optional>
```

Examples:

```text
day9_bill_leak
2026-04-30_grocery_receipt_post_ready
day10_subscription_audit_v2
```

## Do-Not-Overwrite Rule

Before a runner writes to an output folder, check whether that folder already
contains a post-ready package. A package should be treated as frozen if it has:

- a full MP4,
- `review_summary.md`,
- `qa_report.json`,
- and a human decision of `POST REVIEW CANDIDATE`, `READY_FOR_HUMAN_POST_REVIEW`,
  `POST`, or equivalent in `manifest.json`, `review_summary.md`, or the sprint
  summary.

If the existing package is frozen, create a new output folder instead of
rewriting it.

Code guard:

- `backend/utils/hmr_artifact_manifest.py` defines `assert_not_frozen_output(...)`.
- Review package creation and flat `review_package/` replacement must call the
  guard before writing, deleting, or copying package files.
- A missing manifest does not block generation, which keeps older working
  folders compatible.
- `force=True` is an explicit maintenance-only escape hatch. Use it only when a
  task names the frozen package and says to update it.

## Safe Daily Output Flow

1. Pick a new production slug before rendering.
2. Write all temporary render output under that slug only.
3. Create or update the flat `review_package/` inside that slug.
4. Add `manifest.json` after QA and human-review notes are available.
5. Mark the package frozen only after it becomes the chosen posting candidate.
6. Never reuse the frozen package path for exploratory reruns.

## Manifest Structure

Use this lightweight schema for `manifest.json`:

```json
{
  "schema_version": 1,
  "topic": "Bill leak / money-saving",
  "hook": "I found a $27/month leak hiding in one bill.",
  "created_at": "2026-05-01T18:30:00+00:00",
  "video_path": "backend/generated_videos/storyboard_review/day9_bill_leak/review_package/day9_bill_leak_full.mp4",
  "review_package_path": "backend/generated_videos/storyboard_review/day9_bill_leak/review_package/",
  "technical_status": "PASS",
  "postability_status": "STRONG_PASS",
  "average_score": 8.43,
  "human_posting_gate": "READY_FOR_HUMAN_POST_REVIEW",
  "media_mix": {
    "REAL_STOCK": 2,
    "LOCAL_CAPTURE": 2,
    "ANIMATED_FALLBACK": 1
  },
  "resolved_real_assets": [
    {
      "scene_id": "hook",
      "type": "stock_footage",
      "provider": "local_asset",
      "path": "backend/generated_videos/storyboard_review/day9_bill_leak/review_package/hook.mp4"
    }
  ],
  "paid_providers_used": {
    "elevenlabs": false,
    "runwayml": false,
    "paid_llm": false
  },
  "frozen": false,
  "posted_platforms": [],
  "analytics_placeholders": {
    "youtube_shorts": null,
    "tiktok": null,
    "instagram_reels": null,
    "facebook_reels": null
  }
}
```

## Current Frozen Package

As of this sprint, the current frozen grocery package is:

```text
backend/generated_videos/storyboard_review/post ready 30 april/review_package/
```

Do not modify, overwrite, or regenerate it unless a future task explicitly names
that folder and asks for changes.
