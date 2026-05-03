# Colab GPU Video Lab Reference

This document captures the product and technical reference for the proposed **AI Lab / Colab GPU Queue** feature in Threadforge.

Source discussion: uploaded `AI Video Generation Pipeline.pdf` and product planning conversation.

Related GitHub issue:

- #73 — Epic: Colab GPU Video Lab: Open-Source AI Video Generation Route

---

## 1. Purpose

Create a low-cost, no-paid-provider AI-video generation route using:

```text
Threadforge / local laptop orchestration
→ Google Drive job queue
→ Google Colab Pro GPU inference
→ open-source video models
→ final MP4 saved to Drive
→ Threadforge imports output for review
```

This is intended as a safer alternative to daily RunwayML usage and should be treated as an experimental feature lane until validated.

---

## 2. Product Positioning

Suggested menu name:

```text
AI Lab / Colab GPU Queue
```

Alternative name:

```text
GPU Video Lab
```

This should be a separate menu/lane from current Video Studio/HMR. Do not silently route existing Video Studio generations into this path until it is proven.

---

## 3. Target Output

Initial target from the PDF/reference:

```text
2–3 videos/day
~20 seconds each
~$10/month Colab Pro target cost
L4 or A100 preferred GPU
```

Important: Treat these as assumptions to validate, not guaranteed performance.

Threadforge should start with one proof video, then scale.

---

## 4. Strategic Fit for Krishna's Channels

Target channels:

1. **AI Sidekick**
   - AI tools
   - productivity
   - creator workflow
   - SaaS/screen/motion graphics

2. **Happy Kids Hub**
   - kids education
   - child health
   - parent-friendly learning
   - soft cartoon/educational animation

3. **Bodytruth**
   - body science
   - health explainers
   - walking, food, fat, metabolism animations
   - simple visual science / anatomy-style graphics

4. **Love Nepal Save Nepal**
   - Nepal culture
   - Himalayas
   - temples
   - villages
   - cinematic emotional AI animation

Best first validation target:

```text
Love Nepal Save Nepal — Why Nepal Feels Like a Dream
```

Reason: cinematic landscapes and cultural/emotional visuals are the strongest fit for open-source AI video testing.

---

## 5. Architecture v1

Use a file-based queue. Do not build a live Colab API tunnel first.

### Threadforge responsibilities

- Create AI Lab job packets.
- Generate channel/topic/script/scene prompts.
- Export `job.json`, prompt files, optional metadata to a local or Google Drive sync folder.
- Track job status.
- Import result files from Drive/local output folder.
- Create review package inside Threadforge.
- Require human review before posting.

### Google Drive responsibilities

- Shared filesystem between local Threadforge and Colab.
- Stores pending jobs.
- Stores outputs.
- Allows resumable/manual operation.

### Colab responsibilities

- Mount Google Drive.
- Read pending jobs.
- Load selected open-source model.
- Generate clips.
- Stitch clips with FFmpeg.
- Save `final.mp4`, `result.json`, `generation_log.txt`, and optional `preview_grid.jpg`.
- Mark jobs done/error.

### Review responsibilities

- Human manual QA.
- No auto-posting in v1.

---

## 6. Proposed Folder Layout

```text
GoogleDrive/MyDrive/Threadforge_Colab_Jobs/
  pending/
    love_nepal_2026_05_03_001/
      job.json
      metadata.json
      prompts.json
      optional_voice.wav
      optional_captions.srt

  output/
    love_nepal_2026_05_03_001/
      final.mp4
      result.json
      generation_log.txt
      preview_grid.jpg
      clips/
        clip_01.mp4
        clip_02.mp4
        clip_03.mp4
        clip_04.mp4

  archive/
    ...
```

---

## 7. Job Schema v1

```json
{
  "schema_version": "colab_gpu_video_lab_v1",
  "job_id": "love_nepal_2026_05_03_001",
  "channel": "Love Nepal Save Nepal",
  "title": "Why Nepal Feels Like a Dream",
  "duration_seconds": 20,
  "aspect_ratio": "9:16",
  "resolution": "720x1280",
  "model_hint": "CogVideoX-5B",
  "negative_prompt": "blurry, low quality, watermark, text, logo, distorted, flicker, bad anatomy",
  "clips": [
    {
      "id": "clip_01",
      "duration_seconds": 5,
      "type": "text_to_video",
      "prompt": "Vertical cinematic AI video, majestic Himalayan sunrise over snow peaks, prayer flags moving gently in foreground, golden light, smooth slow camera push, emotional travel film style, no text, no watermark"
    },
    {
      "id": "clip_02",
      "duration_seconds": 5,
      "type": "text_to_video",
      "prompt": "Vertical cinematic AI video of a young Nepali traveler walking along a mountain trail with colorful prayer flags, Himalayas in the background, smooth tracking camera, emotional hopeful mood, no text, no watermark"
    },
    {
      "id": "clip_03",
      "duration_seconds": 5,
      "type": "text_to_video",
      "prompt": "Vertical cinematic AI video of a peaceful Nepali temple courtyard inspired by Kathmandu heritage, warm morning light, prayer wheels, pigeons flying softly, rich cultural detail, no text, no watermark"
    },
    {
      "id": "clip_04",
      "duration_seconds": 5,
      "type": "text_to_video",
      "prompt": "Vertical cinematic AI video of a beautiful Nepal valley with turquoise lake, green hills, small village houses, distant snow mountains, soft clouds moving, peaceful cinematic camera glide, no text, no watermark"
    }
  ],
  "audio": {
    "voiceover_path": null,
    "music_mood": "emotional cinematic"
  },
  "outputs": {
    "final_video": "final.mp4",
    "result_json": "result.json",
    "log": "generation_log.txt"
  }
}
```

