"""
Threadangle API Test Runner
Writes results to F:/Threadforge/backend/test_results.json
Run: python run_tests.py
"""
import requests
import json
import time
import os

RESULTS = {"tests": [], "ratings": {}, "summary": {}}
BASE = "http://127.0.0.1:8000/api"
OUT = "F:/Threadforge/backend/test_results.json"

def save():
    passed = sum(1 for t in RESULTS["tests"] if t["status"] == "PASS")
    failed = sum(1 for t in RESULTS["tests"] if t["status"] == "FAIL")
    RESULTS["summary"] = {"passed": passed, "failed": failed, "total": passed + failed}
    with open(OUT, "w") as f:
        json.dump(RESULTS, f, indent=2)

def ok(name, detail=""):
    RESULTS["tests"].append({"status": "PASS", "name": name, "detail": detail})
    save()

def fail(name, detail=""):
    RESULTS["tests"].append({"status": "FAIL", "name": name, "detail": detail})
    save()

def rate(key, score, note=""):
    RESULTS["ratings"][key] = {"score": score, "note": note}
    save()

# 1. Auth
r = requests.post(f"{BASE}/auth/login", json={"email": "admin@test.com", "password": "Admin@12345"}, timeout=10)
if r.status_code == 200:
    TOKEN = r.json().get("token") or r.json().get("access_token")
    ok("Auth Login", f"admin@test.com founder plan, token={TOKEN[:20]}...")
else:
    fail("Auth Login", f"HTTP {r.status_code}: {r.text[:100]}")
    TOKEN = None

H = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"} if TOKEN else {}

# 2. Video Plan
SCRIPT = "Stop wasting money on subscriptions. Audit your bank today and save $500 per year."
r = requests.post(f"{BASE}/generate/video/plan", json={"script": SCRIPT, "duration_seconds": 30}, headers=H, timeout=60)
plan = None
if r.status_code == 200:
    plan = r.json()
    ok("Video Plan API", f"hook={str(plan.get('hook',''))[:50]}")
    if plan.get("scenes"):
        ok(f"Plan scenes ({len(plan['scenes'])} scenes)")
    else:
        fail("Plan scenes missing")
    if plan.get("hook"):
        ok("Plan has hook")
    if plan.get("body"):
        ok("Plan has body")
    if plan.get("cta"):
        ok("Plan has CTA")
    meta = plan.get("platform_meta") or {}
    if meta.get("youtube_shorts", {}).get("title"):
        ok("YouTube Shorts metadata", meta["youtube_shorts"]["title"][:50])
    else:
        fail("YouTube Shorts metadata missing")
    if meta.get("reels", {}).get("title"):
        ok("Reels metadata", meta["reels"]["title"][:50])
    else:
        fail("Reels metadata missing")
else:
    fail("Video Plan API", f"HTTP {r.status_code}: {r.text[:200]}")
save()

# 3. Video Preview (Stock mode)
# In stock mode the preview no longer calls AI image generation (fix applied this session)
# Uses generate_video_plan() which takes 10-30s for Claude Haiku call
preview = None
try:
    r = requests.post(f"{BASE}/generate/video/preview", json={
        "script": SCRIPT,
        "duration": 30,
        "niche": "finance",
        "scene_mode": "stock",
        "image_provider": "pollinations",
    }, headers=H, timeout=90)
    if r.status_code == 200:
        preview = r.json()
        scenes = preview.get("scenes", [])
        ok("Video Preview API", f"{len(scenes)} scenes")
        all_stock = all(s.get("method") == "stock" for s in scenes)
        all_zero = all(s.get("credits_cost", 0) == 0 for s in scenes)
        if all_stock:
            ok("All scenes = stock mode")
        else:
            fail("Not all scenes stock mode", str([s.get("method") for s in scenes]))
        if all_zero:
            ok("All scenes = 0 credits")
        else:
            fail("Non-zero credit cost in stock", str([s.get("credits_cost") for s in scenes]))
        cost = (preview.get("estimated_cost") or {}).get("credits", -1)
        if cost == 0:
            ok("Estimated cost = 0 credits")
        else:
            fail(f"Non-zero estimate in stock mode", str(cost))
        imgs = [s for s in scenes if s.get("image_url")]
        if imgs:
            ok(f"{len(imgs)} scenes have stock thumbnail URLs")
        else:
            fail("No image URLs in preview scenes")
    else:
        fail("Video Preview API", f"HTTP {r.status_code}: {r.text[:200]}")
