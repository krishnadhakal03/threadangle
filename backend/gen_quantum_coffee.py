#!/usr/bin/env python3
"""
Generate Quantum Coffee 15s video - Simple direct pipeline
"""
import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime

sys.path.insert(0, '.')
os.chdir('F:/Threadforge/backend')

from dotenv import load_dotenv
load_dotenv()

from utils.video_pipeline import (
    parse_script, build_scene_plan, resolve_duration_seconds,
    fetch_scene_clips, assemble_video, new_run_id
)
from routes.voice_gen import generate_voice, VoiceGenRequest

print("[START] Generating Quantum Coffee 15s...")

# Script parts
hook = "This coffee cup violates 3 laws of physics. MIT ran tests for 6 months. They couldn't explain it. Watch what happens at the 7-second mark."
body = "Scene 1: Pristine white table, ceramic cup of black coffee, camera settles. Caption: MIT THERMODYNAMICS LAB - DOCUMENTING THE ANOMALY. Scene 2: THE 7-SECOND MARK - coffee flows upward defying gravity, perfect slow-motion arc, freezes in air. Caption: THE LIQUID HAS NO REASON TO DO THIS. Scene 3: Coffee suspended as perfect sphere, light refracting through it. Caption: FRAME 847: STILL UNEXPLAINED."
cta = "Drop ruler emoji if you can explain this with physics. Drop swirl emoji if this broke your brain. Most common answer gets pinned."
script_text = hook + " " + body + " " + cta

print(f"[1/5] Parsing script ({len(script_text)} total chars)...")

# Parse
try:
    from routes.generate import parse_script as parse_with_class
    parts = parse_with_class(full_script=None, hook=hook, body=body, cta=cta)
    print("  --> Script parsed OK")
except Exception as e:
    print(f"  ERROR parsing: {e}")
    sys.exit(1)

# Scene plan
print(f"[2/5] Building scene plan (15 second duration)...")
try:
    duration_seconds = 15
    scenes = build_scene_plan(parts, duration_seconds=duration_seconds)
    print(f"  --> Built {len(scenes)} scenes")
    for i, s in enumerate(scenes, 1):
        print(f"      Scene {i}: {s.start:.1f}-{s.end:.1f}s")
except Exception as e:
    print(f"  ERROR building scenes: {e}")
    sys.exit(1)

# TTS
print(f"[3/5] Generating ElevenLabs TTS (Adam voice)...")
try:
    tts_req = VoiceGenRequest(text=script_text, voice_id='pNInz6obpgDQGcFmaJgB', force_free=False)
    tts_result = generate_voice(tts_req)
    audio_path = tts_result.audio_file
    audio_kb = os.path.getsize(audio_path) / 1024
    print(f"  --> {tts_result.provider}: {Path(audio_path).name}")
    print(f"      Size: {audio_kb:.1f} KB")
except Exception as e:
    print(f"  ERROR generating TTS: {e}")
    audio_path = None

# Runway
print(f"[4/5] Fetching Runway AI scenes (gen4.5)...")
print(f"      Please wait... this takes 30-120 seconds")
run_id = new_run_id()

async def fetch_async():
    return await fetch_scene_clips(
        scenes,
        run_id=run_id,
        mode='ai',
        available_credits=750.0,
        runway_model='gen4.5',
        max_scenes=len(scenes)
    )

try:
    fetched_scenes = asyncio.run(fetch_async())
    total_creds = sum(float(getattr(s, 'credits_cost', 0) or 0) for s in fetched_scenes)
    print(f"  --> Fetched {len(fetched_scenes)} scenes")
    print(f"      Total Runway credits: {total_creds:.1f}")
except Exception as e:
    print(f"  ERROR fetching scenes: {e}")
    sys.exit(1)

# Assemble
print(f"[5/5] Assembling final video...")
try:
    result = assemble_video(fetched_scenes, run_id=run_id, audio_path=audio_path)
    video_path = result['video_path']
    
    if os.path.exists(video_path):
        size_mb = os.path.getsize(video_path) / (1024 ** 2)
        print(f"  --> Video created: {Path(video_path).name}")
        print(f"      Size: {size_mb:.2f} MB")
        print(f"      Path: {video_path}")
        thumb = result.get('thumbnail_path')
        if thumb and os.path.exists(thumb):
            print(f"      Thumbnail: {Path(thumb).name}")
    else:
        print(f"  ERROR: Video not found at {video_path}")
        sys.exit(1)
except Exception as e:
    print(f"  ERROR assembling video: {e}")
    sys.exit(1)

print("\n" + "=" * 70)
print("SUCCESS: Quantum Coffee 15s generated!")
print("=" * 70)
print(f"Video ready at: {video_path}")
print("\nYou can now:")
print("1. Download and review the video")
print("2. Check quality against 4.2/5 gate")
print("3. Proceed to 45s Marcus Aurelius if this passes")