---

## 8. Result Schema v1

```json
{
  "schema_version": "colab_gpu_video_lab_result_v1",
  "job_id": "love_nepal_2026_05_03_001",
  "status": "done",
  "model_used": "THUDM/CogVideoX-5b",
  "gpu": "L4",
  "started_at": "2026-05-03T09:00:00Z",
  "completed_at": "2026-05-03T09:24:30Z",
  "duration_minutes": 24.5,
  "outputs": {
    "final_video": "/content/drive/MyDrive/Threadforge_Colab_Jobs/output/love_nepal_2026_05_03_001/final.mp4",
    "preview_grid": "/content/drive/MyDrive/Threadforge_Colab_Jobs/output/love_nepal_2026_05_03_001/preview_grid.jpg",
    "log": "/content/drive/MyDrive/Threadforge_Colab_Jobs/output/love_nepal_2026_05_03_001/generation_log.txt"
  },
  "cost": {
    "paid_provider_credits": 0,
    "runwayml": 0,
    "elevenlabs": 0,
    "openai": 0,
    "anthropic": 0,
    "gemini": 0
  },
  "clips": [
    {
      "id": "clip_01",
      "status": "done",
      "path": "/content/drive/MyDrive/Threadforge_Colab_Jobs/output/love_nepal_2026_05_03_001/clips/clip_01.mp4",
      "seconds": 5,
      "seed": 42
    }
  ],
  "notes": []
}
```

---

## 9. Model Candidates

The PDF discusses these model options:

| Model | Approx quality expectation | Approx VRAM expectation | Best use |
|---|---:|---:|---|
| Wan2.1-T2V-14B | Highest target quality | ~18–20GB+ | cinematic quality if GPU allows |
| CogVideoX-5B | strong prompt adherence | ~16GB+ | safer first Colab test |
| LTX-Video | faster/lighter | ~8GB+ | speed / lower VRAM |
| Mochi-1 | smoother motion | ~20GB+ | motion experiments |
| Open-Sora 1.2 | budget VRAM | ~10GB+ | fallback experiments |

Recommended first model:

```text
CogVideoX-5B
```

Reason: more realistic for Colab Pro if L4 or similar GPU is available.

Recommended stretch model:

```text
Wan2.1-T2V-14B
```

Reason: better quality target if VRAM/session supports it.

---

## 10. Colab Notebook v1 Shape

The PDF suggests a 5-cell notebook shape:

1. Install dependencies.
2. Mount Drive and create folders.
3. Load model.
4. Define generation/stitching functions.
5. Run batch loop over pending prompts/jobs.

Threadforge implementation should keep this notebook simple and reproducible.

---

## 11. Colab Notebook Pseudocode

```python
# Cell 1: install dependencies
# torch, diffusers, transformers, accelerate, imageio, ffmpeg, opencv, xformers, huggingface_hub

# Cell 2: mount Google Drive
from google.colab import drive
drive.mount('/content/drive')

# Cell 3: load model
MODEL_ID = 'THUDM/CogVideoX-5b'
# pipe = CogVideoXPipeline.from_pretrained(...)
# pipe.enable_model_cpu_offload()
# pipe.vae.enable_slicing()
# pipe.vae.enable_tiling()

# Cell 4: define functions
# load_jobs()
# generate_clip(prompt, negative, seed)
# save_clip(frames, path)
# stitch_clips(paths, final_path)
# write_result_json()

# Cell 5: run batch
# for each pending job:
#   generate each clip
#   stitch final video
#   save result.json
#   mark job done/error
```

---

## 12. Implementation Phases

### Phase 0 — Manual validation

Use PDF notebook or simplified Colab notebook directly.

Goal:

```text
Generate one Love Nepal cinematic AI video candidate.
```

Pass criteria:

- Final MP4 exists.
- No paid provider used.
- Render completes within acceptable time.
- Output is better than current stock-only/HMR placeholder visuals.
- Quality is worth further iteration.

### Phase 1 — Job packet export

Add backend/app ability to create a Colab job folder with:

- `job.json`
- `prompts.json` or scene prompt list
- optional `metadata.json`
- optional voice/caption inputs later

### Phase 2 — Colab queue notebook v1

Create notebook/script in repo that:

- mounts Drive
- reads pending jobs
- runs selected open-source model
- generates clips
- stitches final MP4
- writes result JSON

