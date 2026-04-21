"""
Retrieve all 8 Runway task IDs from the Quantum Coffee session.
Downloads any completed videos not yet on disk.
Zero credits used - just polling existing tasks.
"""
import os
import sys
import requests

# Load .env manually
env_path = os.path.join(os.path.dirname(__file__), ".env")
env_vars = {}
if os.path.exists(env_path):
    with open(env_path, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env_vars[k.strip()] = v.strip()

API_KEY = env_vars.get("RUNWAYML_API_KEY", "").replace("\n", "").replace(" ", "")
TASK_URL = "https://api.dev.runwayml.com/v1/tasks/{task_id}"
API_VERSION = "2024-11-06"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "generated_videos", "raw")

TASK_IDS = [
    "bb2c03c5-fa25-4569-b0f8-c35d970b9a50",
    "bd81ba03-aad9-4fb4-9404-be9ce508a426",
    "3c7fc992-c162-4b8b-8f7c-7ddfa50635fd",
    "be10344e-06f5-454f-b925-a623037aef5e",
    "d45566c0-ae3f-436d-a3fc-742fbca1f84a",
    "27b3339e-1703-4630-9361-af4a89d6e900",
    "6667ab59-7e40-46e6-87bb-7de5b1d07055",
    "267c207d-722e-46c3-a48c-ee48a1cbac85",
]

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "X-Runway-Version": API_VERSION,
}

os.makedirs(OUTPUT_DIR, exist_ok=True)

print(f"Polling {len(TASK_IDS)} Runway task IDs...\n")

results = []
for task_id in TASK_IDS:
    url = TASK_URL.format(task_id=task_id)
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            status = data.get("status", "unknown")
            output = data.get("output", [])
            progress = data.get("progressRatio", 0)
            print(f"Task {task_id[:8]}... | Status: {status} | Progress: {progress}")
            if output:
                print(f"  Output URLs: {output}")
            results.append({
                "task_id": task_id,
                "status": status,
                "output": output,
                "data": data,
            })
        else:
            print(f"Task {task_id[:8]}... | HTTP {resp.status_code}: {resp.text[:200]}")
            results.append({"task_id": task_id, "status": "error", "output": []})
    except Exception as e:
        print(f"Task {task_id[:8]}... | Exception: {e}")
        results.append({"task_id": task_id, "status": "exception", "output": []})

print("\n--- Downloading completed tasks ---")
downloaded = []
for r in results:
    if r["status"] == "SUCCEEDED" and r["output"]:
        for i, url in enumerate(r["output"]):
            short_id = r["task_id"].replace("-", "")[:12]
            filename = f"runway_task_{short_id}_clip{i+1}.mp4"
            out_path = os.path.join(OUTPUT_DIR, filename)
            if os.path.exists(out_path):
                print(f"  Already exists: {filename}")
                downloaded.append(out_path)
                continue
            print(f"  Downloading {filename} from {url[:60]}...")
            try:
                dl = requests.get(url, timeout=120, stream=True)
                with open(out_path, "wb") as f:
                    for chunk in dl.iter_content(chunk_size=8192):
                        f.write(chunk)
                size_mb = os.path.getsize(out_path) / (1024*1024)
                print(f"  Saved: {filename} ({size_mb:.1f}MB)")
                downloaded.append(out_path)
            except Exception as e:
                print(f"  Download failed: {e}")

print(f"\nDone. Downloaded {len(downloaded)} file(s).")
for f in downloaded:
    print(f"  {os.path.basename(f)}")
