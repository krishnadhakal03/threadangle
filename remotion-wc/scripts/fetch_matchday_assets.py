"""
Fetch all assets for MatchdayHype composition.
Outputs to public/matchday/:
  brazil_vs_morocco.jpg  — portrait Pexels image for hero panel
  voice_hook.mp3         — "Breaking news! Ancelotti drops a bombshell!"
  voice_neymar.mp3       — "Neymar is officially out of the squad!"
  voice_morocco.mp3      — "Morocco have beaten Brazil, two goals to one!"
  voice_predict.mp3      — prediction CTA
"""
import json
import time
import urllib.request
import urllib.parse
from pathlib import Path

ROOT     = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT.parent / "backend" / ".env"
OUT_DIR  = ROOT / "public" / "matchday"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Load .env
env = {}
if ENV_FILE.exists():
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.startswith("#"):
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip()

PEXELS_KEY = env.get("PEXELS_API_KEY", "")

# ── 1. Hero image (portrait) ──────────────────────────────────────────────────

def pexels_portrait(query):
    if not PEXELS_KEY:
        print("  No PEXELS_API_KEY — skipping image fetch")
        return None
    enc = urllib.parse.quote(query)
    url = f"https://api.pexels.com/v1/search?query={enc}&per_page=3&orientation=portrait"
    req = urllib.request.Request(url, headers={"Authorization": PEXELS_KEY})
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.loads(r.read())
        photos = data.get("photos", [])
        return photos[0]["src"]["portrait"] if photos else None

def download(url, dest):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as r, open(dest, "wb") as f:
        data = r.read()
        f.write(data)
    return dest.stat().st_size

img_dest = OUT_DIR / "brazil_vs_morocco.jpg"
if img_dest.exists():
    print(f"Image: already exists ({img_dest.stat().st_size // 1024} KB), skipping")
else:
    # Try Pexels first, fall back to copying existing quiz stadium image
    fetched = False
    for query in ["soccer stadium floodlights night", "football stadium crowd"]:
        print(f"Image: trying Pexels '{query}'")
        try:
            img_url = pexels_portrait(query)
            if img_url:
                size = download(img_url, img_dest)
                print(f"  Saved {size // 1024} KB -> brazil_vs_morocco.jpg")
                fetched = True
                break
        except Exception as e:
            print(f"  Pexels error: {e}")
    if not fetched:
        # Reuse existing Azteca stadium image (q3.jpg) as backdrop
        fallback = ROOT / "public" / "quiz_images" / "q3.jpg"
        if fallback.exists():
            import shutil
            shutil.copy(str(fallback), str(img_dest))
            print(f"  Copied q3.jpg (Azteca) as hero backdrop")
        else:
            print("  No image available — component will use CSS gradient fallback")

# ── 2. Voice clips (gTTS) ────────────────────────────────────────────────────

try:
    from gtts import gTTS
except ImportError:
    raise SystemExit("gTTS not found — run: pip install gtts")

PARTS = [
    ("voice_hook.mp3",    "Breaking news! Ancelotti drops a bombshell!"),
    ("voice_neymar.mp3",  "Neymar is officially out of the squad!"),
    ("voice_morocco.mp3", "Morocco have beaten Brazil, two goals to one!"),
    ("voice_predict.mp3", "We predict a two-all draw! Drop your prediction in the comments below!"),
]

for filename, text in PARTS:
    dest = OUT_DIR / filename
    if dest.exists():
        print(f"Voice: {filename} already exists ({dest.stat().st_size // 1024} KB), skipping")
        continue
    print(f"Voice: generating {filename} -> \"{text}\"")
    try:
        tts = gTTS(text=text, lang="en", slow=False)
        tts.save(str(dest))
        print(f"  Saved {dest.stat().st_size // 1024} KB")
    except Exception as e:
        print(f"  ERROR: {e}")
    time.sleep(0.4)

print("\nDone. Assets in public/matchday/")
