import os
from .runwayml_client import RunwayMLClient, RunwayMLQuotaError
from pathlib import Path
import random

def fetch_runwayml_clip(prompt: str, out_path: Path = None, num_frames: int = 24, seed: int = None, motion: str = "cinematic", model: str = None) -> str:
    """
    Generate a video clip using RunwayML Gen-2 API and save to out_path.
    Returns the path to the generated video file, or raises on error/quota.
    
    Args:
        model: Runway model to use. Options: gen4.5, gen4_turbo, gen3a_turbo (cheaper).
               Defaults to env RUNWAYML_MODEL or gen4.5
    """
    client = RunwayMLClient(model=model)
    # Use a random seed for diversity, but allow override for reproducibility
    if seed is None:
        seed = random.randint(1, 999999)
    try:
        video_path = client.generate_video(prompt, num_frames=num_frames, seed=seed, motion=motion)
        if out_path:
            # Use shutil.move instead of Path.rename to handle cross-device moves (different drives)
            import shutil
            shutil.move(str(video_path), str(out_path))
            return str(out_path)
        return video_path
    except RunwayMLQuotaError as e:
        print(f"[RUNWAYML] Quota error: {e}")
        raise
    except Exception as e:
        print(f"[RUNWAYML] Error: {e}")
        raise
