# Proof Assets

Place user-provided proof images and clips under topic or run folders:

```text
assets/proof/<topic_or_run>/
```

Examples:

```text
assets/proof/bill_leak/statement.png
assets/proof/grocery_receipt/receipt_closeup.jpg
assets/proof/browser_capture/ai_answer.mp4
```

HMR proof asset inputs can target scenes by `scene_id` or `scene_role`. Missing
assets are reported in `proof_asset_plan.missing_assets` and do not block
generation.
