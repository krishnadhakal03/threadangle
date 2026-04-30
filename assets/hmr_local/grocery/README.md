# HMR Grocery Local Asset Pack

Scene Intelligence Sprint 1 uses this folder only as a real-asset fallback when
free stock providers are unavailable or cannot resolve a scene.

Add real footage or stills with these names:

- `hook.mp4` or `hook.jpg`
- `reveal.mp4` or `reveal.jpg`
- `payoff.mp4` or `payoff.jpg`
- `cta.mp4` or `cta.jpg`

Supported extensions:

- Video: `.mp4`, `.mov`, `.m4v`, `.webm`
- Image: `.jpg`, `.jpeg`, `.png`, `.webp`

The renderer will not fake success. If these files are missing and no stock API
keys are configured, HMR reports `fallback_used=true` and keeps the motion
template fallback.
