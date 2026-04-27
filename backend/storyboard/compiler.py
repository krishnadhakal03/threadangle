"""
Prompt-to-Storyboard Compiler

Converts topic/prompt into populated storyboard JSON.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from .schema import Storyboard, StoryboardScene, BeatRole, MotionProfile, VisualSource


def compile_storyboard(
    topic: str,
    niche: str = "personal finance",
    proof_numbers: Optional[list] = None,
    user_assets: Optional[list] = None,
    format: str = "short_9x16",
    template_type: str = "money_proof_short"
) -> Storyboard:
    """Compile topic into storyboard."""

    # Basic rule-based compilation
    project_id = f"compiled_{topic.lower().replace(' ', '_')[:20]}"

    scenes = []

    # Hook scene
    scenes.append(StoryboardScene(
        scene_id="hook",
        scene_type="hook",
        duration=3.0,
        narration_text=f"I need to talk about {topic.lower()}.",
        caption_text=f"I need to talk about {topic.lower()}.",
        visual_source=VisualSource.generated_card,
        beat_role=BeatRole.hook,
        micro_beats=["punch_zoom"],
        motion_profile=MotionProfile.documentary_dynamic
    ))

    # Setup scene
    scenes.append(StoryboardScene(
        scene_id="setup",
        scene_type="setup",
        duration=3.0,
        narration_text=f"Here's what I mean: {topic.lower()} is a big deal.",
        caption_text=f"Here's what I mean: {topic.lower()} is a big deal.",
        visual_source=VisualSource.generated_card,
        beat_role=BeatRole.setup,
        micro_beats=["value_tick"],
        motion_profile=MotionProfile.kinetic_explainer
    ))

    # Proof scene
    scenes.append(StoryboardScene(
        scene_id="proof",
        scene_type="proof",
        duration=4.0,
        narration_text=f"The numbers don't lie. {proof_numbers[0] if proof_numbers else 'Here are the facts'}.",
        caption_text=f"The numbers don't lie. {proof_numbers[0] if proof_numbers else 'Here are the facts'}.",
        visual_source=VisualSource.generated_card,
        beat_role=BeatRole.proof,
        micro_beats=["split_reveal"],
        motion_profile=MotionProfile.documentary_dynamic
    ))

    # Payoff scene
    scenes.append(StoryboardScene(
        scene_id="payoff",
        scene_type="payoff",
        duration=2.0,
        narration_text=f"That's why {topic.lower()} matters so much.",
        caption_text=f"That's why {topic.lower()} matters so much.",
        visual_source=VisualSource.generated_card,
        beat_role=BeatRole.payoff,
        motion_profile=MotionProfile.static_clean
    ))

    # CTA scene
    scenes.append(StoryboardScene(
        scene_id="cta",
        scene_type="cta",
        duration=2.0,
        narration_text=f"Take action on {topic.lower()} today.",
        caption_text=f"Take action on {topic.lower()} today.",
        visual_source=VisualSource.generated_card,
        beat_role=BeatRole.cta,
        micro_beats=["punch_zoom"],
        motion_profile=MotionProfile.static_clean
    ))

    return Storyboard(
        project_id=project_id,
        title=topic,
        niche=niche,
        template_id=template_type,
        format=format,
        render_mode="draft",
        scenes=scenes
    )


def save_compiled_storyboard(
    topic: str,
    output_path: Path,
    **kwargs
) -> Path:
    """Compile and save storyboard."""
    storyboard = compile_storyboard(topic, **kwargs)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(storyboard.model_dump(mode="json"), f, indent=2)
    return output_path