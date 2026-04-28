"""Playwright Reference Sampler

Samples frames from a YouTube reference URL using Playwright and a
sandbox Chrome profile (if provided via env `PLAYWRIGHT_SANDBOX_PROFILE`).
Performs lightweight frame-diff analysis to estimate shot boundaries,
average shot length, motion, text-overlay presence, and exports a
structured JSON suitable for the Reference Style Engine.

This tool does not save or commit captured frames (they are written
to a temporary folder and removed after analysis). It does not download
the video file. Use responsibly and do not store copyrighted frames.
"""
import os
import time
import json
import tempfile
from pathlib import Path
from typing import List

from playwright.sync_api import sync_playwright
import cv2
import numpy as np

OUTPUT_DIR = Path(__file__).resolve().parents[1] / "generated_videos" / "storyboard_review"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def capture_frames(youtube_url: str, sample_interval: float = 0.5, max_seconds: float = 60.0) -> List[Path]:
    user_profile = os.getenv("PLAYWRIGHT_SANDBOX_PROFILE")
    tmpdir = Path(tempfile.mkdtemp(prefix="tf_ref_frames_"))
    frames: List[Path] = []

    with sync_playwright() as p:
        browser_type = p.chromium
        launch_args = {"headless": True}
        if user_profile:
            launch_args["user_data_dir"] = user_profile
        browser = browser_type.launch(**launch_args)
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        page = context.new_page()
        page.goto(youtube_url, timeout=60000)
        # wait for video element
        page.wait_for_selector("video", timeout=30000)
        # get duration
        try:
            duration = page.evaluate("() => { const v = document.querySelector('video'); return v ? v.duration : 0 }") or 0
        except Exception:
            duration = 0
        duration = min(duration or max_seconds, max_seconds)
        t = 0.0
        while t < duration:
            # seek and wait
            try:
                page.evaluate(f"(t)=>{{const v=document.querySelector('video'); if(v) v.currentTime = t}}", t)
            except Exception:
                pass
            time.sleep(0.25)
            # screenshot the video element
            try:
                el = page.query_selector("video")
                img_bytes = el.screenshot(type="png")
            except Exception:
                img_bytes = page.screenshot(type="png")
            out = tmpdir / f"frame_{int(t*1000)}.png"
            out.write_bytes(img_bytes)
            frames.append(out)
            t += sample_interval

        try:
            context.close()
            browser.close()
        except Exception:
            pass

    return frames


def analyze_frames(frames: List[Path], diff_threshold: float = 30.0):
    times = []
    imgs = []
    for p in frames:
        img = cv2.imdecode(np.frombuffer(p.read_bytes(), np.uint8), cv2.IMREAD_GRAYSCALE)
        imgs.append(img)
    # compute frame diffs
    diffs = []
    for i in range(1, len(imgs)):
        a = cv2.resize(imgs[i - 1], (320, 180))
        b = cv2.resize(imgs[i], (320, 180))
        diff = cv2.absdiff(a, b)
        diffs.append(float(np.mean(diff)))

    # shot boundaries where diff exceeds threshold
    shot_indices = [0]
    for i, d in enumerate(diffs, start=1):
        if d > diff_threshold:
            shot_indices.append(i)
    # add last frame end
    shot_indices.append(len(imgs))

    shot_lengths = []
    for s, e in zip(shot_indices[:-1], shot_indices[1:]):
        shot_lengths.append((e - s) * 0.5)  # sample_interval default

    avg_shot = float(np.mean(shot_lengths)) if shot_lengths else 0.0
    cuts_per_sec = (len(shot_lengths) / (len(imgs) * 0.5)) if imgs else 0.0

    # first 5s inspection (first ~10 frames at 0.5s interval)
    first_frames = imgs[:10]
    motion_scores = []
    text_presence = False
    for i in range(1, len(first_frames)):
        motion_scores.append(float(np.mean(cv2.absdiff(first_frames[i - 1], first_frames[i]))))
    motion_level = float(np.mean(motion_scores)) if motion_scores else 0.0
    # naive text detection: look for bright horizontal bands
    f0 = first_frames[0]
    _, thr = cv2.threshold(f0, 220, 255, cv2.THRESH_BINARY)
    # detect blobs of bright pixels
    if np.sum(thr) > 1000:
        text_presence = True

    # zoom/punch heuristic: detect change in center-of-mass of bright features
    zoom_count = 0
    centers = []
    for im in imgs:
        _, timg = cv2.threshold(im, 200, 255, cv2.THRESH_BINARY)
        M = cv2.moments(timg)
        if M["m00"] != 0:
            cx = M["m10"] / M["m00"]
            cy = M["m01"] / M["m00"]
        else:
            cx, cy = im.shape[1] / 2, im.shape[0] / 2
        centers.append((cx, cy))
    for i in range(1, len(centers)):
        prev = centers[i - 1]
        cur = centers[i]
        if abs(prev[0] - cur[0]) + abs(prev[1] - cur[1]) > 20:
            zoom_count += 1

    results = {
        "num_frames": len(imgs),
        "avg_shot_length_s": avg_shot,
        "cuts_per_sec": cuts_per_sec,
        "first5s_motion_level": motion_level,
        "first5s_text_overlay": text_presence,
        "estimated_zoom_events": zoom_count,
        "shot_count": len(shot_lengths),
    }

    return results


def cleanup_frames(frames: List[Path]):
    for p in frames:
        try:
            p.unlink()
        except Exception:
            pass
    # remove parent tmpdir
    if frames:
        try:
            frames[0].parent.rmdir()
        except Exception:
            pass


def run_on_url(url: str):
    frames = capture_frames(url, sample_interval=0.5, max_seconds=30)
    results = analyze_frames(frames)
    cleanup_frames(frames)
    out = OUTPUT_DIR / "reference_playwright_analysis.json"
    out.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print("Analysis saved:", out)
    return results


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m backend.storyboard.playwright_reference_sampler <youtube_url>")
        raise SystemExit(2)
    run_on_url(sys.argv[1])
