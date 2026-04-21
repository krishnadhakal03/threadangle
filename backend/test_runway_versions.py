import os
from pathlib import Path
import requests


def load_env():
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def main():
    load_env()
    key = os.getenv("RUNWAYML_API_KEY", "").strip()
    if not key:
        print("No RUNWAYML_API_KEY found")
        return

    versions = [
        "2024-11-06",
        "2024-12-01",
        "2025-01-01",
        "2024-09-13",
        "2024-08-01",
        "2024-07-01",
        "2024-06-01",
        "2024-05-01",
        "2024-04-01",
    ]

    url = "https://api.dev.runwayml.com/v1/organization"
    print("Testing versions against no-credit endpoint:")
    for v in versions:
        headers = {
            "Authorization": f"Bearer {key}",
            "X-Runway-Version": v,
        }
        try:
            r = requests.get(url, headers=headers, timeout=20)
            txt = (r.text or "").replace("\n", " ")[:180]
            print(f"{v} -> {r.status_code} :: {txt}")
        except Exception as e:
            print(f"{v} -> ERROR :: {e}")


if __name__ == "__main__":
    main()
