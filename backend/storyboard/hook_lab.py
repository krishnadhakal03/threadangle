"""
Hook Lab MVP

Generate hook variants for storyboards.
"""

from typing import List, Dict
from .schema import StoryboardScene


def generate_confession_hook(original_text: str) -> str:
    """Generate confession-style hook."""
    return f"I have a confession to make: {original_text.lower()}"


def generate_number_hook(original_text: str) -> str:
    """Generate number-focused hook."""
    # Extract numbers
    import re
    numbers = re.findall(r'\d+', original_text)
    if numbers:
        return f"Did you know {numbers[0]} people are dealing with this? {original_text}"
    return f"Here's a number that shocked me: {original_text}"


def generate_tension_hook(original_text: str) -> str:
    """Generate tension/injustice hook."""
    return f"This is unacceptable: {original_text.lower()}"


def generate_hook_variants(storyboard) -> Dict[str, List[str]]:
    """Generate 3 hook variants for storyboard."""
    hook_scene = next((s for s in storyboard.scenes if s.beat_role == "hook"), None)
    if not hook_scene:
        hook_scene = storyboard.scenes[0] if storyboard.scenes else None

    if not hook_scene:
        return {"variants": []}

    original = hook_scene.narration_text
    variants = [
        generate_confession_hook(original),
        generate_number_hook(original),
        generate_tension_hook(original)
    ]

    return {
        "original": original,
        "variants": variants,
        "scene_id": hook_scene.scene_id
    }


def check_hook_quality(scene: StoryboardScene) -> str | None:
    """Check if hook has low motion or no curiosity trigger."""
    if scene.beat_role == "hook":
        if not scene.micro_beats:
            return "Hook scene lacks micro-beats for immediate engagement"
        curiosity_words = ["confession", "shocking", "unacceptable", "secret", "truth"]
        text = (scene.narration_text + " " + (scene.caption_text or "")).lower()
        if not any(word in text for word in curiosity_words):
            return "Hook lacks curiosity trigger words"
    return None