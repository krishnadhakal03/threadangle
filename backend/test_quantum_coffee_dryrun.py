#!/usr/bin/env python3
"""
Dry-run test for Quantum Coffee 15s script.
Tests without spending Runway or ElevenLabs credits.
"""

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

# Test endpoint URL (adjust if running on different port)
BASE_URL = "http://localhost:8000/api/generate"

# Quantum Coffee JSON payload from the spec
payload = {
    "hook": "This coffee cup violates 3 laws of physics. MIT ran tests for 6 months. They couldn't explain it. Watch what happens at the 7-second mark.",
    "body": "Scene 1: Pristine white table, ceramic cup of black coffee, camera settles. Caption: MIT THERMODYNAMICS LAB - DOCUMENTING THE ANOMALY. Scene 2: THE 7-SECOND MARK - coffee flows upward defying gravity, perfect slow-motion arc, freezes in air. Caption: THE LIQUID HAS NO REASON TO DO THIS. Scene 3: Coffee suspended as perfect sphere, light refracting through it. Caption: FRAME 847: STILL UNEXPLAINED.",
    "cta": "Drop ruler emoji if you can explain this with physics. Drop swirl emoji if this broke your brain. Most common answer gets pinned.",
    "duration_seconds": 15,
    "scene_mode": "ai",
    "niche": "Entertainment",
    "runway_model": "gen4.5",
    "dry_run": True,  # Explicitly request dry-run mode
    "tts_provider": "elevenlabs",
}

print("=" * 70)
print("QUANTUM COFFEE DRY-RUN TEST")
print("=" * 70)
print(f"\nPayload:\n{json.dumps(payload, indent=2)}")

# Get a dummy auth token (check if we can access the endpoint)
print("\n\n[1] Testing endpoint connectivity...")
try:
    # This will fail with 401 if no auth, but we'll see if the endpoint exists
    resp = requests.post(
        f"{BASE_URL}/video/free",
        json=payload,
        timeout=120,
    )
    print(f"Status: {resp.status_code}")
    if resp.status_code == 401:
        print("❌ Requires authentication. Use FastAPI token or run via web UI.")
        print("\nInstead, use the web UI or curl with auth header:")
        print(f"  POST to: {BASE_URL}/video/free")
        print(f"  Body: {json.dumps(payload)}")
    elif resp.status_code == 200:
        result = resp.json()
        print("✅ Success!")
        print(f"\nResponse:\n{json.dumps(result, indent=2)}")
        video_path = result.get("video_path")
        if video_path:
            print(f"\n🎬 Video generated: {video_path}")
            import os as os_
            if os_.path.exists(video_path):
                size_mb = os_.path.getsize(video_path) / (1024 ** 2)
                print(f"   Size: {size_mb:.2f} MB")
    else:
        print(f"Response: {resp.text[:500]}")
except requests.exceptions.ConnectionError:
    print("❌ Cannot connect to localhost:8000")
    print("   Is uvicorn backend running?")
    print("   Start with: cd F:\\Threadforge\\backend && python start_backend.py")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 70)
print("MANUAL TEST INSTRUCTIONS")
print("=" * 70)
print("""
To run the dry-run via cURL (if you have FastAPI token):

1. Get your auth token from the web UI or database
2. Run:
   
   curl -X POST http://localhost:8000/api/generate/video/free \\
     -H "Authorization: Bearer YOUR_TOKEN_HERE" \\
     -H "Content-Type: application/json" \\
     -d '{
       "hook": "This coffee cup violates 3 laws of physics...",
       "body": "Scene 1: ...",
       "cta": "Drop ruler emoji...",
       "duration_seconds": 15,
       "scene_mode": "ai",
       "niche": "Entertainment",
       "runway_model": "gen4.5",
       "dry_run": true
     }'

3. Wait ~20-30s for processing
4. Check backend output for scene planning, TTS, and video path
5. Review the generated video at: F:\\Threadforge\\backend\\generated_videos\\
""")
