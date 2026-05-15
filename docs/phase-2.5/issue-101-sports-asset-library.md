# Issue #101: Sports Asset Library

GitHub: https://github.com/krishnadhakal03/threadangle/issues/101

## Added

- Folder and metadata contract: `docs/phase-2.5/sports-asset-library-contract.md`
- Sample manifest: `assets/sports_library/manifests/sample_worldcup_trophy_pressure.json`

## Integration Note

Sports Clip Lab asset discovery should read manifests from `assets/sports_library/manifests/`, filter by `usable_for` and `visual_tags`, prefer `cost_credits: 0`, and surface rights warnings when any safety field is unknown or risky.
