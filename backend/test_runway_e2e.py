import os
from pathlib import Path


def load_env():
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v


def main():
    load_env()
    os.environ.setdefault("RUNWAYML_API_URL", "https://api.dev.runwayml.com/v1/text_to_video")
    os.environ.setdefault("RUNWAYML_API_VERSION", "2024-11-06")
    os.environ.setdefault("RUNWAYML_MODEL", "gen4.5")

    from utils.runwayml_client import RunwayMLClient

    prompt = "Cinematic close-up of hands typing on a laptop, shallow depth of field, vertical framing"
    client = RunwayMLClient()
    video_path = client.generate_video(prompt=prompt, num_frames=24, motion="cinematic")
    p = Path(video_path).resolve()
    print(f"SUCCESS: {p}")
    print(f"SIZE_BYTES: {p.stat().st_size}")


if __name__ == "__main__":
    main()
