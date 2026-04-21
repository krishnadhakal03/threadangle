"""Verify all API keys in .env are working."""
import requests, json, os, sys

BASE = "http://127.0.0.1:8000"

# Auth
login = requests.post(f"{BASE}/api/auth/login", json={"email": "admin@test.com", "password": "Admin@12345"}, timeout=5)
tok = login.json()["token"]
headers = {"Authorization": f"Bearer {tok}"}

# Credits check (includes runway, elevenlabs, gemini, huggingface)
r = requests.get(f"{BASE}/api/generate/video/credits", headers=headers, timeout=30)
d = r.json()
print("=== API KEY STATUS ===")
for key in ("runway", "elevenlabs", "gemini", "huggingface"):
    info = d.get(key, {})
    ok = info.get("ok")
    err = info.get("error") or ""
    bal = info.get("balance") or info.get("used_today") or ""
    print(f"  {key:15s}: {'OK' if ok else 'FAIL':4s}  balance={bal}  err={err[:60]}")

# Direct Pexels test
pexels_key = os.environ.get("PEXELS_API_KEY") or open(".env").read()
# Read from .env
env_vars = {}
for line in open(".env"):
    line = line.strip()
    if "=" in line and not line.startswith("#"):
        k, _, v = line.partition("=")
        env_vars[k.strip()] = v.strip()

print("\n=== DIRECT API KEY TESTS ===")

# Pexels
pexels_key = env_vars.get("PEXELS_API_KEY", "")
if pexels_key:
    pr = requests.get(
        "https://api.pexels.com/v1/videos/search",
        headers={"Authorization": pexels_key},
        params={"query": "business finance", "per_page": 1, "orientation": "portrait"},
        timeout=10,
    )
    if pr.status_code == 200:
        n = len(pr.json().get("videos", []))
        print(f"  Pexels         : OK  ({n} results for 'business finance')")
    else:
        print(f"  Pexels         : FAIL  HTTP {pr.status_code}")
else:
    print("  Pexels         : NO KEY")

# Pixabay
pixabay_key = env_vars.get("PIXABAY_API_KEY", "")
if pixabay_key:
    px = requests.get(
        "https://pixabay.com/api/videos/",
        params={"key": pixabay_key, "q": "business", "per_page": 3, "safesearch": "true"},
        timeout=10,
    )
    if px.status_code == 200:
        n = len(px.json().get("hits", []))
        print(f"  Pixabay        : OK  ({n} results for 'business')")
    else:
        print(f"  Pixabay        : FAIL  HTTP {px.status_code}")
else:
    print("  Pixabay        : NO KEY")

# HuggingFace
hf_token = env_vars.get("HF_TOKEN", "")
if hf_token:
    hf = requests.get(
        "https://huggingface.co/api/whoami",
        headers={"Authorization": f"Bearer {hf_token}"},
        timeout=10,
    )
    if hf.status_code == 200:
        uname = hf.json().get("name") or hf.json().get("fullname") or "unknown"
        print(f"  HuggingFace    : OK  (user={uname})")
    else:
        print(f"  HuggingFace    : FAIL  HTTP {hf.status_code}")
else:
    print("  HuggingFace    : NO KEY")

print("\n=== DRY RUN STATUS ===")
dry_run = env_vars.get("VIDEO_GENERATION_DRY_RUN", "1")
print(f"  VIDEO_GENERATION_DRY_RUN = {dry_run}  ({'LIVE MODE - real credits will be used!' if dry_run == '0' else 'SAFE MODE'})")
