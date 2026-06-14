"""
Replace low-relevance quiz images with Wikipedia / Pexels photos.
Targets: Q3 (Azteca), Q8 (Haaland), Q10 (Ronaldo), Q4 (matches played).

Run: python scripts/fix_images.py
"""
import json
import os
import urllib.request
import urllib.parse
import urllib.error
import time
from pathlib import Path

ROOT       = Path(__file__).resolve().parent.parent
ENV_FILE   = ROOT.parent / "backend" / ".env"
OUT_DIR    = ROOT / "public" / "quiz_images"

# ── Load .env ──────────────────────────────────────────────────────────────────
env = {}
if ENV_FILE.exists():
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.startswith("#"):
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip()

PEXELS_KEY = env.get("PEXELS_API_KEY", "")

# ── Helpers ────────────────────────────────────────────────────────────────────

def download(url: str, dest: Path, headers: dict = None) -> int:
    req = urllib.request.Request(url, headers=headers or {"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r, open(dest, "wb") as f:
            data = r.read()
            f.write(data)
            return len(data)
    except Exception as e:
        raise RuntimeError(str(e))

def wikipedia_image(title: str) -> str | None:
    safe  = urllib.parse.quote(title.replace(" ", "_"))
    url   = f"https://en.wikipedia.org/api/rest_v1/page/summary/{safe}"
    try:
        req  = urllib.request.Request(url, headers={"User-Agent": "QuizBot/1.0 (educational)"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
            return data.get("thumbnail", {}).get("source")
    except Exception:
        return None

def pexels_image(query: str) -> str | None:
    if not PEXELS_KEY:
        print("  ! PEXELS_API_KEY not set -skipping Pexels fallback")
        return None
    encoded = urllib.parse.quote(query)
    url     = f"https://api.pexels.com/v1/search?query={encoded}&per_page=1&orientation=landscape"
    req     = urllib.request.Request(url, headers={"Authorization": PEXELS_KEY})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            data   = json.loads(r.read())
            photos = data.get("photos", [])
            if photos:
                return photos[0]["src"]["landscape"]
    except Exception:
        pass
    return None

# ── Per-question fix config ────────────────────────────────────────────────────
# (qid, wikipedia_title, pexels_query_fallback)
TARGETS = [
    (10, None, "Cristiano Ronaldo football Portugal"),
]

# ── Main ───────────────────────────────────────────────────────────────────────
OUT_DIR.mkdir(parents=True, exist_ok=True)

for qid, wiki_title, pexels_query in TARGETS:
    dest = OUT_DIR / f"q{qid}.jpg"
    print(f"\nQ{qid} -updating image")

    img_url = None

    # Try Wikipedia first
    if wiki_title:
        print(f"  Trying Wikipedia: {wiki_title}")
        img_url = wikipedia_image(wiki_title)
        if img_url:
            print(f"  Wikipedia -> {img_url[:80]}...")
        else:
            print("  Wikipedia: no thumbnail")

    # Pexels fallback
    if not img_url:
        print(f"  Trying Pexels: {pexels_query}")
        img_url = pexels_image(pexels_query)
        if img_url:
            print(f"  Pexels -> {img_url[:80]}...")
        else:
            print("  Pexels: no results")

    if not img_url:
        print(f"  Q{qid} -no image found, keeping existing")
        continue

    # Backup old file
    if dest.exists():
        dest.rename(dest.with_suffix(".jpg.bak"))

    try:
        size = download(img_url, dest)
        print(f"  Q{qid} -saved {size // 1024} KB -> q{qid}.jpg")
    except Exception as e:
        print(f"  Q{qid} -download failed: {e}")
        # Restore backup
        bak = dest.with_suffix(".jpg.bak")
        if bak.exists():
            bak.rename(dest)

    time.sleep(0.5)

print("\nDone. Images in public/quiz_images/")
