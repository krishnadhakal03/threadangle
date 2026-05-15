# Sports Asset Library Contract

Root: `assets/sports_library/`

## Folder Layout

```text
assets/sports_library/
  common/
    stadiums/
    crowds/
    tunnels/
    trophy/
    flags/
    heartbreak/
    celebration/
    pitch_details/
  leagues/
    epl/
    laliga/
    ucl/
    worldcup/
  teams/
    arsenal/
    man_city/
    liverpool/
    real_madrid/
    barcelona/
    inter_miami/
    argentina/
    portugal/
    france/
    england/
    brazil/
  players_archetypes/
    messi_legend_generic/
    ronaldo_power_generic/
    haaland_striker_generic/
    mbappe_speed_generic/
    saka_starboy_generic/
  reusable_clips/
    hero_scenes/
    rivalry_faceoffs/
    title_race/
    worldcup_pressure/
  thumbnails/
  manifests/
```

## Manifest Rules

Every reusable image or clip should have a manifest entry with provider, rights, cost, safety, and reuse metadata. Sports Clip Lab should prefer local/free assets before external calls, increment `reuse_count` after accepted use, and warn when `rights_status` is unknown.

Required safety fields:

- `rights_status`
- `logos_present`
- `broadcast_footage`
- `exact_player_likeness`
- `provider`
- `cost_credits`
- `cost_usd_estimate`

## Guardrails

No pirated match footage, ripped broadcast clips, official logos, sponsor marks, or exact player likeness by default. Paid provider assets must be manually approved and tagged with cost metadata.
