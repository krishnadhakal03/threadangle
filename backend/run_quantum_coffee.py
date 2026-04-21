#!/usr/bin/env python3
"""
Generate Quantum Coffee 15s video with full AI pipeline + ElevenLabs TTS
"""
import asyncio
import sys
import os
import json
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

log_file = "quantum_coffee_generation.log"

def log_msg(msg):
    """Log to both stdout and file"""
    print(msg)
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(msg + "\n")

# Clear log
open(log_file, 'w', encoding='utf-8').close()

log_msg(f"[{datetime.now().isoformat()}] QUANTUM COFFEE GENERATION START")
log_msg("=" * 70)

# Script
hook = "This coffee cup violates 3 laws of physics. MIT ran tests for 6 months. They couldn't explain it. Watch what happens at the 7-second mark."
body = "Scene 1: Pristine white table, ceramic cup of black coffee, camera settles. Caption: MIT THERMODYNAMICS LAB - DOCUMENTING THE ANOMALY. Scene 2: THE 7-SECOND MARK - coffee flows upward defying gravity, perfect slow-motion arc, freezes in air. Caption: THE LIQUID HAS NO REASON TO DO THIS. Scene 3: Coffee suspended as perfect sphere, light refracting through it. Caption: FRAME 847: STILL UNEXPLAINED."
cta = "Drop ruler emoji if you can explain this with physics. Drop swirl emoji if this broke your brain. Most common answer gets pinned."
script_text = hook + " " + body + " " + cta

log_msg(f"[PARSE] Hook: {len(hook)} chars, Body: {len(body)} chars, CTA: {len(cta)} chars")

# Parse
from routes.generate import parse_script as parse_with_class
parts = parse_with_class(full_script=None, hook=hook, body=body, cta=cta)

# Scene plan
duration_seconds = 15
scenes = build_scene_plan(parts, duration_seconds=duration_seconds)
log_msg(f"[SCENES] Built {len(scenes)} scenes:")
for i, s in enumerate(scenes, 1):
    log_msg(f"  Scene {i}: {s.start:.1f}–{s.end:.1f}s | {s.visual_description[:60]}...")

# TTS
log_msg(f"\n[TTS] Generating ElevenLabs Adam voiceover ({len(script_text)} chars)...")
tts_req = VoiceGenRequest(text=script_text, voice_id='pNInz6obpgDQGcFmaJgB', force_free=False)
audio_path = None
try:
    tts_result = generate_voice(tts_req)
    audio_path = tts_result.audio_file
    audio_size = os.path.getsize(audio_path) / 1024
    log_msg(f"[TTS] OK: {tts_result.provider} saved")
    log_msg(f"      File: {Path(audio_path).name}")
    log_msg(f"      Size: {audio_size:.1f} KB")
except Exception as e:
    log_msg(f"[TTS] ERROR: Failed: {e}")
    audio_path = None

# Runway
log_msg(f"\n[RUNWAY] Fetching AI scenes (gen4.5)...")
log_msg(f"         This will take 30-120 seconds depending on Runway queue...")
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
    total_credits = sum(float(getattr(s, 'credits_cost', 0) or 0) for s in fetched_scenes)
    log_msg(f"[RUNWAY] OK: Fetched {len(fetched_scenes)} scenes")
    log_msg(f"         Credits used: {total_credits:.1f}")
    for i, s in enumerate(fetched_scenes, 1):
        log_msg(f"         Scene {i}: {getattr(s, 'credits_cost', '?')} credits")
except Exception as e:
    log_msg(f"[RUNWAY] ERROR: Failed: {e}")
    sys.exit(1)

# Assembly
log_msg(f"\n[ASSEMBLY] Creating final video...")
try:
    result = assemble_video(fetched_scenes, run_id=run_id, audio_path=audio_path)
    video_path = result['video_path']
    thumbnail_path = result.get('thumbnail_path')
    
    if os.path.exists(video_path):
        video_size_mb = os.path.getsize(video_path) / (1024 ** 2)
        log_msg(f"[ASSEMBLY] OK: Video generated")
        log_msg(f"           Path: {video_path}")
        log_msg(f"           Size: {video_size_mb:.2f} MB")
        log_msg(f"           Duration: 15 seconds")
        if thumbnail_path and os.path.exists(thumbnail_path):
            thumb_size = os.path.getsize(thumbnail_path) / 1024
            log_msg(f"           Thumbnail: {Path(thumbnail_path).name} ({thumb_size:.1f} KB)")
    else:
        log_msg(f"[ASSEMBLY] ERROR: Video file not found: {video_path}")
        sys.exit(1)
except Exception as e:
    log_msg(f"[ASSEMBLY] ERROR: Failed: {e}")
    sys.exit(1)

log_msg("\n" + "=" * 70)
log_msg(f"[{datetime.now().isoformat()}] QUANTUM COFFEE COMPLETE - SUCCESS")
log_msg("=" * 70)
log_msg("Video is ready. Check generated_videos/ folder.")
