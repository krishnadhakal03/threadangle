# Threadforge HMR Colab Benchmark

This benchmark checks whether Hybrid Motion Renderer v1 can render production-resolution vertical Shorts in Colab before buying new hardware.

It does not use ElevenLabs, RunwayML, or paid image/audio/video APIs. It tries free TTS in this order: `pyttsx3`, `gTTS`, then silent audio with a warning. It uses Pexels/Pixabay only if you provide existing keys.

## Colab Setup

1. Create a new Colab notebook.
2. Set runtime to GPU:
   - `Runtime` -> `Change runtime type` -> `T4 GPU`
3. Clone the branch:

```bash
!git clone -b feature/hybrid-motion-renderer-v1 https://github.com/krishnadhakal03/threadangle.git
%cd threadangle
```

4. Install dependencies:

```bash
!apt-get update -qq
!apt-get install -y -qq ffmpeg espeak
!pip install -q -r backend/requirements.txt pyttsx3 gTTS
```

5. Optional: set existing stock provider keys. Skip this if you want local animated fallbacks only.

```python
import os
os.environ["PEXELS_API_KEY"] = "paste_existing_key_here"
os.environ["PIXABAY_API_KEY"] = "paste_existing_key_here"
```

6. Confirm paid providers remain disabled:

```python
import os
os.environ["VIDEO_GENERATION_DRY_RUN"] = "1"
os.environ["ENABLE_HYBRID_MOTION_RENDERER"] = "1"
os.environ.pop("RUNWAYML_API_KEY", None)
os.environ.pop("ELEVENLABS_API_KEY", None)
```

## Benchmark Commands

Quick mode:

```bash
!python backend/utils/run_hybrid_motion_colab_benchmark.py \
  --preset quick \
  --output-dir backend/generated_videos/storyboard_review/hybrid_motion_colab_benchmark
```

Medium mode:

```bash
!python backend/utils/run_hybrid_motion_colab_benchmark.py \
  --preset medium \
  --output-dir backend/generated_videos/storyboard_review/hybrid_motion_colab_benchmark
```

Full production-resolution mode:

```bash
!python backend/utils/run_hybrid_motion_colab_benchmark.py \
  --preset full \
  --tts-provider gtts \
  --output-dir backend/generated_videos/storyboard_review/hybrid_motion_colab_benchmark
```

Manual override example:

```bash
!python backend/utils/run_hybrid_motion_colab_benchmark.py \
  --width 1080 \
  --height 1920 \
  --fps 24 \
  --preset full \
  --tts-provider gtts \
  --output-dir backend/generated_videos/storyboard_review/hybrid_motion_colab_benchmark
```

Force local animation only:

```bash
!python backend/utils/run_hybrid_motion_colab_benchmark.py \
  --preset full \
  --no-stock \
  --output-dir backend/generated_videos/storyboard_review/hybrid_motion_colab_benchmark
```

## Outputs

For a full preset run, expected files are:

```text
backend/generated_videos/storyboard_review/hybrid_motion_colab_benchmark/hmr_benchmark_1080x1920_30fps_full.mp4
backend/generated_videos/storyboard_review/hybrid_motion_colab_benchmark/render_report.json
backend/generated_videos/storyboard_review/hybrid_motion_colab_benchmark/qa_report.json
backend/generated_videos/storyboard_review/hybrid_motion_colab_benchmark/media_mix_report.json
```

Download outputs from Colab:

```python
from google.colab import files
files.download("backend/generated_videos/storyboard_review/hybrid_motion_colab_benchmark/hmr_benchmark_1080x1920_30fps_full.mp4")
files.download("backend/generated_videos/storyboard_review/hybrid_motion_colab_benchmark/render_report.json")
files.download("backend/generated_videos/storyboard_review/hybrid_motion_colab_benchmark/qa_report.json")
files.download("backend/generated_videos/storyboard_review/hybrid_motion_colab_benchmark/media_mix_report.json")
```

## Local Test

Before pushing changes:

```bash
python -m pytest backend/tests/test_hybrid_motion_renderer.py -q
```

## Notes

- Generated outputs live under `backend/generated_videos/`, which is gitignored.
- Offline `pyttsx3` may fail on some Colab images. If it does, the runner falls back to free `gTTS`; if that also fails, it still renders with silent audio and records the warning.
- GPU runtime helps the Colab environment overall, but the current HMR implementation is primarily CPU/OpenCV/PIL composition. The benchmark is still useful because Colab CPU/RAM may outperform local hardware for full-resolution runs.
