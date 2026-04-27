"""
Progressive Reveal Engine

Supports staged reveals for money comparisons, before/after, AI outputs, etc.
"""

from typing import List, Dict, Any
from PIL import Image, ImageDraw
from .schema import StoryboardScene


class RevealStage:
    """A single stage in a progressive reveal."""

    def __init__(self, text: str, start_time: float, duration: float):
        self.text = text
        self.start_time = start_time
        self.duration = duration

    def is_active(self, t: float) -> bool:
        return self.start_time <= t < self.start_time + self.duration


class ProgressiveReveal:
    """Manages progressive reveal for a scene."""

    def __init__(self, stages: List[RevealStage]):
        self.stages = stages

    def get_active_text(self, t: float) -> str:
        """Get the text to display at time t."""
        active_stages = [stage for stage in self.stages if stage.is_active(t)]
        return " → ".join(stage.text for stage in active_stages) if active_stages else ""

    def apply_to_image(self, img: Image.Image, t: float) -> Image.Image:
        """Apply reveal overlay to image."""
        active_text = self.get_active_text(t)
        if not active_text:
            return img

        result = img.copy()
        draw = ImageDraw.Draw(result)
        # Draw reveal text
        font_size = 60
        try:
            from .formatting import font
            f = font(font_size, True)
        except:
            f = None
        bbox = draw.textbbox((0, 0), active_text, font=f)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (img.width - text_width) // 2
        y = img.height - 200
        draw.rectangle((x-10, y-10, x+text_width+10, y+text_height+10), fill=(0, 0, 0, 180))
        draw.text((x, y), active_text, fill=(255, 255, 255), font=f)
        return result


def create_money_reveal(stages: List[str], scene_duration: float) -> ProgressiveReveal:
    """Create progressive reveal for money comparison."""
    reveal_stages = []
    stage_duration = scene_duration / len(stages)
    for i, stage in enumerate(stages):
        reveal_stages.append(RevealStage(stage, i * stage_duration, stage_duration))
    return ProgressiveReveal(reveal_stages)


def create_ai_response_reveal(prompt: str, response_parts: List[str], scene_duration: float) -> ProgressiveReveal:
    """Create progressive reveal for AI response."""
    stages = [RevealStage(prompt, 0, scene_duration * 0.3)]
    remaining_time = scene_duration * 0.7
    part_duration = remaining_time / len(response_parts)
    for i, part in enumerate(response_parts):
        stages.append(RevealStage(part, scene_duration * 0.3 + i * part_duration, part_duration))
    return ProgressiveReveal(stages)


# Predefined reveals
PREDEFINED_REVEALS: Dict[str, Dict[str, Any]] = {
    "money_save": {
        "stages": ["$53/month", "$12.95/month", "save $480/year"],
        "type": "money"
    },
    "ai_answer": {
        "stages": ["User: How to save?", "AI: Use this method", "Result: Saved $100"],
        "type": "ai"
    }
}


def get_predefined_reveal(name: str, scene_duration: float) -> ProgressiveReveal | None:
    """Get a predefined progressive reveal."""
    if name not in PREDEFINED_REVEALS:
        return None

    config = PREDEFINED_REVEALS[name]
    if config["type"] == "money":
        return create_money_reveal(config["stages"], scene_duration)
    elif config["type"] == "ai":
        # Assume first stage is prompt, rest are response
        prompt = config["stages"][0]
        response_parts = config["stages"][1:]
        return create_ai_response_reveal(prompt, response_parts, scene_duration)
    return None