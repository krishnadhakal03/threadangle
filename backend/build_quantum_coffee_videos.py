"""
Build 2 postable 15s videos from the 8 Runway clips.
Zero new credits - pure FFmpeg assembly.

Video 1: Eye + hand-with-dots + anatomy model (sci-fi/mind-bending)
Video 2: Portrait + muscle tissue + portrait again (cinematic/dramatic)
"""
import subprocess
import os
import sys

BASE = r"F:\Threadforge\backend"
RAW = os.path.join(BASE, "generated_videos", "raw")
TEMP = os.path.join(BASE, "generated_videos", "temp")
OUT = os.path.join(BASE, "generated_videos")
ASS = os.path.join(TEMP, "vid_dc2052b0796f.ass")
AUDIO = os.path.join(TEMP, "quantum_coffee_audio_15s.wav")

os.makedirs(TEMP, exist_ok=True)
os.makedirs(OUT, exist_ok=True)

def run(cmd, label=""):
    print(f"  Running: {label or cmd[:60]}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ERROR ({result.returncode}):")
        print(result.stderr[-1000:])
        return False
    return True

def normalize_clip(input_path, output_path, duration=5):
    """Scale to 720x1280, crop, 24fps, trim to duration, no audio"""
    return run([
        "ffmpeg", "-y", "-i", input_path,
        "-vf", "scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,setsar=1,fps=24",
        "-t", str(duration),
        "-an",
        output_path
    ], f"normalize {os.path.basename(input_path)}")

def concat_clips(clip_paths, output_path):
    """Concatenate clips using filter_complex"""
    inputs = []
    for c in clip_paths:
        inputs += ["-i", c]
    n = len(clip_paths)
    fc = "".join(f"[{i}:v]" for i in range(n)) + f"concat=n={n}:v=1:a=0[outv]"
    return run([
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", fc,
        "-map", "[outv]",
        output_path
    ], f"concat {n} clips")

def add_audio_and_captions(video_path, audio_path, ass_path, output_path):
    """Burn captions and mix audio into video"""
    # Escape ASS path for FFmpeg filter
    ass_escaped = ass_path.replace("\\", "/").replace(":", "\\:")
    return run([
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", audio_path,
        "-filter_complex",
        f"[0:v]ass='{ass_escaped}'[v]",
        "-map", "[v]",
        "-map", "1:a",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-t", "15",
        "-movflags", "+faststart",
        output_path
    ], f"add audio+captions -> {os.path.basename(output_path)}")

# ==================
# TRIM AUDIO TO 15s
# ==================
print("[AUDIO] Trimming 46s narration to 15s...")
if not os.path.exists(AUDIO):
    run([
        "ffmpeg", "-y",
        "-i", os.path.join(BASE, "assets", "voice_cache", "elevenlabs_adam_95d0e8ba77cb19ba.wav"),
        "-t", "15",
        "-af", "afade=t=out:st=13:d=2",
        AUDIO
    ], "trim audio to 15s")
    if os.path.exists(AUDIO):
        print(f"  Audio trimmed: {os.path.getsize(AUDIO)//1024}KB")
    else:
        print("  ERROR: Audio trim failed")
        sys.exit(1)
else:
    print(f"  Audio already exists: {os.path.getsize(AUDIO)//1024}KB")

# ==================
# VIDEO 1: Eye + hand-with-dots + anatomy model
# ==================
print("\n[VIDEO 1] Eye close-up + glowing hand + anatomy model")
v1_clips_raw = [
    os.path.join(RAW, "runway_task_3c7fc992c162_clip1.mp4"),  # extreme eye
    os.path.join(RAW, "runway_task_bd81ba03aad9_clip1.mp4"),  # glowing hand
    os.path.join(RAW, "runway_task_d45566c0ae3f_clip1.mp4"),  # anatomy
]
v1_norm = [os.path.join(TEMP, f"v1_clip{i+1}_norm.mp4") for i in range(3)]

print("  Normalizing clips...")
for raw, norm in zip(v1_clips_raw, v1_norm):
    if not os.path.exists(norm):
        normalize_clip(raw, norm)
    else:
        print(f"  Already normalized: {os.path.basename(norm)}")

v1_concat = os.path.join(TEMP, "v1_concat_raw.mp4")
print("  Concatenating...")
concat_clips(v1_norm, v1_concat)

v1_final = os.path.join(OUT, "quantum_coffee_v1.mp4")
print("  Adding audio + captions...")
add_audio_and_captions(v1_concat, AUDIO, ASS, v1_final)
if os.path.exists(v1_final):
    print(f"  SUCCESS: quantum_coffee_v1.mp4 ({os.path.getsize(v1_final)//1024//1024}MB)")
else:
    print("  FAILED: quantum_coffee_v1.mp4 not created")

# ==================
# VIDEO 2: Portrait + muscle tissue + anatomy model
# ==================
print("\n[VIDEO 2] Portrait + muscle tissue + anatomy model")
v2_clips_raw = [
    os.path.join(RAW, "runway_task_bb2c03c5fa25_clip1.mp4"),  # portrait
    os.path.join(RAW, "runway_task_27b3339e1703_clip1.mp4"),  # muscle tissue
    os.path.join(RAW, "runway_task_d45566c0ae3f_clip1.mp4"),  # anatomy
]
v2_norm = [os.path.join(TEMP, f"v2_clip{i+1}_norm.mp4") for i in range(3)]

print("  Normalizing clips...")
for raw, norm in zip(v2_clips_raw, v2_norm):
    if not os.path.exists(norm):
        normalize_clip(raw, norm)
    else:
        print(f"  Already normalized: {os.path.basename(norm)}")

v2_concat = os.path.join(TEMP, "v2_concat_raw.mp4")
print("  Concatenating...")
concat_clips(v2_norm, v2_concat)

v2_final = os.path.join(OUT, "quantum_coffee_v2.mp4")
print("  Adding audio + captions...")
add_audio_and_captions(v2_concat, AUDIO, ASS, v2_final)
if os.path.exists(v2_final):
    print(f"  SUCCESS: quantum_coffee_v2.mp4 ({os.path.getsize(v2_final)//1024//1024}MB)")
else:
    print("  FAILED: quantum_coffee_v2.mp4 not created")

# ==================
# SUMMARY
# ==================
print("\n" + "="*50)
print("DONE. Final videos:")
for name in ["quantum_coffee_v1.mp4", "quantum_coffee_v2.mp4"]:
    path = os.path.join(OUT, name)
    if os.path.exists(path):
        size = os.path.getsize(path) / (1024*1024)
        print(f"  OK  {name} ({size:.1f}MB)")
    else:
        print(f"  MISSING  {name}")
