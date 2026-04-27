"""
Hook Audio Preview Generator

Generates short 2-second audio previews for hook variants using local TTS.
"""

import pyttsx3
from pathlib import Path
from typing import List
from .schema import StoryboardScene


def generate_hook_preview(
    hook_text: str,
    output_path: Path,
    duration: float = 2.0
) -> Path:
    """Generate short audio preview for hook text."""
    engine = pyttsx3.init()

    # Configure for fast preview
    engine.setProperty('rate', 200)  # Speed up
    engine.setProperty('volume', 0.8)

    # Save to file
    engine.save_to_file(hook_text, str(output_path))
    engine.runAndWait()

    return output_path


def generate_hook_variants(
    base_hook: str,
    output_dir: Path
) -> List[Path]:
    """Generate previews for hook variants."""
    variants = [
        base_hook,
        f"Wait, {base_hook.lower()}",
        f"You won't believe {base_hook.lower()}",
        f"The truth about {base_hook.lower()}"
    ]

    output_dir.mkdir(parents=True, exist_ok=True)
    previews = []

    for i, variant in enumerate(variants):
        output_path = output_dir / f"hook_variant_{i+1}.wav"
        generate_hook_preview(variant, output_path)
        previews.append(output_path)

    return previews


def preview_hooks_for_storyboard(
    storyboard_path: Path,
    output_dir: Path
) -> List[Path]:
    """Generate hook previews for storyboard."""
    # Load storyboard and find hook scene
    import json
    with open(storyboard_path) as f:
        data = json.load(f)

    hook_scene = next((s for s in data['scenes'] if s['scene_type'] == 'hook'), None)
    if not hook_scene:
        raise ValueError("No hook scene found in storyboard")

    return generate_hook_variants(hook_scene['narration_text'], output_dir)