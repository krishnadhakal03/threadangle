# HMR Local SFX Layer

Date: 2026-05-01

## Purpose

HMR can now plan a lightweight local sound-design layer without using paid
providers or requiring a full render during tests. Voice and captions remain the
primary track; SFX are conservative accents.

## Asset Convention

Place free/local files under:

```text
assets/sfx/<role>/
```

Supported roles:

- `whoosh`
- `tick`
- `soft_hit`
- `warning_beep`
- `riser`
- `payoff_chime`

Example:

```text
assets/sfx/whoosh/whoosh.wav
assets/sfx/tick/tick.wav
assets/sfx/payoff_chime/chime_01.wav
```

Accepted extensions are `.wav`, `.mp3`, `.m4a`, `.aac`, `.flac`, and `.ogg`.

## Planning Metadata

`backend/utils/hmr_sfx.py` builds a `sfx_plan` with:

- supported roles;
- per-scene cues;
- resolved local file paths;
- missing roles and missing cues;
- conservative volume policy;
- `render_required: false`.

Scene dictionaries can provide explicit cues:

```json
{
  "id": "payoff",
  "duration": 3.0,
  "sfx_cues": [
    {"role": "riser", "local_time": 1.8, "volume": 0.14},
    {"role": "payoff_chime", "local_time": 2.75, "volume": 0.18}
  ]
}
```

If no explicit cues are present, HMR plans simple automatic accents from scene
role, template, and text. Missing files are reported truthfully and do not block
generation.

## Mixing

Use `build_sfx_mix_command(...)` to construct an ffmpeg command that mixes
resolved cues beneath the primary audio. The command builder keeps the base
voice track at `volume=1.0`, delays cues onto the timeline, caps cue volume, and
uses `amix` with `duration=first`.

Do not use paid SFX providers. Use self-recorded audio, public-domain files,
Creative Commons files with compatible attribution, or generated local tones you
have rights to use.
