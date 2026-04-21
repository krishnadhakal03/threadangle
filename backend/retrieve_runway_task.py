"""
Retrieve a RunwayML task result by task_id.
Usage: python retrieve_runway_task.py <task_id>
"""
import asyncio
import os
import sys
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


async def fetch_task(task_id: str):
    import httpx

    load_env()
    api_key = os.getenv("RUNWAYML_API_KEY", "").strip()
    api_version = os.getenv("RUNWAYML_API_VERSION", "2024-11-06")
    task_url = f"https://api.dev.runwayml.com/v1/tasks/{task_id}"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "X-Runway-Version": api_version,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(task_url, headers=headers)

    print(f"Status: {resp.status_code}")
    if resp.status_code != 200:
        print(f"Error: {resp.text}")
        return

    import json
    payload = resp.json()
    print(json.dumps(payload, indent=2))

    status = str(payload.get("status") or payload.get("state") or "").upper()
    print(f"\nTask status: {status}")

    if status in ("SUCCEEDED", "SUCCESS", "COMPLETED"):
        output = payload.get("output")
        if isinstance(output, list) and output:
            url = output[0] if isinstance(output[0], str) else output[0].get("url")
        elif isinstance(output, dict):
            url = output.get("url") or output.get("videoUrl")
        else:
            url = payload.get("url") or payload.get("videoUrl")

        if url:
            print(f"\n✅ VIDEO URL (valid ~24h from task creation):\n{url}")
        else:
            print("\n⚠ Task succeeded but no output URL found in payload.")
    elif status in ("FAILED", "ERROR", "CANCELED", "CANCELLED"):
        print(f"\n❌ Task failed: {payload.get('failure') or payload.get('error')}")
    else:
        print(f"\n⏳ Task still running (status={status}). Try again in a minute.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python retrieve_runway_task.py <task_id>")
        print("\nGet the task_id from RunwayML dashboard:")
        print("  Request History → click the green 200 POST /v1/image_to_video → Response body → 'id' field")
        sys.exit(1)

    asyncio.run(fetch_task(sys.argv[1]))
