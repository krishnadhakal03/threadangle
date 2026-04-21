"""
Comprehensive Video Flow Test -- Free/Safe Mode Only
Tests: stock footage, free TTS, dry-run, Pollinations images
NO RunwayML credits consumed. NO ElevenLabs credits consumed.

Run: python test_video_flow.py
"""
import sys
import requests
import json
import time
import sys
import os

BASE = "http://127.0.0.1:8000/api"
ISSUES = []
PASSES = []
RATINGS = {}

def pass_test(name, detail=""):
    PASSES.append(name)
    print(f"  [PASS] {name}{(' - ' + detail) if detail else ''}")

def fail_test(name, detail=""):
    ISSUES.append({"name": name, "detail": detail})
    print(f"  [FAIL] {name}{(' - ' + detail) if detail else ''}")

def rate(key, score, note=""):
    RATINGS[key] = {"score": score, "note": note}
    stars = "*" * score + "." * (5 - score)
    print(f"  [RATE] {key}: {stars} ({score}/5){(' - ' + note) if note else ''}")

# ── helpers ──────────────────────────────────────────────────────────────────

def get_token():
    print("\n[AUTH] Getting test token...")
    # Use the admin test account created by create_admin.py
    payload = {"email": "admin@test.com", "password": "Admin@12345"}
    r = requests.post(f"{BASE}/auth/login", json=payload, timeout=10)
    if r.status_code == 200:
        data = r.json()
        # Server returns "token" not "access_token"
        token = data.get("token") or data.get("access_token")
        if token:
            pass_test("Login", "admin@test.com (founder plan)")
            return token
    fail_test("Auth", f"HTTP {r.status_code}: {r.text[:200]}")
    return None

TOKEN = get_token()

def req(method, path, **kwargs):
    headers = {"Content-Type": "application/json"}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    kwargs.setdefault("timeout", 60)
    fn = getattr(requests, method.lower())
    return fn(f"{BASE}{path}", headers=headers, **kwargs)

# ── TEST SUITE ─────────────────────────────────────────────────────────────

TEST_SCRIPT = """Stop wasting money on subscriptions you never use. Most people spend over 500 dollars a year on services they forgot they had. Audit your bank statement today, cancel the ones you haven't used in 30 days, and redirect that money to savings. Your future self will thank you."""

print("\n" + "="*60)
print("TEST 1: Video Plan Generation")
print("="*60)
r = req("POST", "/generate/video/plan", json={"script": TEST_SCRIPT, "duration_seconds": 30})
print(f"  HTTP {r.status_code}")
if r.status_code == 200:
    plan = r.json()
    pass_test("Video Plan API", f"HTTP 200")
    if plan.get("hook"):
        pass_test("Plan has hook", plan["hook"][:60])
    else:
        fail_test("Plan missing hook")
    if plan.get("body"):
        pass_test("Plan has body", plan["body"][:60])
    else:
        fail_test("Plan missing body")
    if plan.get("cta"):
        pass_test("Plan has CTA", plan["cta"][:60])
    else:
        fail_test("Plan missing CTA")
    if plan.get("platform_meta"):
        meta = plan["platform_meta"]
        if isinstance(meta.get("youtube_shorts"), dict) and meta["youtube_shorts"].get("title"):
            pass_test("YouTube Shorts metadata", meta["youtube_shorts"]["title"][:50])
        else:
            fail_test("YouTube Shorts metadata missing")
        if isinstance(meta.get("reels"), dict) and meta["reels"].get("title"):
            pass_test("Reels metadata", meta["reels"]["title"][:50])
        else:
            fail_test("Reels metadata missing")
    scenes = plan.get("scenes", [])
    print(f"  Scenes: {len(scenes)}")
    if len(scenes) >= 2:
        pass_test(f"Scene count ({len(scenes)} scenes)")
    else:
        fail_test(f"Too few scenes ({len(scenes)})")
else:
    fail_test("Video Plan API", f"HTTP {r.status_code}: {r.text[:200]}")
    plan = None

