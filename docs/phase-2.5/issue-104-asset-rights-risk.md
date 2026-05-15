# Issue #104: Sports Asset Rights and Risk Scoring

GitHub: https://github.com/krishnadhakal03/threadangle/issues/104

## Implemented

- Asset suggestions display `rights_status` and risk level in Sports Clip Lab.
- The sample sports asset manifest includes `risk_level` and `risk_reason`.
- The asset library contract requires rights and risk metadata for reusable assets.

## Current Risk Rules

- `low`: AI generated safe assets and free stock candidates that still need approval.
- `medium`: user-uploaded assets without known license metadata.
- `high`: official social/editorial clips.
- `critical`: ripped broadcast footage or scraped match highlights.

Unknown or risky assets should be treated as warnings before manual approval and should not silently advance into final stitch.
