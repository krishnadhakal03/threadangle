# HMR Creative QA Scorecard

Date: 2026-05-01

## Purpose

Creative QA captures Krishna's human judgment separately from technical QA,
automated postability scoring, and the human posting gate.

Technical `PASS` does not mean a video is hook-strong, credible, novel, or worth
posting.

## Score Fields

Each score is an integer from 1 to 10:

- `hook_strength`
- `first_frame_strength`
- `proof_credibility`
- `pacing`
- `visual_novelty`
- `caption_readability`
- `sound_feel`
- `platform_fit`
- `post_worthiness`

Records also include `improvement_notes`.

## Status Derivation

Creative status is separate:

- `CREATIVE_PASS`: average score is at least 7, `post_worthiness` is at least 7, and no dimension is 5 or lower.
- `CREATIVE_REVIEW`: middling creative score, or any dimension scored 4-5.
- `CREATIVE_BLOCKED`: any score is 3 or lower, or `post_worthiness` is 4 or lower.

These statuses do not mutate:

- `technical_status`
- `postability_status`
- `human_posting_gate`

## Helpers

`backend/utils/hmr_creative_qa.py` provides:

- `build_creative_qa_record(...)`
- `write_creative_qa_record(...)`
- `read_creative_qa_record(...)`
- `update_creative_qa_record(...)`
- `attach_creative_qa(...)`

By default, records are stored under:

```text
backend/data/creative_qa/
```

HMR manifests can carry `creative_qa` as additive review metadata.
