"""
Editorial Motion Engine - Micro-Beat Engine

Applies micro-beats and motion effects to scenes during rendering.
"""

from typing import List
from PIL import Image, ImageDraw
import math


class MicroBeat:
    """Base class for micro-beat effects."""

    def __init__(self, start_time: float, duration: float):
        self.start_time = start_time
        self.duration = duration

    def apply(self, img: Image.Image, t: float, scene_duration: float) -> Image.Image:
        """Apply the effect at time t. Return modified image."""
        raise NotImplementedError


class ZoomPunch(MicroBeat):
    def apply(self, img: Image.Image, t: float, scene_duration: float) -> Image.Image:
        if self.start_time <= t < self.start_time + self.duration:
            progress = (t - self.start_time) / self.duration
            # Zoom in to 1.2x over the duration
            scale = 1 + 0.2 * progress
            new_size = (int(img.width * scale), int(img.height * scale))
            zoomed = img.resize(new_size, Image.Resampling.LANCZOS)
            # Crop back to original size, centered
            left = (zoomed.width - img.width) // 2
            top = (zoomed.height - img.height) // 2
            return zoomed.crop((left, top, left + img.width, top + img.height))
        return img


class CropShift(MicroBeat):
    def apply(self, img: Image.Image, t: float, scene_duration: float) -> Image.Image:
        if self.start_time <= t < self.start_time + self.duration:
            progress = (t - self.start_time) / self.duration
            # Shift crop position
            shift_x = int(50 * math.sin(progress * math.pi))
            shift_y = int(30 * math.cos(progress * math.pi))
            left = max(0, shift_x)
            top = max(0, shift_y)
            right = min(img.width, img.width + shift_x)
            bottom = min(img.height, img.height + shift_y)
            return img.crop((left, top, right, bottom)).resize((img.width, img.height), Image.Resampling.LANCZOS)
        return img


class RapidZoom(MicroBeat):
    def apply(self, img: Image.Image, t: float, scene_duration: float) -> Image.Image:
        if self.start_time <= t < self.start_time + self.duration:
            progress = (t - self.start_time) / self.duration
            # Rapid zoom to 1.5x
            scale = 1 + 0.5 * progress
            new_size = (int(img.width * scale), int(img.height * scale))
            zoomed = img.resize(new_size, Image.Resampling.LANCZOS)
            left = (zoomed.width - img.width) // 2
            top = (zoomed.height - img.height) // 2
            return zoomed.crop((left, top, left + img.width, top + img.height))
        return img


class FlashCut(MicroBeat):
    def apply(self, img: Image.Image, t: float, scene_duration: float) -> Image.Image:
        if self.start_time <= t < self.start_time + self.duration:
            # Instant white flash
            flash_img = Image.new('RGB', (img.width, img.height), 'white')
            return Image.blend(img, flash_img, 0.3)
        return img


class ShakePan(MicroBeat):
    def apply(self, img: Image.Image, t: float, scene_duration: float) -> Image.Image:
        if self.start_time <= t < self.start_time + self.duration:
            progress = (t - self.start_time) / self.duration
            # Subtle shake and pan
            shake_x = int(10 * math.sin(progress * 10 * math.pi))
            shake_y = int(5 * math.cos(progress * 10 * math.pi))
            pan_x = int(20 * progress)
            left = max(0, shake_x + pan_x)
            top = max(0, shake_y)
            right = min(img.width, img.width + shake_x + pan_x)
            bottom = min(img.height, img.height + shake_y)
            return img.crop((left, top, right, bottom)).resize((img.width, img.height), Image.Resampling.LANCZOS)
        return img


class PulseGlow(MicroBeat):
    def apply(self, img: Image.Image, t: float, scene_duration: float) -> Image.Image:
        if self.start_time <= t < self.start_time + self.duration:
            progress = (t - self.start_time) / self.duration
            # Add glow effect by brightening
            enhancer = 1 + 0.3 * math.sin(progress * math.pi)
            return Image.eval(img, lambda x: min(255, int(x * enhancer)))
        return img


class DocumentaryDrift(MicroBeat):
    def apply(self, img: Image.Image, t: float, scene_duration: float) -> Image.Image:
        # Subtle continuous drift
        drift_x = int(10 * math.sin(t * 0.5))
        drift_y = int(5 * math.cos(t * 0.3))
        # For simplicity, just return img, implement pan logic
        return img  # TODO: implement pan


class ProofHighlight(MicroBeat):
    def apply(self, img: Image.Image, t: float, scene_duration: float) -> Image.Image:
        if self.start_time <= t < self.start_time + self.duration:
            # Add a highlight overlay
            overlay = Image.new('RGBA', img.size, (255, 255, 0, 50))
            return Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
        return img


