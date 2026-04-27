"""
Documentary Motion Helpers

Enhanced motion treatments for static proof assets and screenshots.
"""

import math
from pathlib import Path
from PIL import Image
from typing import Optional
from .schema import StoryboardScene, MotionProfile


def apply_documentary_drift(img: Image.Image, t: float, duration: float) -> Image.Image:
    """Apply subtle handheld drift."""
    drift_x = int(math.sin(t * 1.3) * 9)
    drift_y = int(math.cos(t * 1.1) * 12)
    # Simulate camera shake by offsetting the image
    offset_img = Image.new("RGB", img.size, (10, 18, 30))
    offset_img.paste(img, (drift_x, drift_y))
    return offset_img


def apply_pan_across(img: Image.Image, t: float, duration: float) -> Image.Image:
    """Pan across the image like scanning a document."""
    pan_progress = (t / duration) * 0.5  # Pan halfway
    pan_x = int(pan_progress * img.width * 0.2)
    pan_y = int(pan_progress * img.height * 0.1)
    # Crop and reposition
    crop_width = int(img.width * 0.8)
    crop_height = int(img.height * 0.9)
    left = pan_x
    top = pan_y
    right = left + crop_width
    bottom = top + crop_height
    cropped = img.crop((left, top, right, bottom))
    # Paste back centered or something
    result = Image.new("RGB", img.size, (0, 0, 0))
    paste_x = (img.width - crop_width) // 2
    paste_y = (img.height - crop_height) // 2
    result.paste(cropped, (paste_x, paste_y))
    return result


def apply_punch_zoom(img: Image.Image, t: float, duration: float) -> Image.Image:
    """Punch into important area with zoom."""
    if t < duration * 0.5:
        return img
    zoom_progress = (t - duration * 0.5) / (duration * 0.5)
    scale = 1 + zoom_progress * 0.3
    new_size = (int(img.width * scale), int(img.height * scale))
    zoomed = img.resize(new_size, Image.Resampling.LANCZOS)
    # Crop center
    left = (zoomed.width - img.width) // 2
    top = (zoomed.height - img.height) // 2
    return zoomed.crop((left, top, left + img.width, top + img.height))


def apply_documentary_motion(img: Image.Image, scene: StoryboardScene, t: float, duration: float) -> Image.Image:
    """Apply appropriate documentary motion based on profile."""
    if scene.motion_profile == MotionProfile.documentary_dynamic:
        # Combine drift and pan
        img = apply_documentary_drift(img, t, duration)
        img = apply_pan_across(img, t, duration)
    elif scene.motion_profile == MotionProfile.kinetic_explainer:
        img = apply_punch_zoom(img, t, duration)
    # For static_clean, no motion
    return img