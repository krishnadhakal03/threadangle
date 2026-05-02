# Local SFX Assets

Place free/local sound effects in role folders:

```text
assets/sfx/whoosh/
assets/sfx/tick/
assets/sfx/soft_hit/
assets/sfx/warning_beep/
assets/sfx/riser/
assets/sfx/payoff_chime/
```

Supported file types: `.wav`, `.mp3`, `.m4a`, `.aac`, `.flac`, `.ogg`.

Missing assets are reported in HMR `sfx_plan.missing_roles` and do not block
video generation.