class SplitReveal(MicroBeat):
    def apply(self, img: Image.Image, t: float, scene_duration: float) -> Image.Image:
        if self.start_time <= t < self.start_time + self.duration:
            progress = (t - self.start_time) / self.duration
            # Split screen reveal: left side old, right side new
            # For simplicity, darken left half
            result = img.copy()
            draw = ImageDraw.Draw(result)
            width = img.width
            split_x = int(width * progress)
            # Draw a rectangle over left part
            draw.rectangle((0, 0, split_x, img.height), fill=(0, 0, 0, 128))
            return result
        return img


class ValueTick(MicroBeat):
    def apply(self, img: Image.Image, t: float, scene_duration: float) -> Image.Image:
        # Simulate ticking number
        # For MVP, just flash or something
        if self.start_time <= t < self.start_time + self.duration:
            # Add a number overlay that "ticks"
            result = img.copy()
            draw = ImageDraw.Draw(result)
            tick_value = int((t - self.start_time) / self.duration * 100)
            draw.text((img.width // 2, img.height // 2), f"${tick_value}", fill=(255, 255, 0))
            return result
        return img


class PunchIn(MicroBeat):
    def apply(self, img: Image.Image, t: float, scene_duration: float) -> Image.Image:
        if self.start_time <= t < self.start_time + self.duration:
            progress = (t - self.start_time) / self.duration
            # Punch into a corner or area
            scale = 1 + progress * 0.5
            new_size = (int(img.width * scale), int(img.height * scale))
            zoomed = img.resize(new_size, Image.Resampling.LANCZOS)
            # Crop to simulate punch-in
            left = int(progress * img.width * 0.2)
            top = int(progress * img.height * 0.2)
            return zoomed.crop((left, top, left + img.width, top + img.height))
        return img


class FocusCrop(MicroBeat):
    def apply(self, img: Image.Image, t: float, scene_duration: float) -> Image.Image:
        if self.start_time <= t < self.start_time + self.duration:
            # Crop to focus on center area
            crop_width = int(img.width * 0.8)
            crop_height = int(img.height * 0.8)
            left = (img.width - crop_width) // 2
            top = (img.height - crop_height) // 2
            return img.crop((left, top, left + crop_width, top + crop_height)).resize((img.width, img.height), Image.Resampling.LANCZOS)
        return img


class PunchZoom(MicroBeat):
    def apply(self, img: Image.Image, t: float, scene_duration: float) -> Image.Image:
        if self.start_time <= t < self.start_time + self.duration:
            progress = (t - self.start_time) / self.duration
            scale = 1 + 0.5 * progress  # Punch zoom in
            new_size = (int(img.width * scale), int(img.height * scale))
            zoomed = img.resize(new_size, Image.Resampling.LANCZOS)
            left = (zoomed.width - img.width) // 2
            top = (zoomed.height - img.height) // 2
            return zoomed.crop((left, top, left + img.width, top + img.height))
        return img


class HardCutaway(MicroBeat):
    def apply(self, img: Image.Image, t: float, scene_duration: float) -> Image.Image:
        if self.start_time <= t < self.start_time + self.duration:
            # Simulate cutaway by darkening or changing
            return Image.new('RGB', img.size, (0, 0, 0))  # Black for cutaway
        return img


class TextSnap(MicroBeat):
    def apply(self, img: Image.Image, t: float, scene_duration: float) -> Image.Image:
        if self.start_time <= t < self.start_time + self.duration:
            # Add snapping text overlay
            result = img.copy()
            draw = ImageDraw.Draw(result)
            draw.text((img.width // 2, img.height // 2), "SNAP!", fill=(255, 255, 255))
            return result
        return img


# Map of beat names to classes
MICRO_BEAT_CLASSES = {
    "zoom_punch": ZoomPunch,
    "crop_shift": CropShift,
    "rapid_zoom": RapidZoom,
    "flash_cut": FlashCut,
    "shake_pan": ShakePan,
    "pulse_glow": PulseGlow,
    "documentary_drift": DocumentaryDrift,
    "proof_highlight": ProofHighlight,
    "split_reveal": SplitReveal,
    "value_tick": ValueTick,
    "punch_in": PunchIn,
    "focus_crop": FocusCrop,
    "punch_zoom": PunchZoom,
    "hard_cutaway": HardCutaway,
    "text_snap": TextSnap,
}


def create_micro_beats(beat_sequence: List[str], scene_duration: float) -> List[MicroBeat]:
    """Create micro-beat instances from sequence, spaced evenly."""
    beats = []
    if not beat_sequence:
        return beats

    beat_duration = scene_duration / len(beat_sequence)
    for i, beat_name in enumerate(beat_sequence):
        if beat_name in MICRO_BEAT_CLASSES:
            start_time = i * beat_duration
            beats.append(MICRO_BEAT_CLASSES[beat_name](start_time, beat_duration))
    return beats


def apply_motion(img: Image.Image, t: float, scene_duration: float, micro_beats: List[MicroBeat]) -> Image.Image:
    """Apply all active micro-beats to the image at time t."""
    result = img
    for beat in micro_beats:
        result = beat.apply(result, t, scene_duration)
    return result