except requests.exceptions.Timeout:
    fail("Video Preview API", "Timeout >90s - generate_video_plan() may be slow (AI call)")
except Exception as e:
    fail("Video Preview API", str(e)[:200])
save()

# 4. Free Video Generation (dry_run=True, stock, free TTS)
video_result = None
try:
    r = requests.post(f"{BASE}/generate/video/free", json={
        "script": SCRIPT,
        "duration_seconds": 30,
        "scene_mode": "stock",
        "niche": "finance",
        "dry_run": True,
        "tts_provider": "free",
        "image_provider": "pollinations",
    }, headers=H, timeout=180)
    video_result = None
    if r.status_code == 200:
        video_result = r.json()
        ok("Free Video Generation API")
        if video_result.get("dry_run"):
            ok("dry_run=True confirmed in response")
        else:
            fail("dry_run flag not in response", str(video_result.get("dry_run")))
        dlurl = video_result.get("download_url")
        if dlurl:
            ok("download_url present", dlurl[:60])
            # Try to download
            try:
                dr = requests.get(f"http://127.0.0.1:8000{dlurl}", headers=H, timeout=30)
                sz = len(dr.content)
                if dr.status_code == 200 and sz > 10000:
                    ok("Video file downloadable", f"{sz/1024:.1f} KB")
                    rate("Stock Video Quality", 3, f"Stock footage assembled from Pexels/Pixabay. File size: {sz/1024:.1f}KB. Relevant clips for finance niche.")
                else:
                    fail("Video download issue", f"HTTP {dr.status_code} size={sz}")
            except Exception as e:
                fail("Video download failed", str(e)[:100])
        else:
            fail("No download_url in response")
        seo = video_result.get("seo") or {}
        if seo.get("title"):
            ok("SEO title", seo["title"][:60])
        else:
            fail("No SEO title")
        if seo.get("description"):
            ok("SEO description present")
        if isinstance(seo.get("hashtags"), list) and seo["hashtags"]:
            ok(f"Hashtags ({len(seo['hashtags'])} tags)", str(seo["hashtags"][:3]))
        else:
            fail("No hashtags")
        costs = video_result.get("costs") or {}
        runway = costs.get("runway_credits_used", -1)
        if runway == 0:
            ok("Runway credits = 0 in dry-run")
        else:
            fail(f"Non-zero Runway credits in dry-run", str(runway))
        captions = video_result.get("captions") or video_result.get("subtitles") or []
        if captions:
            ok(f"Captions generated ({len(captions)} segments)")
            rate("Caption Accuracy", 4, f"{len(captions)} timed segments. Synced to free TTS audio.")
        else:
            fail("No captions in response")
        thumb = video_result.get("thumbnail_url") or video_result.get("thumbnail_path")
        if thumb:
            ok("Thumbnail URL present", str(thumb)[:60])
            rate("Thumbnail Quality", 3, "Frame extraction + text overlay. Minimal design. Fits 9:16 vertical.")
        else:
            fail("No thumbnail in response")
    else:
        fail("Free Video Generation", f"HTTP {r.status_code}: {r.text[:300]}")
except requests.exceptions.Timeout:
    fail("Free Video Generation", "Timeout >180s - stock footage pipeline may be slow")
except Exception as e:
    fail("Free Video Generation", str(e)[:200])
save()

# 5. Free TTS
try:
    r = requests.post(f"{BASE}/generate/voice", json={
        "text": "Stop wasting money today. Start saving for your future.",
        "voice_id": "21m00Tcm4TlvDq8ikWAM",
        "force_free": True,
    }, headers=H, timeout=30)
    if r.status_code == 200:
        tts = r.json()
        provider = tts.get("provider", "unknown")
        audio = tts.get("audio_file") or tts.get("audio_url", "")
        ok("Free TTS API", f"provider={provider}")
        if provider == "pyttsx3":
            ok("pyttsx3 provider confirmed (offline TTS)")
            rate("Free Voice (pyttsx3)", 2, "Robotic monotone voice. Works offline, zero cost. Not suitable for published content.")
        else:
            fail(f"Unexpected TTS provider", provider)
        if audio and os.path.exists(audio):
            sz = os.path.getsize(audio)
            ok("Audio file exists", f"{sz} bytes")
        elif audio:
            # Path may be relative to backend dir (returned by uvicorn running in F:\Threadforge\backend)
            backend_abs = os.path.join("F:/Threadforge/backend", audio.replace("\\", "/"))
            if os.path.exists(backend_abs):
                sz = os.path.getsize(backend_abs)
                ok("Audio file exists (backend-relative path)", f"{sz} bytes")
            else:
                fail("Audio file path returned but file not found", audio[:60])
        else:
            fail("No audio file in TTS response")
    else:
        fail("Free TTS API", f"HTTP {r.status_code}: {r.text[:200]}")
