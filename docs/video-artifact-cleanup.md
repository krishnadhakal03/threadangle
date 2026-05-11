# Video Artifact Cleanup

Generated videos are stored under `backend/generated_videos`. The cleanup command only deletes files and folders inside that Threadangle artifact root.

Manual EC2 dry run:

```bash
cd /path/to/Threadangle/backend
python cleanup_video_artifacts.py --dry-run --completed-hours 72 --failed-temp-hours 24
```

Manual EC2 delete:

```bash
cd /path/to/Threadangle/backend
python cleanup_video_artifacts.py --completed-hours 72 --failed-temp-hours 24
```

Environment defaults:

```bash
VIDEO_COMPLETED_ARTIFACT_EXPIRY_HOURS=72
VIDEO_TEMP_ARTIFACT_EXPIRY_HOURS=24
```

The command deletes completed run folders older than `completed-hours`, plus stale `raw`, `temp`, and `cache` entries older than `failed-temp-hours`. It does not touch WealthPro paths or any folder outside `backend/generated_videos`.
