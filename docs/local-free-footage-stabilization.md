# Local Free Footage Stabilization

This sprint is local-first and no-credit. Do not use Runway, ElevenLabs, or production rendering for debugging.

## Route And File Map

- Frontend entry: `frontend/src/components/Dashboard.jsx`
- Plan endpoint: `backend/routes/generate.py` `POST /api/generate/video/plan`
- Preview endpoint: `backend/routes/generate.py` `POST /api/generate/video/preview`
- Generate-from-preview endpoint: `backend/routes/generate.py` `POST /api/generate/video/generate-from-preview`
- Stock fetchers and assembly: `backend/utils/video_pipeline.py`
- Free TTS: `backend/routes/voice_gen.py`
- Captions: `backend/utils/caption_generator.py`
- History/download/delete: `backend/routes/generate.py`

## Local No-Credit Env

Use these local settings:

```bash
FREE_VIDEO_ALLOW_PAID_PROVIDERS=0
VIDEO_GENERATION_DRY_RUN=0
ENABLE_SERVER_VIDEO_RENDERING=true
TTS_PROVIDER=free
VIDEO_SCENE_MODE=stock
RUNWAYML_MAX_SCENES=0
VIDEO_ALLOW_SILENT_FALLBACK=1
```

`PEXELS_API_KEY` or `PIXABAY_API_KEY` is required for real stock footage.

## Free TTS Fallbacks

Fallback order:

1. `gTTS`: free, requires internet access, writes MP3 then converts to WAV with `ffmpeg`.
2. `pyttsx3`: optional offline fallback. Requires the Python package and OS speech dependencies. Linux often needs `espeak` or `espeak-ng`; Windows uses installed SAPI voices.
3. Silent fallback: only when explicitly enabled with `VIDEO_ALLOW_SILENT_FALLBACK=1` or `TTS_PROVIDER=silent`. History should clearly say audio was not generated.

## Local Render Command

From repo root:

```bash
cd backend
python local_free_footage_render.py --allow-silent
```

The script uses the Issue #81 sample:

```text
HOOK:
Most students use AI the wrong way.

BODY:
Don't ask it to do your homework.
Ask it to explain hard topics, organize your notes, and quiz you before exams.
That turns AI into a study coach instead of a shortcut.

CTA:
Save this before your next study session.
```

The command prints the final local MP4 path under `backend/generated_videos`.

## Manual Review Checklist

- Scenes are relevant to studying, AI, notes, and exams.
- No repeated bad clips.
- Voice exists, or silent fallback is explicitly reported.
- Captions are readable and synced enough.
- MP4 plays locally.
- File can be opened/downloaded.
- Delete/cleanup removes final MP4 and related artifacts.

## Production Promotion Checklist

- Krishna manually approves a local MP4.
- Keep beta gate enabled.
- Keep public rendering disabled.
- Enable only owner rendering for one controlled 10-20s production test.
- Check disk usage before/after.
- Delete from UI and verify artifacts are removed.
- Do not touch or restart WealthPro.
