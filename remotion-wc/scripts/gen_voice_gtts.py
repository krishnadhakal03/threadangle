"""
Generate quiz voiceovers with gTTS (dev build — no ElevenLabs spending).
Run: python scripts/gen_voice_gtts.py
"""
import json
import os
import time
from pathlib import Path

try:
    from gtts import gTTS
except ImportError:
    raise SystemExit("gTTS not found. Run: pip install gtts")

ROOT       = Path(__file__).resolve().parent.parent
QUIZ_FILE  = ROOT / "src" / "data" / "quiz_wc2026_v2.json"
VOICE_DIR  = ROOT / "public" / "voice"

VOICE_DIR.mkdir(parents=True, exist_ok=True)

with open(QUIZ_FILE, encoding="utf-8") as f:
    quiz = json.load(f)

questions = quiz["questions"]

for q in questions:
    qid  = q["id"]
    text = q["question"]
    dest = VOICE_DIR / f"q{qid}.mp3"

    if dest.exists():
        print(f"  Q{qid} - deleting stale: {dest.name}")
        dest.unlink()

    print(f"  Q{qid} - generating: \"{text}\"")
    try:
        tts = gTTS(text=text, lang="en", slow=False)
        tts.save(str(dest))
        kb = dest.stat().st_size // 1024
        print(f"  Q{qid} -- saved {kb} KB -> {dest.name}")
    except Exception as e:
        print(f"  Q{qid} - ERROR: {e}")

    time.sleep(0.4)  # polite delay between requests

print("\nDone. Voice files in public/voice/")
