# Free AI Video Generator (Dashboard)

This implementation adds a **Generate AI Video (Free)** workflow to the customer dashboard.

## What it does

- Accepts full script (or optional Hook/Body/CTA fields)
- Builds a 10–15s scene plan
- Fetches free stock clips from:
  - Pexels API
  - Pixabay API
- Assembles vertical short (`1080x1920`) with fast scene cuts using `moviepy`
- Burns timed subtitles using `ffmpeg` (fallback: exports without burned subtitles)
- Returns MP4 preview/download in the dashboard

## Backend endpoint

- `POST /api/generate/video/free`
- `GET /api/generate/video/download/{filename}`

## Required environment variables

At least one of these must be set in backend environment:

- `PEXELS_API_KEY`
- `PIXABAY_API_KEY`

## Required tools/libraries

- Python dependency: `moviepy==1.0.3`
- System dependency: `ffmpeg` available on PATH

## Notes

- Workflow is fully free-only (no paid AI APIs)
- If some clips are not ideal, you can manually replace/edit in CapCut after export
- If subtitle burn fails, API returns a warning and still exports a playable MP4