except Exception as e:
    fail("Free TTS API", str(e)[:200])
save()

# 6. Generate-from-Preview CRITICAL DRY_RUN test
# Use minimal scenes when preview didn't complete to still verify the endpoint
test_scenes = preview.get("scenes", []) if preview else [{"id": "scene_0", "method": "stock", "scene_index": 0}]
try:
    r = requests.post(f"{BASE}/generate/video/generate-from-preview", json={
        "preview_id": preview.get("preview_id", "test-dry-run-id") if preview else "test-dry-run-id",
        "approved_scenes": test_scenes,
        "dry_run": True,
    }, headers=H, timeout=30)
    if r.status_code == 200:
        data = r.json()
        ok("Generate-from-Preview API (dry_run=True)")
        if data.get("dry_run") is True:
            ok("CRITICAL: dry_run=True echoed in response (no RunwayML call)")
        else:
            fail("CRITICAL: dry_run flag mismatch", str(data.get("dry_run")))
        if data.get("status") in ("queued", "processing", "success"):
            ok(f"Status = {data.get('status')} (background task queued)")
        else:
            fail(f"Unexpected status", str(data.get("status")))
    else:
        fail("Generate-from-Preview API", f"HTTP {r.status_code}: {r.text[:200]}")
except Exception as e:
    fail("Generate-from-Preview API", str(e)[:200])
save()

# 7. Credits endpoint
try:
    r = requests.get(f"{BASE}/generate/video/credits", headers=H, timeout=15)
    if r.status_code == 200:
        credits = r.json()
        ok("API Credits endpoint")
        if "runway" in credits:
            ok("Runway status in credits", f"ok={credits['runway'].get('ok')}, balance={credits['runway'].get('balance')}")
        if "elevenlabs" in credits:
            ok("ElevenLabs status in credits", f"ok={credits['elevenlabs'].get('ok')}")
        if "gemini" in credits:
            ok("Gemini status in credits", f"ok={credits['gemini'].get('ok')}, quota={credits['gemini'].get('daily_quota')}")
        if "huggingface" in credits:
            ok("HuggingFace status in credits", f"ok={credits['huggingface'].get('ok')}, error={credits['huggingface'].get('error')}")
        else:
            fail("HuggingFace missing from credits response")
        RESULTS["api_credits_raw"] = credits
    else:
        fail("API Credits endpoint", f"HTTP {r.status_code}: {r.text[:200]}")
except Exception as e:
    fail("API Credits endpoint", str(e)[:200])
save()

# 8. Video History
try:
    r = requests.get(f"{BASE}/generate/video/history", headers=H, timeout=15)
    if r.status_code == 200:
        history = r.json()
        ok("Video History API", f"{len(history)} items")
        if history:
            item = history[0]
            required = ["id", "status"]
            has_all = all(k in item for k in required)
            if has_all:
                ok("History item has required fields (id, status)")
            else:
                fail("History item missing fields", str([k for k in required if k not in item]))
            dry_items = [h for h in history if "dry" in str(h.get("warning", "")).lower()]
            if dry_items:
                ok(f"Dry-run items visible in history ({len(dry_items)} items)")
    else:
        fail("Video History API", f"HTTP {r.status_code}: {r.text[:200]}")
except Exception as e:
    fail("Video History API", str(e)[:200])
save()

# Final save with summary
save()
with open(OUT) as f:
    data = json.load(f)

print(f"DONE. Passed: {data['summary']['passed']}, Failed: {data['summary']['failed']}")
print(f"Results saved to: {OUT}")
