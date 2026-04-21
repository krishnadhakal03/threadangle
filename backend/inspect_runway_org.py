import os
from pathlib import Path
import json
import requests


def load_env():
    env_path = Path(__file__).resolve().parent / ".env"
    if env_path.exists():
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
    key = os.getenv("RUNWAYML_API_KEY", "").strip()
    version = os.getenv("RUNWAYML_API_VERSION", "2024-11-06")
    if not key:
        print("RUNWAYML_API_KEY missing")
        return

    headers = {
        "Authorization": f"Bearer {key}",
        "X-Runway-Version": version,
    }

    resp = requests.get("https://api.dev.runwayml.com/v1/organization", headers=headers, timeout=30)
    print("status:", resp.status_code)
    if resp.status_code != 200:
        print(resp.text)
        return

    data = resp.json()
    print(json.dumps(data, indent=2)[:12000])


if __name__ == "__main__":
    main()
