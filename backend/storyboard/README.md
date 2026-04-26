# Storyboard Engine MVP

This package moves Threadforge video production toward:

`idea -> template -> storyboard -> scene preview -> user replace/lock -> caption/audio review -> final stitch`

Draft mode is intentionally local/free only. Paid providers are blocked unless final mode and explicit approval flags are set.

Useful commands:

```powershell
python -m backend.storyboard.cli preview backend\storyboard\examples\day6_walmart_storyboard.json
python -m backend.storyboard.cli render backend\storyboard\examples\day6_walmart_storyboard.json
python -m backend.storyboard.smoke_day6
```

Generated previews, media, manifests, and smoke outputs are written under `backend/generated_videos/storyboard_review/`, which is gitignored.