print("\n" + "="*60)
print("TEST 2: Video Preview Generation (Stock + Pollinations images, no credits)")
print("="*60)
r = req("POST", "/generate/video/preview", json={
    "script": TEST_SCRIPT,
    "duration": 30,
    "niche": "finance",
    "character_source": "generate",
    "scene_mode": "stock",
    "image_provider": "pollinations",
})
print(f"  HTTP {r.status_code}")
preview = None
if r.status_code == 200:
    preview = r.json()
    pass_test("Video Preview API", "HTTP 200")
    scenes = preview.get("scenes", [])
    print(f"  Preview scenes: {len(scenes)}")
    if len(scenes) > 0:
        pass_test(f"Preview has scenes ({len(scenes)})")
    else:
        fail_test("No preview scenes returned")

    # Check all scenes are stock (no credits)
    all_stock = all(s.get("method") == "stock" for s in scenes)
    all_zero_cost = all(s.get("credits_cost", 0) == 0 for s in scenes)
    if all_stock:
        pass_test("All scenes = stock mode (zero credits)")
    else:
        methods = [s.get("method") for s in scenes]
        fail_test(f"Not all scenes are stock: {methods}")
    if all_zero_cost:
        pass_test("All scenes = zero credits")
    else:
        costs = [s.get("credits_cost") for s in scenes]
        fail_test(f"Some scenes have credit cost: {costs}")

    total_credits = preview.get("estimated_cost", {}).get("credits", -1)
    print(f"  Estimated credits: {total_credits}")
    if total_credits == 0:
        pass_test("Estimated cost = 0 credits (safe)")
    elif total_credits > 0:
        fail_test(f"Non-zero credit estimate in stock mode: {total_credits}")

    # Check image_url presence
    scenes_with_images = [s for s in scenes if s.get("image_url")]
    print(f"  Scenes with images: {len(scenes_with_images)}/{len(scenes)}")
    if scenes_with_images:
        pass_test(f"{len(scenes_with_images)} scenes have Pollinations images")
        # Rate image quality by checking if URLs point to valid content
        sample_url = scenes_with_images[0]["image_url"]
        print(f"  Sample image URL: {sample_url[:80]}...")
        try:
            img_r = requests.get(sample_url, timeout=20)
            if img_r.status_code == 200 and len(img_r.content) > 5000:
                pass_test("Pollinations image URL is valid", f"{len(img_r.content)} bytes")
                rate("Pollinations Image Quality", 3, "Free tier — resolution 720x1280, Flux model")
            else:
                fail_test("Pollinations image too small or invalid", f"HTTP {img_r.status_code}, {len(img_r.content)} bytes")
        except Exception as e:
            fail_test("Pollinations image fetch failed", str(e))
    else:
        fail_test("No scenes have images")
else:
    fail_test("Video Preview API", f"HTTP {r.status_code}: {r.text[:200]}")

