# HMR Local Asset Packs

Date: 2026-05-01

## Purpose

HMR local assets are optional free/local fallbacks for scenes that are planned as
stock footage or stock image. They let production keep moving when stock
provider keys are unavailable or a provider search does not resolve a useful
asset.

## Folder Convention

Use domain folders under:

```text
assets/hmr_local/
```

Recommended first slice folders:

```text
assets/hmr_local/grocery/hook.mp4
assets/hmr_local/bill_leak/hook.mp4
assets/hmr_local/coffee_savings/hook.mp4
assets/hmr_local/generic_money_problem/hook.mp4
```

Accepted extensions:

- video: `.mp4`, `.mov`, `.m4v`, `.webm`
- image: `.jpg`, `.jpeg`, `.png`, `.webp`

Accepted role names:

- `hook`
- `reveal`
- `context`
- `payoff`
- `result`
- `cta`
- scene-specific IDs, for example `habit_reveal.mp4`

A role can also be a folder containing assets:

```text
assets/hmr_local/bill_leak/hook/clip_01.mp4
```

## Domain Lookup

Scene asset strategy rows now include a `domain` field from the existing HMR
domain logic. Local lookup checks folders in this order:

- `bill_leak`: `bill_leak`, `generic_money_problem`, `grocery`
- `coffee_savings`: `coffee_savings`, `generic_money_problem`, `grocery`
- `grocery_savings`: `grocery`, `grocery_savings`, `generic_money_problem`
- no domain: `grocery`, `generic_money_problem`

The final legacy root fallback remains:

```text
assets/hmr_local/
```

This preserves existing grocery behavior while allowing new topic packs to be
added without changing renderer templates.

## Readiness Check

Default behavior remains grocery-compatible:

```bash
python backend/utils/check_hmr_asset_readiness.py --json
```

Check a specific domain:

```bash
python backend/utils/check_hmr_asset_readiness.py --domain bill_leak --json
```

Infer from topic text:

```bash
python backend/utils/check_hmr_asset_readiness.py --topic "monthly bill leak price changed plan" --json
```

Missing assets do not fake success. Reports include the checked directories and
the local asset paths that would satisfy the missing role.