### Phase 3 — Result importer

Add app feature to import completed Colab output:

- final MP4
- result JSON
- logs
- preview image

Then create a review/history record in Threadforge.

### Phase 4 — Daily 4-channel planner

Generate daily queue for:

- AI Sidekick
- Happy Kids Hub
- Bodytruth
- Love Nepal Save Nepal

Start with 1–2 videos/day, then scale after quality/reliability proves out.

### Phase 5 — Optional active Colab bridge

Only after file-based queue works, consider temporary tunnel/API bridge from active Colab session.

Do not implement this first.

---

## 13. Gate 0 Dependency

This feature should not distract from the current critical stabilization gate.

Current required gate:

```text
Gate 0 — No-Spend Render Contract
```

Gate 0 must prove:

1. `ALLOW_PAID_PROVIDERS=0`
2. Runway client is blocked by test.
3. ElevenLabs is disabled/blocked.
4. Hybrid payload is verified as `scene_mode=hybrid_motion`.
5. Missing stock fallback works.
6. Final MP4 is generated.
7. `generation.video_file` is populated or history returns valid artifact.
8. Download works.
9. Credits used = 0.

Only after Gate 0 passes should this feature become the next major build lane.

---

## 14. Guardrails

- Do not use RunwayML.
- Do not use ElevenLabs.
- Do not call paid OpenAI/Anthropic/Gemini APIs.
- Do not auto-post v1 outputs.
- Do not claim Runway/Kling/Seedance quality until validated by actual outputs.
- Manual QA required before posting.
- Keep this separate from current HMR/Video Studio until stable.
- Do not overwrite frozen review package:

```text
backend/generated_videos/storyboard_review/post ready 30 april/review_package/
```

---

## 15. Out of Scope for v1

- Full auto-posting.
- Always-on GPU backend.
- Colab API tunnel.
- Guaranteed Runway/Kling/Seedance quality.
- Buying local GPU hardware.
- Replacing HMR/Video Studio as the default route.

---

## 16. Acceptance Criteria for Epic v1

- New AI Lab / Colab GPU Queue menu exists.
- User can create/export a Love Nepal job packet.
- Colab notebook can process that packet and write `final.mp4` + `result.json`.
- App can import final MP4 into review/history.
- Download/preview works in app.
- No paid provider credits are used.
- One manual Love Nepal AI-video candidate is created and reviewed.

---

## 17. First Validation Prompt Set — Love Nepal Save Nepal

### Video title

```text
Why Nepal Feels Like a Dream
```

### Clip 1 — Himalayan sunrise

```text
Vertical cinematic AI video, majestic Himalayan sunrise over Mount Everest style snow peaks, golden light breaking through clouds, prayer flags moving gently in the wind in the foreground, epic emotional atmosphere, smooth slow drone-like camera push forward, premium animated film quality, realistic cinematic lighting, 9:16 vertical, no text, no watermark, no logo
```

### Clip 2 — Nepali traveler

```text
Vertical cinematic AI video of a young Nepali traveler wearing a warm jacket and traditional scarf walking along a mountain trail lined with colorful prayer flags, Himalayas in the background, wind moving fabric and hair naturally, emotional hopeful mood, smooth tracking camera, premium cinematic animation, consistent character, 9:16 vertical, no text, no watermark
```

### Clip 3 — Temple / stupa

```text
Vertical cinematic AI video of a peaceful Nepali temple courtyard inspired by Kathmandu heritage, glowing morning light, prayer wheels, pigeons flying softly, a traveler pauses with respect, cinematic camera pan, rich cultural detail, warm emotional tone, premium animated film look, 9:16 vertical, no text, no watermark
```

### Clip 4 — Valley / lake

```text
Vertical cinematic AI video of a beautiful Nepal valley with turquoise lake, green hills, small village houses, distant snow mountains, soft clouds moving, peaceful cinematic camera glide, emotional travel film mood, premium AI animation quality, 9:16 vertical, no text, no watermark
```

### Clip 5 — Sunset closing

```text
Vertical cinematic AI video of the same Nepali traveler standing on a ridge looking at the Himalayan landscape at sunset, prayer flags fluttering beside them, golden sky, emotional proud moment, slow cinematic push-in from behind to side profile, premium animated film quality, 9:16 vertical, no text, no watermark
```

### Universal negative prompt

```text
low quality, blurry, jittery motion, warped face, deformed hands, extra fingers, bad anatomy, flicker, inconsistent character, distorted mountains, unreadable text, watermark, logo, oversaturated, cartoonish, flat lighting
```

---

## 18. Future Work

Potential future issues after Epic #73:

1. AI Lab UI/menu shell.
2. Colab job schema models.
3. Export Love Nepal job packet.
4. Colab queue notebook v1.
5. Import Colab result into Threadforge history.
6. Review package integration.
7. Daily 4-channel batch planner.
8. Quality scoring / regeneration loop.
9. Optional Drive API polling.
10. Optional active Colab API bridge.