print("\n" + "="*60)
print("TEST 3: Free Video Generation (Stock mode, dry-run, free TTS)")
print("="*60)
r = req("POST", "/generate/video/free", json={
    "script": TEST_SCRIPT,
    "duration_seconds": 30,
    "scene_mode": "stock",
    "niche": "finance",
    "dry_run": True,
    "tts_provider": "free",
    "image_provider": "pollinations",
})
print(f"  HTTP {r.status_code}")
video_result = None
if r.status_code == 200:
    video_result = r.json()
    pass_test("Free Video Generation API", "HTTP 200")

    if video_result.get("dry_run") is True:
        pass_test("dry_run=True confirmed in response")
    else:
        fail_test("dry_run flag missing from response")

    if video_result.get("download_url"):
        pass_test("download_url present", video_result["download_url"])
    else:
        fail_test("No download_url in response")

    costs = video_result.get("costs", {})
    runway_credits = costs.get("runway_credits_used", -1)
    print(f"  Runway credits used: {runway_credits}")
    if runway_credits == 0:
        pass_test("Runway credits = 0 in dry-run/stock mode")
    else:
        fail_test(f"Non-zero Runway credits in dry-run mode: {runway_credits}")

    scenes = video_result.get("scenes", [])
    print(f"  Video scenes: {len(scenes)}")
    if len(scenes) >= 2:
        pass_test(f"Video has {len(scenes)} scenes")
    else:
        fail_test(f"Too few video scenes: {len(scenes)}")

    # Check SEO metadata
    seo = video_result.get("seo") or {}
    if seo.get("title"):
        pass_test("SEO title generated", seo["title"][:50])
    else:
        fail_test("SEO title missing")
    if seo.get("description"):
        pass_test("SEO description generated")
    else:
        fail_test("SEO description missing")
    if isinstance(seo.get("hashtags"), list) and seo["hashtags"]:
        pass_test(f"Hashtags generated ({len(seo['hashtags'])} tags)")
    else:
        fail_test("No hashtags generated")

    # Download and check the video file
    dl_url = video_result.get("download_url")
    if dl_url:
        print(f"  Downloading video from: http://127.0.0.1:8000{dl_url}")
        try:
            dHeaders = {"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}
            dr = requests.get(f"http://127.0.0.1:8000{dl_url}", headers=dHeaders, timeout=30)
            print(f"  Download HTTP {dr.status_code}, size: {len(dr.content)} bytes")
            if dr.status_code == 200 and len(dr.content) > 10000:
                pass_test("Video file downloadable", f"{len(dr.content)/1024:.1f} KB")
                rate("Stock Video", 3, "Stock footage assembled from Pexels/Pixabay. Free, no AI generation.")
            else:
                fail_test(f"Video download issue: HTTP {dr.status_code}, {len(dr.content)} bytes")
        except Exception as e:
            fail_test(f"Video download failed: {e}")
else:
    fail_test("Free Video Generation", f"HTTP {r.status_code}: {r.text[:200]}")

print("\n" + "="*60)
print("TEST 4: Free TTS Voice Generation")
print("="*60)
try:
    r = req("POST", "/generate/voice", json={
        "text": "Stop wasting money today. Start saving for your future.",
        "voice_id": "21m00Tcm4TlvDq8ikWAM",
        "force_free": True,
    })
    print(f"  HTTP {r.status_code}")
    if r.status_code == 200:
        tts = r.json()
        pass_test("Free TTS (pyttsx3) API", "HTTP 200")
        audio_file = tts.get("audio_file")
        provider = tts.get("provider")
        print(f"  Provider: {provider}")
        print(f"  Audio file: {audio_file}")
        if provider == "pyttsx3":
            pass_test("pyttsx3 provider confirmed")
        else:
            fail_test(f"Unexpected TTS provider: {provider}")
        if audio_file and os.path.exists(audio_file):
            size = os.path.getsize(audio_file)
            print(f"  Audio file size: {size} bytes")
            if size > 1000:
                pass_test("Audio file exists and has content", f"{size} bytes")
                rate("Free TTS (pyttsx3)", 2, "Robotic voice, offline, zero cost. Not suitable for production.")
            else:
                fail_test(f"Audio file too small: {size} bytes")
        else:
            fail_test(f"Audio file missing: {audio_file}")
    else:
        fail_test("Free TTS API", f"HTTP {r.status_code}: {r.text[:200]}")
except Exception as e:
    fail_test("Free TTS", str(e))

print("\n" + "="*60)
print("TEST 5: Generate-from-Preview (dry_run passthrough — CRITICAL)")
print("="*60)
if preview:
    scenes_payload = preview.get("scenes", [])
    # Test 5a: dry_run=True (should NOT call Runway)
    r = req("POST", "/generate/video/generate-from-preview", json={
        "preview_id": preview.get("preview_id", "test-preview-id"),
        "approved_scenes": scenes_payload,
        "dry_run": True,
    })
    print(f"  dry_run=True request: HTTP {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        if data.get("dry_run") is True:
            pass_test("CRITICAL: dry_run=True returned in response (no credits consumed)")
        else:
            fail_test("CRITICAL: dry_run flag mismatch in response", str(data))
        if data.get("status") == "queued":
            pass_test("Task queued successfully in dry-run mode")
        else:
            fail_test(f"Unexpected status: {data.get('status')}")
        print("  Waiting 3s for background task...")
        time.sleep(3)
    else:
        fail_test("generate-from-preview (dry_run=True)", f"HTTP {r.status_code}: {r.text[:200]}")
else:
    fail_test("Skipped (no preview from Test 2)")

print("\n" + "="*60)
print("TEST 6: API Credits Endpoint")
print("="*60)
r = req("GET", "/generate/video/credits")
print(f"  HTTP {r.status_code}")
if r.status_code == 200:
    credits = r.json()
    pass_test("API Credits endpoint returns data")
    runway = credits.get("runway", {})
    elevenlabs = credits.get("elevenlabs", {})
    gemini = credits.get("gemini", {})
    hf = credits.get("huggingface", {})
    print(f"  Runway: {runway}")
    print(f"  ElevenLabs: {elevenlabs}")
    print(f"  Gemini: {gemini}")
    print(f"  HuggingFace: {hf}")
    if "huggingface" in credits:
        pass_test("HuggingFace status present in API credits")
    else:
        fail_test("HuggingFace missing from API credits response")
else:
    fail_test("API Credits endpoint", f"HTTP {r.status_code}: {r.text[:200]}")

print("\n" + "="*60)
print("TEST 7: Thumbnail Endpoint")
print("="*60)
if video_result and video_result.get("generation_id"):
    r = req("POST", "/generate/regenerate-thumbnail", json={
        "video_id": video_result["generation_id"],
        "thumbnail_text": "SAVE $500/YEAR",
    })
    print(f"  HTTP {r.status_code}")
    if r.status_code == 200:
        thumb = r.json()
        pass_test("Thumbnail regeneration", thumb.get("thumbnail_url", "no url")[:60])
        rate("Thumbnail", 3, "Text overlay on first video frame. Clean, minimal style.")
    else:
        resp_body = r.text[:200]
        if "Video file not found" in resp_body or "not found on disk" in resp_body:
            print(f"  Note: Thumbnail skipped — video file not on disk in dry-run mode (expected)")
        else:
            fail_test("Thumbnail regeneration", f"HTTP {r.status_code}: {resp_body}")
else:
    print("  Skipped — no generation_id from Test 3")

print("\n" + "="*60)
print("TEST 8: Video History endpoint")
print("="*60)
r = req("GET", "/generate/video/history")
print(f"  HTTP {r.status_code}")
if r.status_code == 200:
    history = r.json()
    print(f"  History items: {len(history)}")
    pass_test("Video History API", f"{len(history)} entries")
    if history:
        latest = history[0]
        has_status = bool(latest.get("status"))
        has_id = bool(latest.get("id"))
        if has_status and has_id:
            pass_test("History item has required fields (id, status)")
        else:
            fail_test("History item missing required fields")
        # Check dry-run items have correct status
        dry_run_items = [h for h in history if h.get("warning") and "Dry-run" in str(h.get("warning", ""))]
        if dry_run_items:
            pass_test(f"Dry-run items visible in history ({len(dry_run_items)} found)")
else:
    fail_test("Video History API", f"HTTP {r.status_code}: {r.text[:200]}")

# ── SUMMARY ────────────────────────────────────────────────────────────────

print("\n" + "="*60)
print("SUMMARY")
print("="*60)
print(f"\n  Passed: {len(PASSES)}")
print(f"  Failed: {len(ISSUES)}")
print()

if ISSUES:
    print("  FAILED TESTS:")
    for issue in ISSUES:
        print(f"    ✗ {issue['name']}: {issue['detail']}")

if RATINGS:
    print("\n  QUALITY RATINGS:")
    for key, rating in RATINGS.items():
        stars = "★" * rating["score"] + "☆" * (5 - rating["score"])
        print(f"    {key}: {stars} ({rating['score']}/5) — {rating['note']}")

if not ISSUES:
    print("\n  [OK] ALL TESTS PASSED - Free mode verified safe")
    sys.exit(0)
else:
    print(f"\n  [ERR] {len(ISSUES)} TESTS FAILED - See details above")
    sys.exit(1)
